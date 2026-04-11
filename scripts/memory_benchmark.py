import argparse
import gc
import json
import os
import resource
import statistics
import subprocess
import sys
import tracemalloc
from pathlib import Path

import eml_parser


def rss_mb() -> float:
    # ru_maxrss is KB on Linux.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def process_eml_collection(eml_dir: Path, include_raw_body: bool, include_attachment_data: bool) -> dict:
    parser = eml_parser.EmlParser(
        include_raw_body=include_raw_body,
        include_attachment_data=include_attachment_data,
    )
    bytes_total = 0
    body_chars = 0
    attachment_count = 0

    tracemalloc.start()
    rss_before = rss_mb()

    for eml_file in sorted(eml_dir.glob("*.eml")):
        payload = eml_file.read_bytes()
        bytes_total += len(payload)
        parsed = parser.decode_email_bytes(payload)

        body = parsed.get("body", [])
        if body:
            body_chars += sum(len(x.get("content", "")) for x in body)

        attachment_count += len(parsed.get("attachment", []))
        del parsed, payload

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()

    return {
        "rss_delta_mb": max(0.0, rss_mb() - rss_before),
        "trace_peak_mb": peak / (1024 * 1024),
        "bytes_total": bytes_total,
        "body_chars": body_chars,
        "attachment_count": attachment_count,
        "trace_current_mb": current / (1024 * 1024),
    }


def _run_single_mode_subprocess(eml_dir: Path, include_raw_body: bool, include_attachment_data: bool) -> dict:
    command = [
        sys.executable,
        __file__,
        "--single-run",
        "--eml-dir",
        str(eml_dir),
        "--include-raw-body",
        str(int(include_raw_body)),
        "--include-attachment-data",
        str(int(include_attachment_data)),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True, env=os.environ.copy())
    return json.loads(result.stdout.strip())


def run_profile(eml_dir: Path, runs: int) -> None:
    legacy = []
    optimized = []

    for _ in range(runs):
        legacy.append(_run_single_mode_subprocess(eml_dir, include_raw_body=True, include_attachment_data=True))
        optimized.append(_run_single_mode_subprocess(eml_dir, include_raw_body=False, include_attachment_data=False))

    legacy_rss = [x["rss_delta_mb"] for x in legacy]
    optimized_rss = [x["rss_delta_mb"] for x in optimized]
    legacy_peak = [x["trace_peak_mb"] for x in legacy]
    optimized_peak = [x["trace_peak_mb"] for x in optimized]

    avg_legacy_rss = statistics.mean(legacy_rss)
    avg_optimized_rss = statistics.mean(optimized_rss)
    avg_legacy_peak = statistics.mean(legacy_peak)
    avg_optimized_peak = statistics.mean(optimized_peak)

    rss_improvement = ((avg_legacy_rss - avg_optimized_rss) / avg_legacy_rss * 100) if avg_legacy_rss else 0.0
    peak_improvement = ((avg_legacy_peak - avg_optimized_peak) / avg_legacy_peak * 100) if avg_legacy_peak else 0.0

    print("=== Memory Benchmark (EML parse mode comparison) ===")
    print(f"Input dir: {eml_dir}")
    print(f"Runs: {runs}")
    print()
    print("Mode,Avg RSS Delta MB,Avg tracemalloc peak MB")
    print(f"legacy(raw+attachment),{avg_legacy_rss:.2f},{avg_legacy_peak:.2f}")
    print(f"optimized(no-raw/no-attachment),{avg_optimized_rss:.2f},{avg_optimized_peak:.2f}")
    print()
    print(f"RSS improvement: {rss_improvement:.2f}%")
    print(f"Tracemalloc peak improvement: {peak_improvement:.2f}%")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Benchmark memory usage for EML parsing modes")
    arg_parser.add_argument("--eml-dir", default="eml-collection", help="Directory with .eml files")
    arg_parser.add_argument("--runs", type=int, default=3, help="Number of repeated runs per mode")
    arg_parser.add_argument("--single-run", action="store_true", help="Internal mode: perform one parse run and print JSON")
    arg_parser.add_argument("--include-raw-body", type=int, choices=[0, 1], default=1)
    arg_parser.add_argument("--include-attachment-data", type=int, choices=[0, 1], default=1)
    args = arg_parser.parse_args()

    if args.single_run:
        output = process_eml_collection(
            Path(args.eml_dir),
            include_raw_body=bool(args.include_raw_body),
            include_attachment_data=bool(args.include_attachment_data),
        )
        print(json.dumps(output))
    else:
        run_profile(Path(args.eml_dir), runs=max(1, args.runs))
