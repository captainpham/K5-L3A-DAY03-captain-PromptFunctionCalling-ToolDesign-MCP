"""Append measured run evidence and student notes to version_log.csv."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "version", "author", "changed_artifact", "artifact_version", "prompt_hash",
    "tools_hash", "reason", "hypothesis", "metric_before", "metric_after", "run_file",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_file", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/version_log.csv")
    parser.add_argument("--author", default="team")
    parser.add_argument("--changed-artifact", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--metric-before", type=float, default=None,
                        help="Previous run's case_accuracy; omit for baseline.")
    args = parser.parse_args()
    run_path = args.run_file.resolve()
    run = json.loads(run_path.read_text(encoding="utf-8"))
    # Read evidence from the run, never from the current (possibly edited) artifacts.
    row = {key: run[key] for key in
           ("version", "artifact_version", "prompt_hash", "tools_hash")}
    try:
        run_label = run_path.relative_to(ROOT).as_posix()
    except ValueError:
        run_label = str(run_path)
    row.update(
        author=args.author, changed_artifact=args.changed_artifact,
        reason=args.reason, hypothesis=args.hypothesis,
        metric_before="" if args.metric_before is None else args.metric_before,
        metric_after=run["summary"]["case_accuracy"], run_file=run_label,
    )
    has_content = args.output.exists() and args.output.stat().st_size > 0
    if has_content:
        with args.output.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != FIELDS:
                parser.error("Output CSV has an unexpected header; no changes written.")
            for existing in reader:
                if existing["run_file"] == run_label:
                    print("Run already logged; no changes written.")
                    return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if not has_content:
            writer.writeheader()
        writer.writerow(row)
    print(f"Logged {row['version']}: case_accuracy={row['metric_after']}")


if __name__ == "__main__":
    main()
