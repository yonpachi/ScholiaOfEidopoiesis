"""
run_all.py — 全 Part オーケストレーション

実行:
    python sim/run_all.py
    python sim/run_all.py --parts 1,2,3,4
    python sim/run_all.py --out-dir data/20260101_120000 --plot-only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SIM_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM_DIR))

from _common import resolve_out_dir  # noqa: E402

SIM_PARTS = (1, 2, 3, 4, 5, 6, 7)


def run_part_script(
    part: int,
    out_dir: Path,
    *,
    seed: int,
    trials_p1: int,
    trials_p2: int,
    trials_p3: int,
    trials_p4: int,
    trials_p5: int,
    trials_p6: int,
    trials_p7: int,
    plot_only: bool,
) -> None:
    script = SIM_DIR / f"part{part}" / "run.py"
    if not script.exists():
        print(f"[Part{part}] スキップ: {script} なし")
        return
    cmd = [sys.executable, str(script), "--out-dir", str(out_dir)]
    if part in SIM_PARTS:
        if plot_only:
            cmd.append("--plot-only")
        else:
            cmd.extend(["--seed", str(seed)])
            if part == 1:
                cmd.extend(["--trials", str(trials_p1)])
            elif part == 2:
                cmd.extend(["--trials", str(trials_p2)])
            elif part == 3:
                cmd.extend(["--trials", str(trials_p3)])
            elif part == 4:
                cmd.extend(["--trials", str(trials_p4)])
            elif part == 5:
                cmd.extend(["--trials", str(trials_p5)])
            elif part == 6:
                cmd.extend(["--trials", str(trials_p6)])
            elif part == 7:
                cmd.extend(["--trials", str(trials_p7)])
    print(f"\n--- Part{part} ---")
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def main() -> None:
    p = argparse.ArgumentParser(description="Run all sim parts + plots")
    p.add_argument("--out-dir", type=Path, default=None, help="output directory (default: data/<timestamp>)")
    p.add_argument("--parts", type=str, default="1,2,3,4,5,6,7", help="comma-separated part numbers")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials-p1", type=int, default=20000)
    p.add_argument("--trials-p2", type=int, default=5000)
    p.add_argument("--trials-p3", type=int, default=100000)
    p.add_argument("--trials-p4", type=int, default=10000)
    p.add_argument("--trials-p5", type=int, default=50000)
    p.add_argument("--trials-p6", type=int, default=50000)
    p.add_argument("--trials-p7", type=int, default=50000, help="Part6 trials when running Part7")
    p.add_argument("--plot-only", action="store_true", help="skip Go sim, plot existing CSV only")
    args = p.parse_args()

    parts = [int(x.strip()) for x in args.parts.split(",") if x.strip()]
    has_sim = any(n in SIM_PARTS for n in parts) and not args.plot_only

    if args.out_dir is not None:
        out_dir = resolve_out_dir(args.out_dir, create=True)
    elif has_sim:
        out_dir = resolve_out_dir(None, create=True)
    else:
        out_dir = resolve_out_dir(None, create=False)

    print(f"出力: {out_dir}")

    for part in parts:
        run_part_script(
            part,
            out_dir,
            seed=args.seed,
            trials_p1=args.trials_p1,
            trials_p2=args.trials_p2,
            trials_p3=args.trials_p3,
            trials_p4=args.trials_p4,
            trials_p5=args.trials_p5,
            trials_p6=args.trials_p6,
            trials_p7=args.trials_p7,
            plot_only=args.plot_only or part not in SIM_PARTS,
        )

    print(f"\n全処理完了。出力フォルダ: {out_dir}")


if __name__ == "__main__":
    main()
