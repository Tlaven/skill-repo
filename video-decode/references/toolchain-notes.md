# Toolchain Notes — 本机环境事实、坑与降级路径

## 本机环境事实 (2026-10 实测)

| 项 | 状态 |
|---|---|
| Python | pyenv-win 3.12.4, 命令用 `python` (shim 正常) |
| `py` launcher | **损坏**: 指向不存在的 `C:\Apps\Python3.12\python.exe`, 不要用 `py -3.12` |
| yt-dlp | 默认未装; `python -m pip install -q yt-dlp` 即装 (脚本自动做) |
| ffmpeg | 默认未装; ASR 路径不需要系统 ffmpeg (faster-whisper 用 PyAV 内置解码) |
| GPU | AMD Radeon RX 6650 XT (8GB), **无 NVIDIA** → CTranslate2 CUDA 不可用 (实测 `get_cuda_device_count()==0`); GPU ASR 走 DirectCompute (见"GPU ASR 快路径") |
| CPU | i5-12400F (6C12T); faster-whisper medium int8 ≈ 0.5~0.75x 实时 (备用路径) |
| 临时目录 | `C:\Users\TL\AppData\Local\Temp\opencode` (已预授权) |
| 字幕输出 | `%TEMP%\video-decode\<videoId>\` (脚本默认; 注意**不在** Temp\opencode 下, 实测找错过) |
| yt-cookies | `%LOCALAPPDATA%\yt-cookies.txt` (含 Google 登录态 — **勿外传/勿入库**; `yt_cookies.py` / `yt_login_watch.py` 默认输出即此路径, 不要改到仓库目录) |

## PowerShell 5.1 坑 (实测)

1. **管道 BOM**: native 命令 stdout 管道给 python 时带 UTF-8 BOM → 用 `json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))`
2. **`%` 模板必炸**: 本环境 shell 按 cmd.exe 语义解析。实测两种失败: `--print "%(title)s"` 报 "'%' 不是内部或外部命令"; `-o "...audio.%(ext)s"` 导致 URL 参数丢失。**规则: 命令行里绝不出现 `%`**; 一律用 Python API / 本 skill 脚本, 或 `--dump-single-json` + python 按 `utf-8-sig` 解析
3. **中文乱码**: GBK/UTF-8 不匹配导致 `����` → 脚本已 `sys.stdout.reconfigure(encoding="utf-8")`; 手写脚本时同样处理
4. **长操作 timeout**: 首次解析/下载可能 1~2 分钟, 命令 timeout 设 ≥300000ms

## 手动兜底命令 (脚本不可用时)

```bash
# 查字幕清单
python -m yt_dlp --no-warnings --list-subs "URL"

# 下中文字幕 (官方优先; 自动字幕同名时优先官方)
python -m yt_dlp --no-warnings --skip-download --write-subs --write-auto-subs --sub-langs "zh" --sub-format vtt -o "DIR/video" "URL"

# 年龄限制/需要登录的视频: 加 --cookies-from-browser chrome
```

## BOT_CHECK (机器人验证) 升级阶梯

症状: `Sign in to confirm you're not a bot`。这是**高频请求后的 IP 临时风控, 不是脚本问题**。
实测 (2026-10-03): 同一 URL 前一小时正常, 连续约 15 次请求后触发; 换 `player_client=ios/android/tv/mweb/web_embedded/web_safari/tv_embedded/web_creator/tv_simply` **全部无效**。二次实测 (2026-10-03 晚): 新一轮风控持续 >1.5h, 90 秒冷却/多次重试均未解。

> **本机快捷路径 (2026-10-03 起已落地)**: POT provider + 专用登录 cookies 都已装好。BOT_CHECK 时首选:
> `python scripts/yt_transcript.py --url "URL" --cookies "%LOCALAPPDATA%\yt-cookies.txt" --player-client mweb`
> 实测成功组合 (2026-10-03 E212): cookies + `--player-client mweb` (+ 脚本内置 `ignore_no_formats_error`)。默认客户端遇 cookies 报 "The page needs to be reloaded"。**媒体格式下载 (ASR 降级) 已验证**: 再加 `--js-runtimes node --remote-components ejs:github` (自动拉取 nsig 求解脚本, 格式全出, 如 140 m4a 129k)。
> (cookies 失效时按下方 "持久解决方案" 刷新, 约 10 秒)

