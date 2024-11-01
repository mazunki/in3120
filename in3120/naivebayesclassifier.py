# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import math
from collections import Counter
from typing import Any, Dict, Iterable, Iterator
from .dictionary import InMemoryDictionary
from .normalizer import Normalizer
from .tokenizer import Tokenizer
from .corpus import Corpus


class NaiveBayesClassifier:
    """
    Defines a multinomial naive Bayes text classifier. For a detailed primer, see
    https://nlp.stanford.edu/IR-book/html/htmledition/naive-bayes-text-classification-1.html.
    """

    def __init__(self, training_set: Dict[str, Corpus], fields: Iterable[str],
                 normalizer: Normalizer, tokenizer: Tokenizer):
        """
        Trains the classifier from the named fields in the documents in the
        given training set.
        """
        # Used for breaking the text up into discrete classification features.
        self.__normalizer = normalizer
        self.__tokenizer = tokenizer

        # The vocabulary we've seen during training.
        self.__vocabulary = InMemoryDictionary()

        # Maps a category c to the logarithm of its prior probability,
        # i.e., c maps to log(Pr(c)).
        self.__priors: Dict[str, float] = {}

        # Maps a category c and a term t to the logarithm of its conditional probability,
        # i.e., (c, t) maps to log(Pr(t | c)).
        self.__conditionals: Dict[str, Dict[str, float]] = {}

        # Maps a category c to the denominator used when doing Laplace smoothing.
        self.__denominators: Dict[str, int] = {}

        # Train the classifier, i.e., estimate all probabilities.
        self.__compute_priors(training_set)
        self.__compute_vocabulary(training_set, fields)
        self.__compute_posteriors(training_set, fields)

    def __compute_priors(self, training_set) -> None:
        """
        Estimates all prior probabilities (log-probabilities) needed for
        the naive Bayes classifier.

            p(lang)
        """
        n_docs = sum(map(len, training_set.values()))

        for meow, corpus in training_set.items():
            weight = len(corpus)
            self.__priors[meow] = math.log(weight / n_docs)


    def __compute_vocabulary(self, training_set, fields) -> None:
        """
        Builds up the overall vocabulary as seen in the training set.
        """
        for corpus in training_set.values():
            for doc in corpus:
                for field in fields:
                    terms = self.__get_terms(doc[field])
                    for term in terms:
                        self.__vocabulary.add_if_absent(term)

    def __compute_posteriors(self, training_set, fields) -> None:
        """
        Estimates all conditional probabilities (log-probabilities) needed for
        the naive Bayes classifier.

            posterior      =   likelyhood   *  prior  / evidence
            p(lang | term) = p(term | lang) * p(lang) / p(term)

            p(term | lang) = count(term in category) + 1 / (count(all terms in category) + len(vocabulary))
        """
        term_freqs_per_meow: Dict[str, Counter[str]] = {}

        for meow, corpus in training_set.items():
            corpus_tfs: Counter[str] = Counter()

            for document in corpus:
                for field in fields:
                    corpus_tfs.update(self.__get_terms(document.get_field(field, "")))

            term_freqs_per_meow[meow] = corpus_tfs
            self.__denominators[meow] = sum(corpus_tfs.values()) + len(self.__vocabulary)

        for meow, term_freqs in term_freqs_per_meow.items():
            self.__conditionals[meow] = {}

            for term, _ in self.__vocabulary:
                weight = term_freqs.get(term, 0) + 1
                fraq = self.__denominators[meow]
                self.__conditionals[meow][term] = math.log(weight/fraq)

    def __get_terms(self, buffer) -> Iterator[str]:
        """
        Processes the given text buffer and returns the sequence of normalized
        terms as they appear. Both the documents in the training set and the buffers
        we classify need to be identically processed.
        """
        tokens = self.__tokenizer.strings(self.__normalizer.canonicalize(buffer))
        return (self.__normalizer.normalize(t) for t in tokens)

    def get_prior(self, category: str) -> float:
        """
        Given a category c, returns the category's prior log-probability log(Pr(c)).

        This is an internal detail having public visibility to facilitate testing.
        """
        return self.__priors[category]

    def get_posterior(self, category: str, term: str) -> float:
        """
        Given a category c and a term t, returns the posterior log-probability log(Pr(t | c)).

        This is an internal detail having public visibility to facilitate testing.
        """
        return self.__conditionals[category].get(term, math.log(1 / (len(self.__vocabulary) + 1)))

    def classify(self, buffer: str) -> Iterator[Dict[str, Any]]:
        """
        Classifies the given buffer according to the multinomial naive Bayes rule. The computed (score, category) pairs
        are emitted back to the client via the supplied callback sorted according to the scores. The reported scores
        are log-probabilities, to minimize numerical underflow issues. Logarithms are base e.

        The results yielded back to the client are dictionaries having the keys "score" (float) and
        "category" (str).
        """
        terms = list(self.__get_terms(buffer))
        scores = {}

        for meow in self.__priors:
            scores[meow] = self.get_prior(meow)

            for term in terms:
                scores[meow] += self.get_posterior(meow, term)

        for meow, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            yield {'category': meow, 'score': score}

    def get_vocabulary(self) -> set:
        return set(term for term, _ in set(self.__vocabulary))
