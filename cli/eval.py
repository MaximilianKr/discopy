import bz2
import sys

import click

from discopy.evaluate.conll import evaluate_docs, print_results
from discopy.evaluate.utils import normalize_senses, truncate_senses
from discopy.utils import init_logger
from discopy_data.data.loaders.conll import load_parsed_conll_dataset
from discopy_data.data.loaders.json import load_documents


logger = init_logger()


def get_fh(path):
    if path.endswith(('json', 'jsonl')):
        return open(path)
    elif path.endswith('bz2'):
        return bz2.open(path, 'rt')
    elif path == '-':
        return sys.stdin
    else:
        raise ValueError('Unknown data ending')


@click.command()
@click.argument('conll-path', type=click.Path())
@click.argument('pred-path', type=click.Path())
@click.option('-t', '--threshold', default=0.9, type=float)
@click.option('--simple-connectives', is_flag=True)  # false by default
@click.option('--sense-level', default=2, type=int)
@click.option('--legacy', is_flag=True)  # false by default
def main(conll_path, pred_path, threshold, simple_connectives, sense_level, legacy):
    gold_docs = load_parsed_conll_dataset(conll_path, simple_connectives=simple_connectives, sense_level=sense_level)
    pred_docs = load_documents(get_fh(pred_path))

    if not legacy:
        gold_docs = normalize_senses(gold_docs)  # only for implicit relations
        pred_docs = normalize_senses(pred_docs)  # only for implicit relations
        gold_docs = truncate_senses(gold_docs, sense_level)
        pred_docs = truncate_senses(pred_docs, sense_level)

    pred_doc_ids = {doc.doc_id for doc in pred_docs}
    gold_docs = [doc for doc in gold_docs if doc.doc_id in pred_doc_ids]
    
    if not pred_docs or not gold_docs:
        logger.warning('No documents found')
        return
    
    print_results(
        evaluate_docs(
            [doc.with_relations([r for r in doc.relations if r.is_explicit()]) for doc in gold_docs],
            [doc.with_relations([r for r in doc.relations if r.is_explicit()]) for doc in pred_docs],
            threshold=threshold,
            legacy=legacy
        ), 
        title='EXPLICIT'
    )
    
    print_results(
        evaluate_docs(
            [doc.with_relations([r for r in doc.relations if not r.is_explicit()]) for doc in gold_docs],
            [doc.with_relations([r for r in doc.relations if not r.is_explicit()]) for doc in pred_docs],
            threshold=threshold,
            legacy=legacy
        ),
        title='NON-EXPLICIT'
    )
    
    print_results(
        evaluate_docs(
            gold_docs, pred_docs, threshold=threshold, legacy=legacy
        ),
        title='ALL'
    )


if __name__ == '__main__':
    main()
