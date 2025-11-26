#!/usr/bin/env python
"""
Build TwiConv gold JSONL for a split and optionally produce parser input.

For each ID:
- Find raw and ann files (PDTB-style 34-column rows, one relation per line).
- Tokenize raw with discopy-tokenize.
- Map spans to tokens, attach all relations, and append to gold JSONL.
- Optionally write the tokenized doc (with doc_id set) to a parser-input JSONL.

Example:
    source .venv/bin/activate
    python scripts/twiconv_build_split.py \
      --ids "085 101 074 082 190 081 036 004 138 112 172 516 010 091 196 557 087 184 092" \
      --raw-dir data/twiconv/PDTB_Annotations/raw \
      --ann-dir data/twiconv/PDTB_Annotations/ann/raw \
      --gold-out data/twiconv/gold/test.jsonl \
      --pred-in data/twiconv/tmp/test.tokenized.jsonl \
      --tmp-dir data/twiconv/tmp
"""

import argparse
import glob
import json
import subprocess
from pathlib import Path

from discopy_data.data.loaders.json import load_documents
from discopy_data.data.relation import Relation

# PDTB-style fields in ann files
FIELDS = [
    "Relation", "ConnSpanList", "ConnSrc", "ConnType", "ConnPol", "ConnDet", "ConnFeatSpanList",
    "Conn1", "SClass1A", "SClass1B", "Conn2", "SClass2A", "SClass2B", "Sup1SpanList",
    "Arg1SpanList", "Arg1Src", "Arg1Type", "Arg1Pol", "Arg1Det", "Arg1FeatSpanList",
    "Arg2SpanList", "Arg2Src", "Arg2Type", "Arg2Pol", "Arg2Det", "Arg2FeatSpanList",
    "Sup2SpanList", "AdjuReason", "AdjuDisagr", "PBRole", "PBVerb", "Offset", "Provenance", "Link",
]


def utf16_spans_to_char_spans(spans, text):
    """
    Convert spans in UTF-16 code units to Python char index spans.

    spans: list of (start16, end16) where indices are in UTF-16 code units
           and end16 is exclusive.
    text:  the original Python str (same as doc.text).
    """
    if not spans:
        return []

    # build map from UTF-16 unit index -> char index
    unit_to_char = []
    for ci, ch in enumerate(text):
        units = len(ch.encode("utf-16le")) // 2  # 1 for BMP, 2 for emoji/surrogates
        unit_to_char.extend([ci] * units)

    max_unit = len(unit_to_char)
    out = []
    for s16, e16 in spans:
        if max_unit == 0:
            continue
        # clamp to valid range
        s16 = max(0, min(s16, max_unit - 1))
        e16 = max(0, min(e16, max_unit))

        # PDTB-style spans are half-open [s16, e16)
        start_char = unit_to_char[s16]
        end_char   = unit_to_char[e16 - 1] + 1  # convert last code unit to end-char+1

        out.append((start_char, end_char))

    return out


def get_spans(span_str: str):
    """ Parse PDTB-style span list string into list of (start, end) tuples. """
    if not span_str:
        return []

    return [tuple(map(int, span.split(".."))) for span in span_str.strip(";").split(";") if span]


def tokens_for(spans, tokens):
    """ Get tokens that overlap with any of the provided spans. """
    out = []
    for t in tokens:
        for s, e in spans:
            if (s <= t.offset_begin < e) or (s < t.offset_end <= e) or (t.offset_begin <= s and t.offset_end >= e):
                out.append(t)
                break

    return out


def tokenize(raw: Path, out_path: Path):
    """ Tokenize raw file with `discopy-tokenize` and write to out_path. """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["discopy-tokenize", "-i", str(raw), "-o", str(out_path)], check=True)


def build_relations(doc, ann_path: Path):
    tokens = doc.get_tokens()
    text = doc.text
    relations = []
    lines = [ln for ln in ann_path.read_text().splitlines() if ln.strip()]
    for line in lines:
        rel = dict(zip(FIELDS, line.split("|")))

        arg1_spans16 = get_spans(rel["Arg1SpanList"])
        arg2_spans16 = get_spans(rel["Arg2SpanList"])
        conn_spans16 = get_spans(rel["ConnSpanList"])

        # convert UTF-16 unit spans -> Python char spans
        arg1_spans = utf16_spans_to_char_spans(arg1_spans16, text)
        arg2_spans = utf16_spans_to_char_spans(arg2_spans16, text)
        conn_spans = utf16_spans_to_char_spans(conn_spans16, text)

        arg1 = tokens_for(arg1_spans, tokens)
        arg2 = tokens_for(arg2_spans, tokens)
        conn = tokens_for(conn_spans, tokens)

        senses = [rel["SClass1A"]] + ([rel["SClass1B"]] if rel["SClass1B"] else [])
        relations.append(Relation(arg1, arg2, conn, senses, rel["Relation"]))

    return relations


def find_one(pattern: str):
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No match for pattern: {pattern}")
    if len(matches) > 1:
        raise FileExistsError(f"Multiple matches for pattern: {pattern}")

    return Path(matches[0])


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True, help="Space-separated list of doc IDs (e.g., '085 101 ...').")
    ap.add_argument("--raw-dir", type=Path, required=True, help="Dir containing raw files.")
    ap.add_argument("--ann-dir", type=Path, required=True, help="Dir containing ann files.")
    ap.add_argument("--gold-out", type=Path, required=True, help="Output gold JSONL path (combined).")
    ap.add_argument("--pred-in", type=Path, help="Optional parser-input JSONL path (combined).")
    ap.add_argument("--tmp-dir", type=Path, default=Path("data/twiconv/tmp"), help="Temp dir for tokenized files.")

    return ap.parse_args()


def main():
    args = parse_args()
    ids = args.ids.split()
    args.tmp_dir.mkdir(parents=True, exist_ok=True)
    args.gold_out.parent.mkdir(parents=True, exist_ok=True)
    if args.pred_in:
        args.pred_in.parent.mkdir(parents=True, exist_ok=True)

    with open(args.gold_out, "w") as gold_f, open(args.pred_in, "w") if args.pred_in else nullcontext() as pred_f:
        for doc_id in ids:
            raw_path = find_one(str(args.raw_dir / f"{doc_id}_*.txt.username_text_tabseparated"))
            ann_path = find_one(str(args.ann_dir / f"{doc_id}_*.txt.username_text_tabseparated"))

            tok_path = args.tmp_dir / f"{doc_id}.tokenized.jsonl"
            tokenize(raw_path, tok_path)
            doc = load_documents(open(tok_path))[0]
            doc.doc_id = raw_path.name.split(".txt", 1)[0]

            relations = build_relations(doc, ann_path)
            out_doc = doc.with_relations(relations)
            gold_f.write(json.dumps(out_doc.to_json()) + "\n")

            if pred_f:
                pred_doc = doc.with_relations([])
                pred_f.write(json.dumps(pred_doc.to_json()) + "\n")

            print(f"Processed {doc_id}")

    print(f"Wrote gold to {args.gold_out}")
    if args.pred_in:
        print(f"Wrote parser input to {args.pred_in}")


class nullcontext:
    """Minimal no-op context manager."""

    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


if __name__ == "__main__":
    main()
