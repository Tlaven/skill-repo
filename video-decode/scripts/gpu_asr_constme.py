#!/usr/bin/env python3
"""gpu_asr_constme.py — 无字幕视频的 GPU ASR 快路径 (Const-me/Whisper, DirectCompute)

适用: 本机无 NVIDIA (CTranslate2 CUDA 不可用), 但任何硬件 GPU 都可跑 Direct3D11
      compute shaders。**仅当 yt_transcript.py 退出码 2 (真无字幕) 时使用**; 字幕优先。
      CPU 备用路径: asr_transcribe.py (GPU 不可用时)。

实测 (2026-10-09, AMD RX 6650 XT, medium): 610s 音频 → 83.5s (≈7.3x 实时)。
模型无自动语言检测 → 必须显式 --lang (默认 zh)。

用法:
    python gpu_asr_constme.py --url "URL" [--model medium|small|large-v3] [--lang zh] [--workdir DIR]
    python gpu_asr_constme.py --audio "path.mp4" [...]

输出 (url 模式默认 <临时目录>/video-decode/<id>; audio 模式默认音频同目录):
    transcript.txt      清洗后纯文本 (按 500 字换行)
    transcript.raw.txt  原样转写文本 (回溯用)
退出码: 0=成功, 1=错误, 2=工具/模型缺失且未启用自动下载

工具缓存 (复用, 勿删): %LOCALAPPDATA%\\video-decode\\const-whisper\\cli\\main.exe + ggml-<model>.bin
自动下载: cli.zip (GitHub releases 1.12.0) + HF 模型 (hf-mirror.com 兜底)。
坑: 音频下载遇 SABR-only 实验时 bestaudio 无 URL (YouTube issue #12482), 脚本用
    `bestaudio/best[ext=mp4]/18` 兜底 (format 18 含 AAC 音轨, 对 ASR 够用)。
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile


def log(*a):
    print(*a, flush=True)


TOOL_ROOT_DEFAULT = os.path.join(os.environ.get("LOCALAPPDATA", ""), "video-decode", "const-whisper")
CLI_ZIP_URL = "https://github.com/Const-me/Whisper/releases/download/1.12.0/cli.zip"
MODELS = {
    "small": ("ggml-small.bin", 466_000_000, 0.46),
    "medium": ("ggml-medium.bin", 1_533_763_059, 1.43),
    "large-v3": ("ggml-large-v3.bin", 3_094_623_691, 2.88),
}
HF = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
HF_MIRROR = "https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/"


def download(urls, dest):
    last = None
    for url in urls:
        try:
            log(f"[dl] {url}")
            t0 = time.time()
            done = 0
            lastpct = -10
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest + ".part", "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done * 100 // total
                        if pct >= lastpct + 10:
                            lastpct = pct
                            log(f"     {pct}% ({done / 1048576:.0f}MB)")
            os.replace(dest + ".part", dest)
            log(f"[dl] ok {dest} ({done / 1048576:.1f}MB, {time.time() - t0:.0f}s)")
            return True
        except Exception as e:
            last = e
            log(f"[dl] fail: {str(e)[:140]}")
    log(f"[dl] ERROR: 全部下载源失败: {last}")
    return False


def ensure_tool(tool_root, allow_dl):
    for cand in (os.path.join(tool_root, "cli", "main.exe"), os.path.join(tool_root, "main.exe")):
        if os.path.isfile(cand):
            return cand
    if not allow_dl:
        log("[tool] 缺 main.exe; 去掉 --no-download 允许自动下载, 或手动解压 cli.zip 到 " + os.path.join(tool_root, "cli"))
        sys.exit(2)
    log("[tool] 未找到, 下载 cli.zip (369KB, GitHub releases 1.12.0)...")
    os.makedirs(tool_root, exist_ok=True)
    zp = os.path.join(tool_root, "cli.zip")
    if not download([CLI_ZIP_URL], zp):
        log("[tool] 下载失败; 手动: " + CLI_ZIP_URL + " → 解压到 " + os.path.join(tool_root, "cli"))
        sys.exit(2)
    outdir = os.path.join(tool_root, "cli")
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(outdir)
    exe = os.path.join(outdir, "main.exe")
    if not os.path.isfile(exe):
        log("[tool] zip 解压后仍无 main.exe, 检查 " + outdir)
        sys.exit(2)
    return exe


def ensure_model(tool_root, model, allow_dl):
    name, size, gb = MODELS[model]
    path = os.path.join(tool_root, name)
    if os.path.isfile(path) and os.path.getsize(path) >= size * 0.99:
        return path
    if not allow_dl:
        log(f"[model] 缺 {name}; 去掉 --no-download 允许自动下载, 或手动放到 {path}")
        sys.exit(2)
    log(f"[model] 下载 {name} (约 {gb}GB, HuggingFace, hf-mirror 兜底)...")
    os.makedirs(tool_root, exist_ok=True)
    if not download([HF + name, HF_MIRROR + name], path):
        log("[model] 下载失败; 手动下载后放到 " + path)
        sys.exit(2)
    return path


def pick_gpu(exe):
    try:
        r = subprocess.run([exe, "-la"], capture_output=True, timeout=60)
        names = re.findall(r'"([^"]+)"', (r.stdout or b"").decode("utf-8", "replace"))
        for n in names:
            if "Microsoft Basic" not in n and "Render Driver" not in n:
                return n
    except Exception:
        pass
    return None


def download_audio(url, workdir, cookie):
    try:
        import yt_dlp
    except ImportError:
        log("ERROR: 缺依赖, 先执行: python -m pip install -U yt-dlp")
        sys.exit(1)
    opts0 = {"quiet": True, "no_warnings": True}
    if "youtu" in url:
        opts0["extractor_args"] = {"youtube": {"player_client": ["mweb"]}}
        opts0["js_runtimes"] = {"node": {}}
        opts0["remote_components"] = ["ejs:github"]
        if cookie and os.path.isfile(cookie):
            opts0["cookiefile"] = cookie
    try:
        with yt_dlp.YoutubeDL(opts0) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        log(f"ERROR: 视频信息提取失败: {e}")
        sys.exit(1)
    vid = info.get("id") or "video"
    log(f"[meta] id={vid} duration={info.get('duration')}s title={info.get('title')}")
    if workdir is None:
        workdir = os.path.join(tempfile.gettempdir(), "video-decode", vid)
    os.makedirs(workdir, exist_ok=True)
    opts = dict(opts0)
    opts.update({
        "format": "bestaudio/best[ext=mp4]/18",
        "outtmpl": os.path.join(workdir, f"audio.{vid}.%(ext)s"),
        "noplaylist": True,
    })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio = ydl.prepare_filename(info)
    except Exception as e:
        log(f"ERROR: 音频下载失败: {e}")
        log("提示: SABR-only 实验下仅 format 18 可用时, 脚本已内置兜底; 若仍失败看 toolchain-notes.md")
        sys.exit(1)
    log(f"[audio] {audio}")
    return workdir, audio, info.get("duration")


def probe_duration(audio):
    try:
        import av
        with av.open(audio) as c:
            return float(c.duration / av.time_base) if c.duration else None
    except Exception:
        return None


def wrap500(text):
    return "\n".join(text[i : i + 500] for i in range(0, len(text), 500))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="无字幕视频 GPU ASR (Const-me/Whisper DirectCompute)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="视频 URL (先经 yt_transcript.py 确认真无字幕)")
    src.add_argument("--audio", help="已有音频/视频文件路径")
    ap.add_argument("--model", default="medium", choices=list(MODELS))
    ap.add_argument("--lang", default="zh", help="语言 (模型无自动检测, 必须显式; 默认 zh)")
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--gpu", default=None, help="指定 adapter 名; 缺省自动选第一个非基础渲染适配器")
    ap.add_argument("--tool-root", default=TOOL_ROOT_DEFAULT)
    ap.add_argument("--cookies", default=os.path.join(os.environ.get("LOCALAPPDATA", ""), "yt-cookies.txt"))
    ap.add_argument("--no-download", action="store_true", help="禁止自动下载工具/模型")
    ap.add_argument("--show-output", action="store_true", help="打印 main.exe 原始输出尾部 (调试)")
    args = ap.parse_args()

    allow_dl = not args.no_download
    exe = ensure_tool(args.tool_root, allow_dl)
    model_path = ensure_model(args.tool_root, args.model, allow_dl)
    log(f"[tool] {exe}")
    log(f"[model] {model_path}")

    duration = None
    if args.url:
        workdir, audio, duration = download_audio(args.url, args.workdir, args.cookies)
    else:
        audio = args.audio
        if not os.path.isfile(audio):
            log(f"ERROR: 文件不存在: {audio}")
            sys.exit(1)
        workdir = args.workdir or os.path.dirname(os.path.abspath(audio))
        duration = probe_duration(audio)
    os.makedirs(workdir, exist_ok=True)

    gpu = args.gpu or pick_gpu(exe)
    cmd = [exe]
    if gpu:
        cmd += ["-gpu", gpu]
    cmd += ["-m", model_path, "-f", audio, "-l", args.lang, "-nt", "-otxt"]
    log(f"[gpu] {gpu or 'default adapter'}")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=3600)
    except subprocess.TimeoutExpired:
        log("ERROR: 转写超时 (>60 分钟)")
        sys.exit(1)
    elapsed = time.time() - t0
    if args.show_output:
        sys.stdout.write((r.stdout or b"").decode("utf-8", "replace")[-3000:])
    if r.returncode != 0:
        tail = ((r.stdout or b"")[-1000:] + (r.stderr or b"")[-1000:]).decode("utf-8", "replace")
        log(f"ERROR: main.exe 退出码 {r.returncode}\n{tail}")
        sys.exit(1)
    log(f"[run] elapsed {elapsed:.0f}s")

    out_txt = os.path.splitext(audio)[0] + ".txt"
    if not os.path.isfile(out_txt):
        log(f"ERROR: 未找到输出文件 {out_txt}")
        sys.exit(1)
    text = open(out_txt, encoding="utf-8-sig").read().strip()
    if not text:
        log("ERROR: 转写结果为空")
        sys.exit(1)

    raw_out = os.path.join(workdir, "transcript.raw.txt")
    with open(raw_out, "w", encoding="utf-8") as f:
        f.write(text)
    out = os.path.join(workdir, "transcript.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(wrap500(text))

    cpm = round(len(text) / (duration / 60), 1) if duration else None
    log(f"[out] chars={len(text)} chars_per_min={cpm} elapsed={elapsed:.0f}s")
    log(f"TRANSCRIPT: {out}")


if __name__ == "__main__":
    main()
