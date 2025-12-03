"""
Uttility functions for evaluating discourse parsing.
Normalize and truncate senses.
"""

def normalize_senses(docs: list) -> list:
    """
    Normalize implicit relation senses by populating empty sense lists based on
    relation type.

    For each relation in each document, if the 'senses' list is empty, it is
    filled with a default sense derived from the relation's 'type'.

    Args:
        docs (list): List of document objects. Each document must have a
            'relations' attribute containing relation objects. Each relation
            must have 'senses' (list) and 'type' (str) attributes.

    Returns:
        list: The same list of documents with normalized relation senses.
    """
    for d in docs:
        for r in d.relations:
            if not r.senses:
                if r.type == 'EntRel':
                    r.senses = ['EntRel']
                elif r.type:
                    r.senses = [r.type]     # NoRel, Hypophora, etc.
                else:
                    r.senses = ['NoSense']

    return docs


def truncate_senses(docs: list, sense_level: int) -> list:
    """
    Truncate senses to a given PDTB level for all relations in docs.

    Modifies the 'senses' attribute of each relation by truncating sense
    strings to the specified level. Each document must have a 'relations'
    attribute containing relation objects with a 'senses' list.

    Args:
        docs (list): List of document objects. 
        sense_level (int): PDTB sense level to truncate to. Must be -1/1/2/3.
            -1 means no truncation (equivalent to PDTB sense level 3).

    Returns:
        list: The same list of documents with truncated relation senses.
    """
    if sense_level not in [-1, 1, 2, 3]:
        raise ValueError("sense_level must be -1, 1, 2, or 3")
    if sense_level and sense_level > 0:
        for d in docs:
            for r in d.relations:
                r.senses = ['.'.join(s.split('.')[:sense_level]) for s in r.senses]
    
    return docs
