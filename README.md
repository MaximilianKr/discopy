# Shallow Discourse Parser

**Note:** this project is a (*work in progress*) fork of the [original discopy](https://github.com/rknaebel/discopy) parser by René Knaebel with the aim of modernizing some parts.

This project aims to provide an implementation of the standard Lin et al. architecture as well as recent advances in neural architectures.
It consists of a parser pipeline architecture which stacks individual parser components to continuously add discourse information.
The focus is currently on explicit relations that were handled first in most pipelines.
Further, remaining sentence pairs without explicit sense relation are processed with the non-explicit component.
The current implementation is following the Conll2016 implementation guidelines.
It accepts PDTB2 CoNLL format as input for training and evaluation and mainly produces a line-based json document format.

The parser was presented at the CODI 2021 Workshop. For more information, checkout the paper
[discopy: A Neural System for Shallow Discourse Parsing](https://aclanthology.org/2021.codi-main.12/).

## Setup

<details>
  <summary>Click to expand/collapse</summary>

```bash
git clone https://github.com/MaximilianKr/discopy.git
cd discopy
```

The parser relies on Python 3.8, which you can set up locally for this repo using [pyenv](https://github.com/pyenv/pyenv).

```bash
curl -fsSL https://pyenv.run | bash
pyenv install 3.8.18
# set default Python interpreter for the local repo
pyenv local 3.8.18
```

### Setup Virtual Environment

Recommended: use [uv package manager](https://docs.astral.sh/uv/)
This will use the previously set up Python 3.8 interpreter.

From root:

```bash
uv venv --python 3.8
source .venv/bin/activate
```

```bash
uv pip install --upgrade pip
uv pip install -e .
```

</details>

## Usage

*Discopy* currently supports different modes and distinguishes standard feature-based models and neural-based (transformer) models.
These example commands are executed from within the repository folder.

**Note:** The standard feature-based pipeline has *not* been updated yet, current focus is on modernizing the neural-based pipeline.

### Evaluation

```bash
discopy-eval path/to/conll-gold path/to/prediction
```

### Standard Architecture

<details>
  <summary>Click to expand/collapse</summary>

#### Training (Standard)

```bash
discopy-train lin path/to/model path/to/conll
```

Training data format is json, the folder contains subfolders `en.{train,dev,test}` with files `relations.json` and `parses.json`.

#### Standard (Standard)

```bash
discopy-predict lin path/to/conll/en.part path/to/model/lin
```

```bash
discopy-parse lin path/to/model/lin -i path/to/some/documents.json
```

```bash
discopy-tokenize -i path/to/textfile | discopy-add-parses -c | discopy-parse lin models/lin
```

</details>

### Neural Architecture

<details>
  <summary>Click to expand/collapse</summary>

Neural components are a little bit more complex and ofter require/allow for more hyper-parameters while designing the component and throughout the training process.
The training cli gives only a single component-parameter choice.
For individual adaptions, one has to write its own training script.
The `bert-model` parameter corresponds to the huggingface transformers model names.

#### Training (Neural)

```bash
discopy-nn-train [BERT-MODEL] [MODEL-PATH] [CONLL-PATH]
```

Training data format follows the one above.

#### Prediction (Neural)

```bash
discopy-nn-predict [BERT-MODEL] [MODEL-PATH] [CONLL-PATH]
```

```bash
discopy-nn-parse [BERT-MODEL] [MODEL-PATH] -i [JSON-INPUT]
```

```bash
cat path/to/textfile | discopy-nn-parse [BERT-MODEL] [MODEL-PATH]
```

```bash
discopy-tokenize --tokenize-only -i path/to/textfile | discopy-nn-parse bert-base-cased models/pipeline-bert-2
```

</details>

[Back to Top](#shallow-discourse-parser)
