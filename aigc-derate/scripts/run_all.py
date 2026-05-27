"""
端到端编排脚本：串联 aigc-derate 全部工作流阶段。

用法:
    python run_all.py --report "查重报告.docx" --thesis "论文.docx" --route de --target red
    python run_all.py --report "查重报告.docx" --thesis "论文.docx" --route en --target yellow
    python run_all.py --resume run_state.json
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

PHASES = [
    {'name': 'detect',   'desc': '检测颜色标记'},
    {'name': 'translate', 'desc': '往返翻译'},
    {'name': 'replace',  'desc': '批量写回文档'},
    {'name': 'check',    'desc': '字数偏差检查'},
    {'name': 'clear',    'desc': '清除颜色标记'},
]


def run_cmd(cmd, desc):
    """运行子进程命令，打印进度，失败则返回 False。"""
    print(f"\n{'='*60}")
    print(f"[{desc}] {' '.join(cmd)}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"[FAIL] {desc} (退出码 {result.returncode}, {elapsed:.1f}s)")
        return False
    print(f"[OK] {desc} ({elapsed:.1f}s)")
    return True


def save_state(state_path, state):
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='aigc-derate 端到端工作流')
    parser.add_argument('--report', help='查重报告 docx 文件路径')
    parser.add_argument('--thesis', help='论文 docx 文件路径')
    parser.add_argument('--route', choices=['de', 'en', 'de-en'], default='de',
                        help='翻译路线（默认 de）')
    parser.add_argument('--target', choices=['red', 'yellow', 'all'], default='red',
                        help='处理目标（默认 red）')
    parser.add_argument('--glossary', help='自定义术语保护词汇表 JSON')
    parser.add_argument('--state-file', default='run_state.json', help='状态文件路径')
    parser.add_argument('--resume', action='store_true', help='从上次断点继续')
    args = parser.parse_args()

    state_path = args.state_file

    # 恢复模式
    if args.resume:
        if not os.path.exists(state_path):
            print(f"状态文件不存在: {state_path}")
            return 1
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"恢复状态: 已完成阶段 {state.get('completed_phases', [])}")
        args.report = state.get('report', args.report)
        args.thesis = state.get('thesis', args.thesis)
        args.route = state.get('route', args.route)
        args.target = state.get('target', args.target)
        args.glossary = state.get('glossary', args.glossary)
    else:
        if not args.report or not args.thesis:
            parser.error('非恢复模式需要 --report 和 --thesis')
        state = {
            'report': os.path.abspath(args.report),
            'thesis': os.path.abspath(args.thesis),
            'route': args.route,
            'target': args.target,
            'glossary': args.glossary,
            'completed_phases': [],
            'started_at': datetime.now().isoformat(),
        }

    report = os.path.abspath(args.report)
    thesis = os.path.abspath(args.thesis)
    colors_json = os.path.join(SCRIPT_DIR, 'colors.json')
    pairs_json = os.path.join(SCRIPT_DIR, 'pairs.json')
    thesis_bak = thesis.replace('.docx', '_bak.docx')

    completed = set(state.get('completed_phases', []))

    # Phase 1: detect
    if 'detect' not in completed:
        cmd = [PYTHON, 'detect_colors.py', report, '-o', colors_json]
        if not run_cmd(cmd, PHASES[0]['desc']):
            save_state(state_path, state)
            return 1
        completed.add('detect')
        state['completed_phases'] = sorted(completed)
        save_state(state_path, state)

    # Phase 2: translate
    if 'translate' not in completed:
        cmd = [PYTHON, 'roundtrip.py', colors_json, '-o', pairs_json,
               '--route', args.route, '--target', args.target]
        if args.glossary:
            cmd += ['--glossary', args.glossary]
        if os.path.exists(pairs_json):
            cmd.append('--resume')
        if not run_cmd(cmd, PHASES[1]['desc']):
            save_state(state_path, state)
            return 1
        completed.add('translate')
        state['completed_phases'] = sorted(completed)
        save_state(state_path, state)

    # Phase 3: replace (requires editing-thesis-docx CLI)
    if 'replace' not in completed:
        print(f"\n{'='*60}")
        print(f"[{PHASES[2]['desc']}] 需要手动执行以下命令:")
        print(f"  python cli.py replace-batch-by-index --pairs-file {pairs_json} --backup {thesis}")
        print(f"\n备份文件将生成: {thesis_bak}")
        resp = input("完成后输入 y 继续，输入 q 退出: ").strip().lower()
        if resp != 'y':
            save_state(state_path, state)
            print(f"已保存状态到 {state_path}，可用 --resume 继续")
            return 0
        completed.add('replace')
        state['completed_phases'] = sorted(completed)
        save_state(state_path, state)

    # Phase 4: check length diff
    if 'check' not in completed:
        if os.path.exists(thesis_bak):
            cmd = [PYTHON, 'check_length_diff.py', thesis_bak, thesis]
            if not run_cmd(cmd, PHASES[3]['desc']):
                save_state(state_path, state)
                return 1
        else:
            print(f"[SKIP] {PHASES[3]['desc']}: 备份文件不存在 ({thesis_bak})")
        completed.add('check')
        state['completed_phases'] = sorted(completed)
        save_state(state_path, state)

    # Phase 5: clear colors
    if 'clear' not in completed:
        cmd = [PYTHON, 'clear_colors.py', thesis]
        if not run_cmd(cmd, PHASES[4]['desc']):
            save_state(state_path, state)
            return 1
        completed.add('clear')
        state['completed_phases'] = sorted(completed)
        save_state(state_path, state)

    elapsed = (datetime.now() - datetime.fromisoformat(state['started_at'])).total_seconds()
    print(f"\n{'='*60}")
    print(f"全部完成! 总耗时 {elapsed/60:.1f} 分钟")
    print(f"\n建议后续步骤:")
    print(f"  python cli.py check-style \"{thesis}\"")
    print(f"  python cli.py read-stats \"{thesis}\"")
    print(f"{'='*60}")
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
