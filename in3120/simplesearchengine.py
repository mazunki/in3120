# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals

from collections import Counter
from typing import Any, Dict, Iterator, List, Set

from .corpus import Corpus
from .invertedindex import InvertedIndex
from .ranker import Ranker
from .sieve import Sieve


class SimpleSearchEngine:
    """
    Realizes a simple query evaluator that efficiently performs N-of-M matching over an inverted index.
    I.e., if the query contains M unique query terms, each document in the result set should contain at
    least N of these m terms. For example, 2-of-3 matching over the query 'orange apple banana' would be
    logically equivalent to the following predicate:

       (orange AND apple) OR (orange AND banana) OR (apple AND banana)
       
    Note that N-of-M matching can be viewed as a type of "soft AND" evaluation, where the degree of match
    can be smoothly controlled to mimic either an OR evaluation (1-of-M), or an AND evaluation (M-of-M),
    or something in between.

    The evaluator uses the client-supplied ratio T = N/M as a parameter as specified by the client on a
    per query basis. For example, for the query 'john paul george ringo' we have M = 4 and a specified
    threshold of T = 0.7 would imply that at least 3 of the 4 query terms have to be present in a matching
    document.
    """

    def __init__(self, corpus: Corpus, inverted_index: InvertedIndex):
        self.__corpus = corpus
        self.__inverted_index = inverted_index

    def evaluate(self, query: str, options: Dict[str, Any], ranker: Ranker) -> Iterator[Dict[str, Any]]:
        """
        Evaluates the given query, doing N-out-of-M ranked retrieval. I.e., for a supplied query having M
        unique terms, a document is considered to be a match if it contains at least N <= M of those terms.

        The matching documents, if any, are ranked by the supplied ranker, and only the "best" matches are yielded
        back to the client as dictionaries having the keys "score" (float) and "document" (Document).

        The client can supply a dictionary of options that controls the query evaluation process: The value of
        N is inferred from the query via the "match_threshold" (float) option, and the maximum number of documents
        to return to the client is controlled via the "hit_count" (int) option.
        """

        multiplicites: Counter[str] = Counter(self.__inverted_index.get_terms(query))
        terms: List[str] = list(multiplicites.keys())

        threshold: float = options.get("match_threshold", 1.0)  # defaults to only accepting perfect matches

        m: int = len(terms)
        n: int = max(1, min(m, int(threshold*m)))
        if options.get("debug", False):
            print(f"Checking {terms} with {n=}÷{m=}")

        max_documents: int = options.get("hit_count", 10)
        sieve = Sieve(max_documents)

        inverted_index = [self.__inverted_index.get_postings_iterator(term) for term in terms]
        postings = [next(p, None) for p in inverted_index]

        n_of_m = Counter()
        while any(postings):
            doc_id = min(p.document_id for p in postings if p is not None)

            for i, p in enumerate(postings):
                if p is not None and p.document_id == doc_id:
                    n_of_m[doc_id] += 1

            if n_of_m[doc_id] >= n:
                ranker.reset(doc_id)

                for term, posting in zip(terms, postings):
                    if posting and posting.document_id == doc_id:
                        ranker.update(term, multiplicites[term], posting)

                sieve.sift(ranker.evaluate(), doc_id)

            for i, p in enumerate(postings):
                if p is not None and p.document_id == doc_id:
                    postings[i] = next(inverted_index[i], None)

        for score, doc_id in sieve.winners():
            yield {'document': self.__corpus.get_document(doc_id), 'score': score}



