# Inference from Plain Text with Neural Pipeline

This walkthrough shows how to run *discopy*'s neural pipeline from plain text using the [pretrained CODI release models](https://github.com/rknaebel/discopy/releases).

It assumes you have followed the setup instructions in the [README#Setup](../README.md#setup).

## Download Model(s)

<details>
  <summary>Click to expand/collapse</summary>

Download one of the available pretrained models from the [CODI Release](https://github.com/rknaebel/discopy/releases) and unpack it to `models/`.

Available model types:

- `albert-base-v2`
- `bert-base-cased`
- `roberta-base`
- `xlnet-base-cased`

For example, using the `bert-base-cased` model, run from the repository root:

```bash
mkdir -p models/bert-base-cased
curl -L \
  "https://github.com/rknaebel/discopy/releases/download/1.1.0/bert-10.11.21-13.31.tar.gz" \
  | tar -xz -C models/bert-base-cased
```

</details>

## Prepare Raw Text

Create one or more UTF-8 text files. Alternatively, use the sample `txt` files in [data/test_raw](../data/test_raw/).

## Tokenize to JSONL

`discopy-tokenize` converts plain text into `Document` objects with `trankit` tokenization / POS / dependencies.

- Single file:

  ```bash
  discopy-tokenize -i data/test_raw/doc1.txt -o data/doc1.jsonl
  ```

- Multiple files:

  ```bash
  cat data/test_raw/*.txt | discopy-tokenize -o data/raw_docs.jsonl
  ```

Each document becomes one JSON line containing sentences, tokens, and metadata.

### Optional: Refine Parses with Supar

<details>
  <summary>Click to expand/collapse</summary>

You can enrich the JSONL with high-quality dependency/constituency parses before parsing:

```bash
discopy-add-parses -s data/doc1.jsonl -o data/doc1.supar.jsonl --dependencies --constituents
```

Feed `data/raw_docs.supar.jsonl` into `discopy-nn-parse` when you need supar parses instead of the default trankit ones.

</details>

## Parse with Pretrained Model

Run the neural parser (replace `bert-base-cased` and the model path with the release you downloaded).

- Single JSONL:

  ```bash
  discopy-nn-parse bert-base-cased models/bert-base-cased \
    -i data/doc1.jsonl -o data/doc1.out.jsonl
  # or if you added optional supar parses
  discopy-nn-parse bert-base-cased models/bert-base-cased \
    -i data/doc1.supar.jsonl -o data/doc1.supar.out.jsonl
  ```

- Multiple files / batch:

  ```bash
  discopy-nn-parse bert-base-cased models/bert-base-cased \
    -i data/raw_docs.jsonl -o data/raw_docs.out.jsonl
  ```

The output JSONL mirrors the input documents but adds predicted `relations` entries (Arg1/Arg2 spans, senses, types).