按顺序升级:
1. **冷却重试** (最有效): 等几分钟~几小时后重试 (实测: 数十分钟~数小时后同一 IP 自动恢复, 无需 cookies)
2. **cookies-from-browser**: 需**完全退出浏览器** (含后台进程/启动增强), 否则报 `Could not copy Chrome cookie database`。**2026-10-03 二次实测: 此路对现代 Chrome/Edge 基本已死** — yt-dlp 2026.08.19 不支持 App-Bound Encryption (v20 cookie), 即使浏览器完全退出也报 `Failed to decrypt with DPAPI` (yt-dlp issue #10927; 本机源码确认 `has_app_bound: False`)
   ```bash
   python scripts/yt_transcript.py --url "URL" --cookies-from-browser edge
   ```
3. **cookies.txt (现代浏览器唯一 cookie 路)**: 装扩展 "Get cookies.txt LOCALLY" → 打开 youtube.com → 导出 Netscape 格式 → `--cookies "path\cookies.txt"` (扩展经浏览器 API 解密导出, 不受 ABE 影响)
4. 长时间冷却仍失败: 风控跟 IP, 需换网络环境

## YouTube 风控持久解决方案 (2026-10-03 实战落地)

根因: 本机流量走 FlClash 代理 (env `HTTP(S)_PROXY=127.0.0.1:7890`), 出口为**机房 IP** → YouTube 风控频繁且顽固; 直连被墙不可用; FlClash 无外部控制端口 (netstat 仅 7890/1053), 无法自动切节点。

已装组件:
1. **bgutil POT provider (script 模式)**: `%USERPROFILE%\bgutil-ytdlp-pot-provider` (node 22, 已 `npm ci` + `npx tsc`) + pip 插件 `bgutil-ytdlp-pot-provider` (2.0.1)。yt-dlp 自动加载 (verbose 可见 "Generating a ... PO Token")。**仅 POT 不足以过机房 IP 风控, 必须叠加登录 cookies**。
2. **专用登录 profile**: `%LOCALAPPDATA%\yt-browser-profile` (独立于用户日常浏览器)
   - 首次登录: 启动
     `chrome.exe --user-data-dir=%LOCALAPPDATA%\yt-browser-profile --remote-debugging-port=9222 --remote-allow-origins=* "https://accounts.google.com/ServiceLogin?continue=https://www.youtube.com/"`
     → 用户登录一次 → `python scripts/yt_login_watch.py <out> [deadline_s]` 自动等待并导出 (默认输出 `%LOCALAPPDATA%\yt-cookies.txt`)
   - 刷新 (profile 保持登录, cookies 过期时): `python scripts/yt_cookies.py <out>` (附着运行中实例, 否则无头启动导出; 默认输出同上)
3. **cookies 落盘**: `%LOCALAPPDATA%\yt-cookies.txt`, 用法 `--cookies` 传给 yt_transcript.py

实测排除的死路 (不要重走):
- **visitor cookies (未登录) 不够**: 机房 IP 上仍被 BOT_CHECK
- **yt-dlp OAuth 已废弃**: 源码 `_base.py` "Login with OAuth is no longer supported"
- **cookies-from-browser (Chrome/Edge)**: ABE v20 无法解密 (yt-dlp 无 app_bound 支持); `yt-dlp-ChromeCookieUnlock` 插件只解文件锁、不解 ABE
- **复制 profile + CDP 读取**: Chrome 在副本/自定义 user-data-dir 中无法使用 app-bound key → 清空原 v20 cookies (实测 3296→0), 新 cookies 回落为 v10; 完全不可行 (v10 下 Chrome 会自动降级, 但读不到原库)
- **Chrome 136+ 默认 profile 禁用 --remote-debugging-port** (自定义 user-data-dir 不受限)
- **公共代理服务**: Invidious 字幕 200+空 body (POT 拦截); Piped/Cobalt/转录服务大面积不可用; f5.si videoplayback 有 JS 挑战
- **rssyes.com 播客镜像**: 频道被收录时可用 (feed `rssyes.com/yt-rss/<channelId>.xml`), 但新视频滞后约 1 天

## 无 cookies 备用路径 (2026-10-03 实测, "视频很新 + IP 被风控" 场景)

全部实测结果 (1 天前发布的 83 分钟视频, 人工 zh-Hans 字幕存在):
- **webfetch 抓 watch 页**: 200 但返回 LOGIN_REQUIRED 风控页 (无 captionTracks); 但 **oEmbed 可用**: `youtube.com/oembed?url=...&format=json` (标题/频道名)
- **Invidious**: 字幕列表端点可能通, 但字幕下载返回 **200 + 空 body** (YouTube POT 拦截, 实例侧同样拿不到, 换实例无解); videos API 多数禁用/403 (nadeko); f5.si 的 videos API + `?local=true` 可用 (拿到代理音频 URL), 但其 videoplayback 有 JS 挑战 (Anubis 类, curl_cffi 也过不了); nadeko 对非浏览器 TLS 直接 403; yewtu/nerdvpn/jing 有 bot 墙; protokolla 有 CAPTCHA
- **Piped API**: kavin.rocks / adminforge 403, 其余 transport error
- **Cobalt**: 公共实例大面积死亡/要 JWT/SSL 错; 官方实例列表本机不可达
- **第三方转录服务**: tactiq 401 (App Check), kome.ai 522, youtubetotranscript Cloudflare 403, youtubetranscript.com 纯前端 JS
- **rssyes.com (YouTube→播客镜像)**: 若频道被收录, feed = `https://rssyes.com/yt-rss/<channelId>.xml`, 音频 = `https://rs-host.rssyes.com/rssyes/<videoId>.mp3?t=<ts>`; **新视频滞后约 1 天** (可构造 URL 探测, 404=未生成)。拿到 mp3 后走 ASR 阶梯
- **元数据备用**: iTunes Search API (`itunes.apple.com/search?term=...&entity=podcast`) 可找 feedUrl
- **搜索备用**: Exa 429 时用 `html.duckduckgo.com/html/?q=...` (webfetch 可通)

## ASR 降级阶梯 (仅当 yt_transcript.py 退出码 2 = NO_SUBTITLES)

**先排除"假 NO_SUBTITLES" (2026-10-04 实测, 8BN8p5xDkzw)**: 无 cookies 首跑输出 exit 2 + `[meta] duration=None`, 但视频实际有官方手工中文字幕; 用 `--cookies ... --player-client mweb` 重跑即成功 (5205 字, cpm 331)。根因: 风控/降级路径返回的 info 缺 duration 与字幕列表, `ignore_no_formats_error` 静默放行。**规则: exit 2 且 duration=None ⇒ 先持久方案重跑; duration 正常且仍 exit 2 才走 ASR**。

**本机 (无 NVIDIA) 首选 GPU 快路径**: `python scripts/gpu_asr_constme.py --url "URL"` — AMD DirectCompute, 实测 4~7x 实时 (见下节)。CPU 阶梯 (`asr_transcribe.py`) 仅在 GPU 不可用时使用。

**先向用户说明成本再动手**。实测数据 (2026-10-03, bilibili 18.5 分钟视频):
- 模型下载: small≈460MB / medium≈1.5GB (首次; HF 缓存后复用)
- CPU 转写: medium int8 ≈ **0.75x 实时** (18.5 分钟音频 → 14 分钟); small 约快 2~3 倍
- 让用户选模型: 试跑用 small, 要准用 medium

**一条命令 (脚本内置全部坑的修补, 自动下音频)**:

```bash
python scripts/asr_transcribe.py --url "URL" --model medium --workdir "DIR"
# 已有音频: --audio "path.m4a"
```

**脚本内置的三个实测坑修补 (不要绕过脚本手写)**:
1. `faster-whisper 1.2.1` 与 `av 19` 不兼容: av 19 移除了 `metadata_errors` 参数, faster-whisper 仍在传 → 脚本用 shim 剥掉该参数
2. 本环境命令行含 `%` 模板 (`audio.%(ext)s`) 会被吞导致 URL 参数丢失 → 音频下载必须走 Python API, 脚本已处理
3. **陈旧音频误转** (2026-10-05 实测, BV1P8eK62EQt): 原实现 `audio.%(ext)s` + 共享 asr 目录, 目录里已有上一个视频的 `audio.m4a` 时 yt-dlp 不会真正重下 (bilibili 格式无 filesize, 校验不了), ASR 静默把 55 分钟旧音频整段转完 (raw 内容与目标视频完全无关)。已修: `--url` 默认 workdir → `<临时目录>/video-decode/<id>` (与 yt_transcript 一致), 音频命名 `audio.<id>.<ext>`, 下载前打印 `[meta] id/duration/title`。**规则: ASR 开始前核对 `[meta] duration` 与 meta.json 一致、raw 开头与标题语义相符, 不一致立刻停**

**其他注意**:
- HF 符号链接警告 (Windows 无 Developer Mode) 无害可忽略
- medium 模型中文输出可能是**繁体** (实测); 转简体是后续演化项 (opencc/zhconv)
- bilibili 的"字幕"只有 danmaku (弹幕 XML), 不是转写文本; `pick_sub` 会正确忽略并报 NO_SUBTITLES (已实测)

## GPU ASR 快路径 (AMD DirectCompute, 2026-10-09 落地)

本机无 NVIDIA, CTranslate2/faster-whisper 无法用 GPU; 改用 **Const-me/Whisper** (D3D11 compute shaders, 任何硬件 GPU 可用, 免安装绿色包)。

- 工具缓存 (已装, 勿删): `%LOCALAPPDATA%\video-decode\const-whisper\` — `cli\main.exe` + `Whisper.dll` (release 1.12.0 cli.zip) + `ggml-medium.bin` (1.43GB)
- 一条命令: `python scripts/gpu_asr_constme.py --url "URL"` (或 `--audio "path"`; 缺工具/模型自动下载并打印体量, `--no-download` 禁用; 默认 zh, 可 `--model small|medium|large-v3`)
- 实测: 610s 音频 → 83.5s (≈7.3x 实时); 631s → 147s (≈4.3x); 1957s → 273s (≈7.2x) — GPU 占用/热状态会波动, 均远快于实时; VRAM 占用 medium ≈2.2GB
- **坑 (脚本已内置修补)**:
  1. 音频下载: BOT_CHECK 组合 (cookies+mweb) 遇 **SABR-only 流媒体实验** 时 `bestaudio` 全无 URL ("Requested format is not available", yt-dlp issue #12482), 仅 format 18 (360p mp4 含 AAC 音轨) 可用 → 脚本用 `bestaudio/best[ext=mp4]/18` 兜底, 对 ASR 够用 (2026-10-09 复测: 该兜底在 mweb 下确能选中 format 18; 但手动换用更窄的 `bestaudio[ext=m4a]/bestaudio` 会误报不可用 — 复现脚本行为时用脚本原样选择器)
  2. main.exe 的 stdout 在 GBK 终端下**中文乱码**, 但 `-otxt` 落盘的 txt 完好 (UTF-8 BOM, 读取用 `utf-8-sig`)
  3. 模型**无自动语言检测** → 必须显式 `-l` (脚本默认 zh); 其余常用参数: `-nt` (无时间戳), `-otxt`
  4. 输出文件 = 输入音频同目录同名 `.txt` (如 `audio.<id>.txt`); 脚本负责搬运成 `transcript.txt` + `transcript.raw.txt`
  5. 手动兜底 (脚本不可用时):
     ```bash
     & "$env:LOCALAPPDATA\video-decode\const-whisper\cli\main.exe" -m "$env:LOCALAPPDATA\video-decode\const-whisper\ggml-medium.bin" -gpu "AMD Radeon RX 6650 XT" -f "audio.mp4" -l zh -nt -otxt
     ```

## 已知边界 / 后续可演化

- **滚动重复行**: 当前清洗只做"连续完全相同行去重"; 若遇到字幕呈 `abc / bc def` 递增滚动模式, 需扩展清洗逻辑 (实际使用中遇到再固化)
- **行级拼接吃空格** (2026-10-04 发现并已修): `clean_vtt` 原 `"".join` 逐行拼接, VTT 断行处词间空格丢失 (实测 "You know the rules / and so do I" → "therulesand")。已改为 `_boundary_space` 判定: 西文↔西文 (含数字、英文句标点后接新句) 补空格; CJK↔任意、前联标点 (如引号开) 不补。离线测试 + dQw4w9WgXcQ 实测通过
- **bilibili** (2026-10-03 实测): 多数视频无字幕 (只有弹幕), 直接走 ASR 阶梯; `pick_sub` 行为正确
- **繁体输出**: medium 模型中文可能输出繁体, 可考虑加 zhconv/opencc 转换 (等再次遇到再固化)
- **直播/无自动字幕**: 走同一 ASR 阶梯
