"""
Evaluate predicted JSONL documents against gold JSONL documents.

Both inputs should be discopy-style JSONL files (e.g., after discopy-extract and
discopy-add-annotations). This is a lightweight wrapper around
`discopy.evaluate.conll.evaluate_docs`.
"""

import argparse
import logging
import sys
from typing import Optional

from discopy.evaluate.conll import evaluate_docs, print_results
from discopy_data.data.loaders.json import load_documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, help="Path to gold JSONL.")
    parser.add_argument("--pred", required=True, help="Path to predicted JSONL.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.9,
        help="IOU threshold for span matching (default: 0.9).",
    )
    return parser.parse_args()


def main() -> Optional[int]:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    gold = load_documents(open(args.gold))
    pred = load_documents(open(args.pred))

    logging.info(f"Loaded gold: {len(gold)} docs from {args.gold}")
    logging.info(f"Loaded pred: {len(pred)} docs from {args.pred}")

    gold_by_id = {d.doc_id: d for d in gold}
    pred_by_id = {d.doc_id: d for d in pred}
    common_ids = sorted(set(gold_by_id) & set(pred_by_id))

    if not gold or not pred:
        sys.stderr.write("No documents to evaluate (gold or pred empty).\n")
        return 1
    if not common_ids:
        sys.stderr.write("No overlapping doc IDs between gold and pred.\n")
        return 1

    if len(common_ids) != len(gold) or len(common_ids) != len(pred):
        logging.info(f"Restricting to overlapping doc IDs: {len(common_ids)}")

    gold_eval = [gold_by_id[i] for i in common_ids]
    pred_eval = [pred_by_id[i] for i in common_ids]

    print_results(evaluate_docs(gold_eval, pred_eval, threshold=args.threshold), title="ALL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
