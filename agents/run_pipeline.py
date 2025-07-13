#!/usr/bin/env python3
"""
CLI: Evaluator → Coach in one shot.
Example:
   python run_pipeline.py se-1.pdf se-1.json "Software Engineer"
"""

import argparse, json, subprocess, sys, tempfile, time
from pathlib import Path
from agents.evaluator.evaluator_agent import EvaluatorAgent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("structured_json")
    ap.add_argument("role", help='"Software Engineer" or "Product Manager"')
    args = ap.parse_args()

    # 1. run Evaluator
    eval_out = Path(args.structured_json).with_suffix(".evaluation.json")
    if not eval_out.exists():
        subprocess.run(
            [sys.executable, "agents/evaluator/evaluate.py",
             args.pdf, args.structured_json, "--role", args.role],
            check=True,
        )
    print("✓ Evaluator output:", eval_out)

    # 2. run Coach
    coach_out = eval_out.with_suffix(".feedback.json")
    subprocess.run(
    [
        sys.executable,
        "-m", "agents.coach.coach",                # <-- this line
        str(eval_out),
        "--role", args.role,
        "--structured_json", args.structured_json,
    ],
    check=True,
)
    print("✓ Coach output:", coach_out)

if __name__ == "__main__":
    main()
