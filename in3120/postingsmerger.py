# pylint: disable=missing-module-docstring

from typing import Iterator
from .posting import Posting

def next_or(iterable, default):
    try:
        return next(iterable)
    except StopIteration:
        return default


class PostingsMerger:
    """
    Utility class for merging posting lists.

    It is currently left unspecified what to do with the term frequency field
    in the returned postings when document identifiers overlap. Different
    approaches are possible, e.g., an arbitrary one of the two postings could
    be returned, or the posting having the smallest/largest term frequency, or
    a new one that produces an averaged value, or something else.
    """

    @staticmethod
    def intersection(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple AND(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        p1 = next_or(iter1, None)
        p2 = next_or(iter2, None)
        while p1 is not None and p2 is not None:
            if p1.document_id == p2.document_id:
                yield p1
                p1 = next_or(iter1, None)
                p2 = next_or(iter2, None)
            elif p1.document_id < p2.document_id:
                p1 = next_or(iter1, None)
            else:
                p2 = next_or(iter2, None)



    @staticmethod
    def union(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple OR(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        p1 = next_or(iter1, None)
        p2 = next_or(iter2, None)
        while p1 is not None and p2 is not None:
            if p1.document_id == p2.document_id:
                yield p1
                p1 = next_or(iter1, None)
                p2 = next_or(iter2, None)
            elif p1.document_id < p2.document_id:
                yield p1
                p1 = next_or(iter1, None)
            else:
                yield p2
                p2 = next_or(iter2, None)
        if p1 is None and p2 is None:
            pass
        elif p1 is None:
            # type checker is too dumb to know p2 can never be None at this
            # point, but we are MASSIVE HUGE 🧠 here so we know better
            yield p2  # pyright: ignore[reportReturnType]
            yield from iter2
        elif p2 is None:
            yield p1
            yield from iter1
        else:
            raise RuntimeError("wtf this shouldn't happen??!??!! HUH?")

    @staticmethod
    def difference(iter1: Iterator[Posting], iter2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple ANDNOT(A, B) of two posting
        lists A and B, given iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        p1 = next_or(iter1, None)
        p2 = next_or(iter2, None)

        while p1 is not None and p2 is not None:
            if p1.document_id == p2.document_id:
                p1 = next_or(iter1, None)
                p2 = next_or(iter2, None)

            elif p1.document_id < p2.document_id:
                yield p1
                p1 = next_or(iter1, None)
            else:
                p2 = next_or(iter2, None)

        if p1 is not None:
            yield p1
            yield from iter1
