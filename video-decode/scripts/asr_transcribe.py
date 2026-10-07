#!/usr/bin/env python3
"""asr_transcribe.py — 无字幕视频的 ASR 降级转写 (video-decode skill 的降级路径)

用法:
    python asr_transcribe.py --url "URL" [--model small|medium] [--lang zh] [--workdir DIR]
    python asr_transcribe.py --audio "path.m4a" [--model small|medium] [--lang zh] [--workdir DIR]

模型体积: small≈460MB, medium≈1.5GB (首次下载, HF 缓存后复用)
CPU 速度: medium int8 ≈ 0.75x 实时 (实测 18.5 分钟音频 → 14 分钟)

输出 (默认 <临时目录>/video-decode/<id>, 与 yt_transcript.py 一致):
    <workdir>/transcript.txt     清洗后纯文本 (按 500 字换行)
    <workdir>/transcript.raw.txt 转写过程实时落盘 (防中断丢失)
退出码: 0=成功, 1=错误

注意: --url 模式下音频落盘为 audio.<id>.<ext> 且默认按视频 id 分目录, 防止
共享目录里的陈旧音频被 yt-dlp 跳过下载后误转 (v0.1.15 实测坑)。
"""
import argparse
import os
import sys
import tempfile
import time


def patch_av():
    # faster-whisper 1.2.1 向 av.open 传 metadata_errors, 但 av 19 已移除该参数 -> 兼容 shim
    import av

    orig_open = av.open

    def _open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return orig_open(*args, **kwargs)

    av.open = _open


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="无字幕视频 ASR 转写")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="视频 URL (自动下载 bestaudio)")
    src.add_argument("--audio", help="已有音频文件路径")
    ap.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"])
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    workdir = args.workdir
    audio = args.audio
    if args.url:
        try:
            import yt_dlp
        except ImportError:
            print("ERROR: 缺依赖, 先执行: python -m pip install -U yt-dlp")
            sys.exit(1)
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                meta = ydl.extract_info(args.url, download=False)
        except Exception as e:
            print(f"ERROR: 视频信息提取失败: {e}")
            sys.exit(1)

        vid = meta.get("id") or "video"
        print(f"[meta] id={vid} duration={meta.get('duration')}s title={meta.get('title')}", flush=True)
        if workdir is None:
            workdir = os.path.join(tempfile.gettempdir(), "video-decode", vid)

        try:
            opts = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": os.path.join(workdir, f"audio.{vid}.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(args.url, download=True)
                audio = ydl.prepare_filename(info)
        except Exception as e:
            print(f"ERROR: 音频下载失败: {e}")
            sys.exit(1)
        print(f"[audio] {audio}", flush=True)

    if workdir is None:
        workdir = os.path.join(tempfile.gettempdir(), "video-decode", "asr")
    os.makedirs(workdir, exist_ok=True)

    patch_av()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: 缺依赖, 先执行: python -m pip install -U faster-whisper")
        sys.exit(1)

    t0 = time.time()
    print(f"[model] loading {args.model} (首次运行会下载模型) ...", flush=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    print(f"[model] ready in {time.time() - t0:.0f}s", flush=True)

    segments, info = model.transcribe(audio, language=args.lang, vad_filter=True, beam_size=5)
    print(f"[asr] duration={info.duration:.0f}s lang={info.language}", flush=True)

    raw_out = os.path.join(workdir, "transcript.raw.txt")
    parts = []
    with open(raw_out, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments):
            parts.append(seg.text)
            f.write(seg.text)
            f.flush()
            if i % 50 == 0:
                print(f"  seg {i} @ {seg.end:.0f}s / {info.duration:.0f}s ({time.time() - t0:.0f}s)", flush=True)

    text = "".join(parts)
    wrapped = "\n".join(text[i : i + 500] for i in range(0, len(text), 500))
    out = os.path.join(workdir, "transcript.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(wrapped)

    cpm = round(len(text) / (info.duration / 60), 1) if info.duration else None
    print(f"[out] chars={len(text)} chars_per_min={cpm} elapsed={time.time() - t0:.0f}s")
    print(f"TRANSCRIPT: {out}")


if __name__ == "__main__":
    main()
