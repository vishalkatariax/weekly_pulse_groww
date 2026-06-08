#!/usr/bin/env python3
"""Run Phase 2: Thematic Analysis and Summary Generation."""

import argparse

from agent.phase2 import run_phase2


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Thematic Analysis")
    parser.add_argument("--input", default="outputs/02_anonymized_reviews.csv", help="Input anonymized review CSV")
    parser.add_argument("--output", default="outputs/phase2", help="Output directory for phase2 artifacts")
    parser.add_argument("--sample-size", type=int, default=1000, help="Maximum reviews to analyze")
    parser.add_argument("--dry-run", action="store_true", help="Do not call the real LLM client")
    parser.add_argument("--batch-tokens", type=int, default=1500, help="Approximate token budget per batch")
    args = parser.parse_args()

    output = run_phase2(
        input_csv=args.input,
        output_dir=args.output,
        sample_size=args.sample_size,
        dry_run=args.dry_run,
        max_batch_tokens=args.batch_tokens,
    )

    print(f"Phase 2 summary written to {args.output}/phase2_summary.json")
    print(f"Sampled reviews: {output['sampled_count']} / {output['review_count']}")
    print(f"Pulse word count: {output['summary']['pulse_word_count']}")
    print("Actions:")
    for i, action in enumerate(output['summary']['actions'], start=1):
        print(f"  {i}. {action}")


if __name__ == "__main__":
    main()
