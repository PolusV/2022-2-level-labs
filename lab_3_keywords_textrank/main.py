"""
Lab 3
Extract keywords based on TextRank algorithm
"""
from pathlib import Path
from typing import Optional, Union
from lab_2_keywords_cooccurrence.main import type_check

import csv

from lab_1_keywords_tfidf.main import (
    calculate_frequencies,
    calculate_tf,
    calculate_tfidf
)

from lab_2_keywords_cooccurrence.main import (
    extract_phrases,
    extract_candidate_keyword_phrases,
    calculate_frequencies_for_content_words,
    calculate_word_degrees,
    calculate_word_scores,
)


class TextPreprocessor:
    """
    A class to preprocess raw text
    ...
    Attributes
    ----------
    _stop_words: tuple[str, ...]
        insignificant words to remove from tokens
    _punctuation: tuple[str, ...]
        punctuation symbols to remove during text cleaning
    Methods
    -------
    _clean_and_tokenize(text: str) -> tuple[str, ...]:
        Removes punctuation, casts to lowercase, splits into tokens.
    _remove_stop_words(tokens: tuple[str, ...] -> tuple[str, ...]:
        Filters tokens, removing stop words
    preprocess_text(text: str) -> tuple[str, ...]:
        Produces filtered clean lowercase tokens from raw text
    """
    # Step 1.1
    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...]) -> None:
        """
        Constructs all the necessary attributes for the text preprocessor object
        Parameters
        ----------
            stop_words : tuple[str, ...]
                insignificant words to remove from tokens
            punctuation : tuple[str, ...]
                punctuation symbols to remove during text cleaning
        """
        self._stop_words = stop_words
        self._punctuation = punctuation

    # Step 1.2
    def _clean_and_tokenize(self, text: str) -> tuple[str, ...]:
        """
        Removes punctuation, casts to lowercase, splits into tokens.
        Parameters
        ----------
            text : str
                raw text
        Returns
        -------
            tuple[str, ...]
                clean lowercase tokens
        """
        if self._punctuation:
            for punc in self._punctuation:
                text = text.replace(punc, '')
        return tuple(text.lower().split())

    # Step 1.3
    def _remove_stop_words(self, tokens: tuple[str, ...]) -> tuple[str, ...]:
        """
        Filters tokens, removing stop words
        Parameters
        ----------
            tokens : tuple[str, ...]
                tokens containing stop-words
        Returns
        -------
            tuple[str, ...]
                tokens without stop-words
        """
        return tuple(token for token in tokens if token not in self._stop_words)

    # Step 1.4
    def preprocess_text(self, text: str) -> tuple[str, ...]:
        """
        Produces filtered clean lowercase tokens from raw text
        Parameters
        ----------
            text : str
                raw text
        Returns
        -------
            tuple[str, ...]
                clean lowercase tokens with no stop-words
        """
        return self._remove_stop_words(self._clean_and_tokenize(text))


class TextEncoder:
    """
    A class to encode string sequence into matching integer sequence
    ...
    Attributes
    ----------
    _word2id: dict[str, int]
        maps words to integers
    _id2word: dict[int, str]
        maps integers to words
    Methods
    -------
     _learn_indices(self, tokens: tuple[str, ...]) -> None:
        Fills attributes mapping words and integer equivalents to each other
    encode(self, tokens: tuple[str, ...]) -> Optional[tuple[int, ...]]:
        Encodes input sequence of string tokens to sequence of integer tokens
    decode(self, encoded_tokens: tuple[int, ...]) -> Optional[tuple[str, ...]]:
        Decodes input sequence of integer tokens to sequence of string tokens
    """

    # Step 2.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the text encoder object
        """
        self._word2id = {}
        self._id2word = {}

    # Step 2.2
    def _learn_indices(self, tokens: tuple[str, ...]) -> None:
        """
        Fills attributes mapping words and integer equivalents to each other
        Parameters
        ----------
            tokens : tuple[str, ...]
                sequence of string tokens
        """
        for token, idx in zip(tokens, range(1001 + len(tokens), 1001, -1)):
            self._word2id[token] = idx

        for token, idx in self._word2id.items():
            self._id2word[idx] = token

    # Step 2.3
    def encode(self, tokens: tuple[str, ...]) -> Optional[tuple[int, ...]]:
        """
        Encodes input sequence of string tokens to sequence of integer tokens
        Parameters
        ----------
            tokens : tuple[str, ...]
                sequence of string tokens
        Returns
        -------
            tuple[int, ...]
                sequence of integer tokens
        In case of empty tokens input data, None is returned
        """
        if not tokens:
            return None
        self._learn_indices(tokens)
        return tuple(self._word2id[token] for token in tokens)

    # Step 2.4
    def decode(self, encoded_tokens: tuple[int, ...]) -> Optional[tuple[str, ...]]:
        """
        Decodes input sequence of integer tokens to sequence of string tokens
        Parameters
        ----------
            encoded_tokens : tuple[int, ...]
                sequence of integer tokens
        Returns
        -------
            tuple[str, ...]
                sequence of string tokens
        In case of out-of-dictionary input data, None is returned
        """
        if not (encoded_tokens and all(encoded_token in self._id2word for encoded_token in encoded_tokens)):
            return None
        return tuple(self._id2word[encoded_token] for encoded_token in encoded_tokens)


# Step 3
def extract_pairs(tokens: tuple[int, ...], window_length: int) -> Optional[tuple[tuple[int, ...], ...]]:
    """
    Retrieves all pairs of co-occurring words in the token sequence
    Parameters
    ----------
        tokens : tuple[int, ...]
            sequence of tokens
        window_length: int
            maximum distance between co-occurring tokens: tokens are considered co-occurring
            if they appear in the same window of this length
    Returns
    -------
        tuple[tuple[int, ...], ...]
            pairs of co-occurring tokens
    In case of corrupt input data, None is returned:
    tokens must not be empty, window lengths must be integer, window lengths cannot be less than 2.
    """
    if not(isinstance(window_length, int) and window_length >= 2 and tokens):
        return None
    pairs = []
    for idx1, token1 in enumerate(tokens):
        for token2 in tokens[idx1 + 1:idx1 + window_length]:
            if token1 != token2:
                pairs.append((token1, token2))
    return tuple(pairs)


class AdjacencyMatrixGraph:
    """
    A class to represent graph as matrix of adjacency
    ...
    Attributes
    ----------
    _matrix: list[list[int]]
        stores information about vertices interrelation
    _positions: dict[int, list[int]]
        stores information about positions in text
    Methods
    -------
     get_vertices(self) -> tuple[int, ...]:
        Returns a sequence of all vertices present in the graph
     add_edge(self, vertex1: int, vertex2: int) -> int:
        Adds or overwrites an edge in the graph between the specified vertices
     is_incidental(self, vertex1: int, vertex2: int) -> int:
        Retrieves information about whether the two vertices are incidental
     calculate_inout_score(self, vertex: int) -> int:
        Retrieves a number of incidental vertices to a specified vertex
    fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        Updates graph instance with vertices and edges extracted from tokenized text
    fill_positions(self, tokens: tuple[int, ...]) -> None:
        Saves information on all positions of each vertex in the token sequence
    calculate_position_weights(self) -> None:
        Computes position weights for all tokens in text
    get_position_weights(self) -> dict[int, float]:
        Retrieves position weights for all vertices in the graph
    """

    _matrix: list[list[int]]
    _positions: dict[int, list[int]]
    _position_weights: dict[int, float]

    # Step 4.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the adjacency matrix graph object
        """
        self._matrix = []
        self._vertices = []
        self._positions = {}
        self._position_weights = {}

    # Step 4.2
    def add_edge(self, vertex1: int, vertex2: int) -> int:
        """
        Adds or overwrites an edge in the graph between the specified vertices
        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the added edge
            vertex2 : int
                the second vertex incidental to the added edge
        Returns
        -------
            int
                0 if edge was added successfully, otherwise -1
        In case of vertex1 being equal to vertex2, -1 is returned as loops are prohibited
        """
        if vertex1 == vertex2:
            return -1
        for vertex in vertex1, vertex2:
            if vertex not in self._vertices:
                self._vertices.append(vertex)
                self._matrix.append([])

        for edges_list in self._matrix:
            if len(edges_list) < len(self._vertices):
                edges_list.extend([0 for _ in range(len(self._vertices) - len(edges_list))])

        idx1 = self._vertices.index(vertex1)
        idx2 = self._vertices.index(vertex2)
        self._matrix[idx1][idx2] = 1
        self._matrix[idx2][idx1] = 1
        return 0

    # Step 4.3
    def is_incidental(self, vertex1: int, vertex2: int) -> int:
        """
        Retrieves information about whether the two vertices are incidental
        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the edge sought
            vertex2 : int
                the second vertex incidental to the edge sought
        Returns
        -------
            Optional[int]
                1 if vertices are incidental, otherwise 0
        If either of vertices is not present in the graph, -1 is returned
        """
        if vertex1 not in self._vertices or vertex2 not in self._vertices:
            return -1
        idx1 = self._vertices.index(vertex1)
        idx2 = self._vertices.index(vertex2)
        return self._matrix[idx1][idx2]

    # Step 4.4
    def get_vertices(self) -> tuple[int, ...]:
        """
        Returns a sequence of all vertices present in the graph
        Returns
        -------
            tuple[int, ...]
                a sequence of vertices present in the graph
        """
        return tuple(self._vertices)

    # Step 4.5
    def calculate_inout_score(self, vertex: int) -> int:
        """
        Retrieves a number of incidental vertices to a specified vertex
        Parameters
        ----------
            vertex : int
                a vertex to calculate inout score for
        Returns
        -------
            int
                number of incidental vertices
        If vertex is not present in the graph, -1 is returned
        """
        if vertex not in self._vertices:
            return -1
        idx = self._vertices.index(vertex)
        return sum(self._matrix[idx])

    # Step 4.6
    def fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        """
        Updates graph instance with vertices and edges extracted from tokenized text
        Parameters
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
            window_length: int
                maximum distance between co-occurring tokens: tokens are considered co-occurring
                if they appear in the same window of this length
        """
        for pair in extract_pairs(tokens, window_length):
            self.add_edge(*pair)

    # Step 8.2
    def fill_positions(self, tokens: tuple[int, ...]) -> None:
        """
        Saves information about all positions of each vertex in the token sequence
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
        """
        for idx, token in enumerate(tokens):
            if token not in self._positions:
                self._positions[token] = []
            self._positions[token].append(idx + 1)

    # Step 8.3
    def calculate_position_weights(self) -> None:
        """
        Computes position weights for all tokens in text
        """
        non_norm_total_weight = 0.0
        for vertex in self._positions:
            for position in self._positions[vertex]:
                self._position_weights[vertex] = self._position_weights.get(vertex, 0.0) + 1 / position
            non_norm_total_weight += self._position_weights[vertex]

        for vertex in self._position_weights:
            self._position_weights[vertex] = self._position_weights.get(vertex, 0.0) / non_norm_total_weight

    # Step 8.4
    def get_position_weights(self) -> dict[int, float]:
        """
        Retrieves position weights for all vertices in the graph
        Returns
        -------
            dict[int, float]
                position weights for all vertices in the graph
        """
        return self._position_weights


class EdgeListGraph:
    """
    A class to represent graph as a list of edges
    ...
    Attributes
    ----------
    _edges: dict[int, list[int]]
        stores information about vertices interrelation
    Methods
    -------
     get_vertices(self) -> tuple[int, ...]:
        Returns a sequence of all vertices present in the graph
     add_edge(self, vertex1: int, vertex2: int) -> int:
        Adds or overwrites an edge in the graph between the specified vertices
     is_incidental(self, vertex1: int, vertex2: int) -> int:
        Retrieves information about whether the two vertices are incidental
     calculate_inout_score(self, vertex: int) -> int:
        Retrieves a number of incidental vertices to a specified vertex
    fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        Updates graph instance with vertices and edges extracted from tokenized text
    fill_positions(self, tokens: tuple[int, ...]) -> None:
        Saves information on all positions of each vertex in the token sequence
    calculate_position_weights(self) -> None:
        Computes position weights for all tokens in text
    get_position_weights(self) -> dict[int, float]:
        Retrieves position weights for all vertices in the graph
    """

    # Step 7.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the edge list graph object
        """
        self._edges = {}
        self._positions = {}
        self._position_weights = {}

    # Step 7.2
    def get_vertices(self) -> tuple[int, ...]:
        """
        Returns a sequence of all vertices present in the graph
        Returns
        -------
            tuple[int, ...]
                a sequence of vertices present in the graph
        """
        return tuple(self._edges.keys())

    # Step 7.2
    def add_edge(self, vertex1: int, vertex2: int) -> int:
        """
        Adds or overwrites an edge in the graph between the specified vertices
        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the added edge
            vertex2 : int
                the second vertex incidental to the added edge
        Returns
        -------
            int
                0 if edge was added successfully, otherwise -1
        In case of vertex1 being equal to vertex2, -1 is returned as loops are prohibited
        """
        if vertex1 == vertex2:
            return -1
        for vertex in vertex1, vertex2:
            if vertex not in self._edges:
                self._edges[vertex] = []

        if vertex1 not in self._edges[vertex2]:
            self._edges[vertex2].append(vertex1)
        if vertex2 not in self._edges[vertex1]:
            self._edges[vertex1].append(vertex2)
        return 0

    # Step 7.2
    def is_incidental(self, vertex1: int, vertex2: int) -> int:
        """
        Retrieves information about whether the two vertices are incidental
        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the edge sought
            vertex2 : int
                the second vertex incidental to the edge sought
        Returns
        -------
            Optional[int]
                1 if vertices are incidental, otherwise 0
        If either of vertices is not present in the graph, -1 is returned
        """
        if vertex1 not in self._edges or vertex2 not in self._edges:
            return -1
        return int(vertex1 in self._edges.get(vertex2, 0))

    # Step 7.2
    def calculate_inout_score(self, vertex: int) -> int:
        """
        Retrieves a number of incidental vertices to a specified vertex
        Parameters
        ----------
            vertex : int
                a vertex to calculate inout score for
        Returns
        -------
            int
                number of incidental vertices
        If vertex is not present in the graph, -1 is returned
        """
        if vertex not in self._edges:
            return -1
        return len(self._edges[vertex])

    # Step 7.2
    def fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        """
        Updates graph instance with vertices and edges extracted from tokenized text
        Parameters
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
            window_length: int
                maximum distance between co-occurring tokens: tokens are considered co-occurring
                if they appear in the same window of this length
        """
        for pair in extract_pairs(tokens, window_length):
            self.add_edge(*pair)

    # Step 8.2
    def fill_positions(self, tokens: tuple[int, ...]) -> None:
        """
        Saves information on all positions of each vertex in the token sequence
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
        """
        for idx, token in enumerate(tokens):
            if token not in self._positions:
                self._positions[token] = []
            self._positions[token] += [idx + 1]

    # Step 8.3
    def calculate_position_weights(self) -> None:
        """
        Computes position weights for all tokens in text
        """
        non_norm_total_weight = 0.0
        for vertex in self._positions:
            for position in self._positions[vertex]:
                self._position_weights[vertex] = self._position_weights.get(vertex, 0) + 1 / position
            non_norm_total_weight += self._position_weights[vertex]

        for vertex in self._position_weights:
            self._position_weights[vertex] = self._position_weights.get(vertex, 0.0) / non_norm_total_weight

    # Step 8.4
    def get_position_weights(self) -> dict[int, float]:
        """
        Retrieves position weights for all vertices in the graph
        Returns
        -------
            dict[int, float]
                position weights for all vertices in the graph
        """
        return self._position_weights


class VanillaTextRank:
    """
    Basic TextRank implementation
    ...
    Attributes
    ----------
    _graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
        a graph representing the text
    _damping_factor: float
         probability of jumping from a given vertex to another random vertex
         in the graph during vertices scores calculation
    _convergence_threshold: float
        maximal acceptable difference between the vertices scores in two consequent iteration
    _max_iter: int
        maximal number of iterations to perform
    _scores: dict[int, float]
        scores of significance for all vertices present in the graph
    Methods
    -------
     update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        Changes vertex significance score using algorithm-specific formula
     score_vertices(self) -> dict[int, float]:
        Iteratively computes significance scores for vertices
     get_scores(self) -> dict[int, float]:
        Retrieves importance scores of all tokens in the encoded text
     get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        Retrieves top n most important tokens in the encoded text
     """

    _scores: dict[int, float]

    # Step 5.1
    def __init__(self, graph: Union[AdjacencyMatrixGraph, EdgeListGraph]) -> None:
        """
        Constructs all the necessary attributes for the text rank algorithm implementation
        Parameters
        ----------
        graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
            a graph representing the text
        """
        self._graph = graph
        self._damping_factor = 0.85
        self._convergence_threshold = 0.0001
        self._max_iter = 50
        self._scores = {}

    # Step 5.2
    def update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        """
        Changes vertex significance score using algorithm-specific formula
        Parameters
        ----------
            vertex : int
                a vertex which significance score is updated
            incidental_vertices: list[int]
                vertices incidental to the scored one
            scores: dict[int, float]
                scores of all vertices in the graph
        """
        summa = sum((1 / self._graph.calculate_inout_score(inc_vertex)) * scores[inc_vertex]
                    for inc_vertex in incidental_vertices)
        self._scores[vertex] = summa * self._damping_factor + (1 - self._damping_factor)
        pass

    # Step 5.3
    def train(self) -> None:
        """
        Iteratively computes significance scores for vertices
        Returns
        -------
            dict[int, float]:
                scores for all vertices present in the graph
        """
        vertices = self._graph.get_vertices()
        for vertex in vertices:
            self._scores[vertex] = 1.0

        for _ in range(0, self._max_iter):
            prev_score = self._scores.copy()
            for scored_vertex in vertices:
                incidental_vertices = [vertex for vertex in vertices
                                       if self._graph.is_incidental(scored_vertex, vertex) == 1]
                self.update_vertex_score(scored_vertex, incidental_vertices, prev_score)
            abs_score_diff = [abs(i - j) for i, j in zip(prev_score.values(), self._scores.values())]
            if sum(abs_score_diff) <= self._convergence_threshold:
                break

    # Step 5.4
    def get_scores(self) -> dict[int, float]:
        """
        Retrieves importance scores of all tokens in the encoded text
        Returns
        -------
            dict[int, float]
                importance scores of all tokens in the encoded text
        """
        return self._scores

    # Step 5.5
    def get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        """
        Retrieves top n most important tokens in the encoded text
        Returns
        -------
            tuple[int, ...]
                top n most important tokens in the encoded text
        """
        srtd_tokens = sorted(self._scores.items(), key=lambda elem: (-elem[1], elem[0]))
        return tuple(elem[0] for elem in srtd_tokens)[:n_keywords]


class PositionBiasedTextRank(VanillaTextRank):
    """
    Advanced TextRank implementation: positions of tokens in text are taken into consideration
    ...
    Attributes
    ----------
    _graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
        a graph representing the text
    _damping_factor: float
         probability of jumping from a given vertex to another random vertex
         in the graph during vertices scores calculation
    _convergence_threshold: float
        maximal acceptable difference between the vertices scores in two consequent iteration
    _max_iter: int
        maximal number of iterations to perform
    _scores: dict[int, float]
        scores of significance for all vertices present in the graph
    _position_weights: dict[int, float]
        position weights for all tokens in the text
    Methods
    -------
     update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        Changes vertex significance score using algorithm-specific formula
     score_vertices(self) -> dict[int, float]:
        Iteratively computes significance scores for vertices
     get_scores(self) -> dict[int, float]:
        Retrieves importance scores of all tokens in the encoded text
     get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        Retrieves top n most important tokens in the encoded text
    """

    # Step 9.1
    def __init__(self, graph: Union[AdjacencyMatrixGraph, EdgeListGraph]) -> None:
        """
        Constructs all the necessary attributes
        for the position-aware text rank algorithm implementation
        Attributes
        ----------
        graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
            a graph representing the text
        """
        super().__init__(graph)
        self._position_weights = graph.get_position_weights()

    # Step 9.2
    def update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        """
        Changes vertex significance score using algorithm-specific formula
        Parameters
        ----------
            vertex : int
                a vertex which significance score is updated
            incidental_vertices: list[int]
                vertices incidental to the scored one
            scores: dict[int, float]
                scores of all vertices in the graph
        """
        summa = sum((1 / self._graph.calculate_inout_score(inc_vertex)) * scores[inc_vertex]
                    for inc_vertex in incidental_vertices)
        self._scores[vertex] = (summa * self._damping_factor +
                                (1 - self._damping_factor) * self._position_weights[vertex])


class TFIDFAdapter:
    """
    A class to unify the interface of TF-IDF keywords extractor with TextRank algorithms
    ...
    Attributes
    ----------
    _tokens: tuple[str, ...]
        sequence of tokens from which to extract keywords
    _idf: dict[str, float]
         Inverse Document Frequency scores for tokens
    _scores: dict[str, float]
        TF-IDF scores reflecting how important each token is
    Methods
    -------
     train(self) -> int:
        Computes importance scores for all tokens
     get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        Retrieves a requested number of the most important tokens
    """

    _scores: dict[str, float]

    # Step 10.1
    def __init__(self, tokens: tuple[str, ...], idf: dict[str, float]) -> None:
        """
        Constructs all the necessary attributes
        for the TF-IDF keywords extractor
        Parameters
        ----------
            tokens: tuple[str, ...]
                sequence of tokens from which to extract keywords
            idf: dict[str, float]
                Inverse Document Frequency scores for tokens
        """
        self._tokens = tokens
        self._idf = idf
        self._scores = {}

    # Step 10.2
    def train(self) -> int:
        """
        Computes importance scores for all tokens
        Returns
        -------
            int:
                0 if importance scores were calculated successfully, otherwise -1
        """
        if not(freq_dict := calculate_frequencies(list(self._tokens))):
            return -1
        if not(tf_dict := calculate_tf(freq_dict)):
            return -1
        if not(tfidf_dict := calculate_tfidf(tf_dict, self._idf)):
            return -1
        self._scores = tfidf_dict
        return 0

    # Step 10.3
    def get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        """
        Retrieves a requested number of the most important tokens
        Parameters
        ----------
            n_keywords: int
                requested number of keywords to extract
        Returns
        -------
            tuple[str, ...]:
                a requested number tokens with the highest importance scores
        """
        srtd_tokens = sorted(self._scores.items(), key=lambda elem: (-elem[1], elem[0]))
        return tuple(elem[0] for elem in srtd_tokens)[:n_keywords]


class RAKEAdapter:
    """
    A class to unify the interface of RAKE keywords extractor with TextRank algorithms
    ...
    Attributes
    ----------
    _text: str
        a text from which to extract keywords
    _stop_words: tuple[str, ...]
         a sequence of stop-words
    _scores: dict[str, float]
        word scores reflecting how important each token is
    Methods
    -------
     train(self) -> int:
        Computes importance scores for all tokens
     get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        Retrieves a requested number of the most important tokens
    """

    _scores: dict[str, float]

    # Step 11.1
    def __init__(self, text: str, stop_words: tuple[str, ...]) -> None:
        """
        Constructs all the necessary attributes
        for the RAKE keywords extractor
        Parameters
        ----------
            text: str
                a text from which to extract keywords
            stop_words: tuple[str, ...]
                a sequence of stop-words
        """
        self._text = text
        self._stop_words = stop_words
        self._scores = {}

    # Step 11.2
    def train(self) -> int:
        """
        Computes importance scores for all tokens
        Returns
        -------
            int:
                0 if importance scores were calculated successfully, otherwise -1
        """
        phrases = extract_phrases(self._text)
        if not phrases:
            return -1
        key_phrases = extract_candidate_keyword_phrases(list(phrases), list(self._stop_words))
        if not key_phrases:
            return -1
        freq_dict = calculate_frequencies_for_content_words(key_phrases)
        if not freq_dict:
            return -1
        degree_dict = calculate_word_degrees(key_phrases, list(freq_dict.keys()))
        if not degree_dict:
            return -1
        score_dict = calculate_word_scores(degree_dict, freq_dict)
        if not score_dict:
            return -1
        self._scores = dict(score_dict)
        return 0

    # Step 11.3
    def get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        """
        Retrieves a requested number of the most important tokens
        Parameters
        ----------
            n_keywords: int
                requested number of keywords to extract
        Returns
        -------
            tuple[str, ...]:
                a requested number tokens with the highest importance scores
        """
        srtd_tokens = sorted(self._scores.items(), key=lambda elem: (-elem[1], elem[0]))
        return tuple(elem[0] for elem in srtd_tokens)[:n_keywords]


# Step 12.1
def calculate_recall(predicted: tuple[str, ...], target: tuple[str, ...]) -> float:
    """
    Computes recall metric
    Parameters
    ----------
        predicted: tuple[str, ...]
            keywords predictions of an algorithm to estimate
        target: tuple[str, ...]
            ground truth keywords
    Returns
    -------
        float:
            recall value
    """
    true_pos = len(set(predicted) & set(target))
    false_neg = len(set(target) - set(predicted))
    return true_pos / (true_pos + false_neg)


class KeywordExtractionBenchmark:
    """
    A class to compare 4 different algorithms of keywords extraction
    ...
    Attributes
    ----------
    _stop_words: tuple[str, ...]
        a sequence of stop-words
    _punctuation: tuple[str, ...]
        symbols of punctuation
    _idf: dict[str, float]
        Inverse Document Frequency scores for the words in materials
    _materials_path: Path
        a path to materials to use for comparison
    themes: tuple[str, ...]
        a sequence of topics to which comparison materials relate
    report: dict[str, dict[str, float]]
        comparison report reflecting how successfully each model extracts keywords
    Methods
    -------
    run(self) -> Optional[dict[str, dict[str, float]]]:
        creates comparison report
    save_to_csv(self, path: Path) -> None:
        saves the report in the .csv format
    """
    # Step 12.2
    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...],
                 idf: dict[str, float], materials_path: Path) -> None:
        """
        Constructs all the necessary attributes for the Benchmark instance
        Parameters
        ----------
            stop_words: tuple[str, ...]
                a sequence of stop-words
            punctuation: tuple[str, ...]
                symbols of punctuation
            idf: dict[str, float]
                Inverse Document Frequency scores for the words in materials
            materials_path: Path
                a path to materials to use for comparison
        """
        self._stop_words = stop_words
        self._punctuation = punctuation
        self._idf = idf
        self._materials_path = materials_path
        self.themes = ('culture', 'business', 'crime', 'fashion', 'health', 'politics', 'science', 'sports', 'tech')
        self.report = {}

    # Step 12.3
    def run(self) -> Optional[dict[str, dict[str, float]]]:
        """
        Creates comparison report
        Returns
        -------
            Optional[dict[str, dict[str, float]]]:
                comparison report
        In case it is impossible to extract keywords due to corrupt inputs, None is returned
        """
        rank_dict = {}
        for theme in self.themes:

            text_path = self._materials_path / f'{self.themes.index(theme)}_text.txt'
            keywords_path = self._materials_path / f'{self.themes.index(theme)}_keywords.txt'

            with (open(text_path, 'r', encoding='utf-8') as text_to_read,
                    open(keywords_path, 'r', encoding='utf-8') as keywords_to_read):
                text = text_to_read.read()
                keywords = tuple(keywords_to_read.read().split('\n'))

                preprocessor = TextPreprocessor(self._stop_words, self._punctuation)
                tokens = preprocessor.preprocess_text(text)
                encoder = TextEncoder()
                encoded_tokens = encoder.encode(tokens)

                graph = EdgeListGraph()
                if encoded_tokens:
                    graph.fill_from_tokens(encoded_tokens, 3)
                    graph.fill_positions(encoded_tokens)
                    graph.calculate_position_weights()

                for algorithm in (VanillaTextRank(graph),
                                  PositionBiasedTextRank(graph),
                                  TFIDFAdapter(tokens, self._idf),
                                  RAKEAdapter(text, self._stop_words)):
                    algorithm.train()
                    top_tokens = algorithm.get_top_keywords(50)
                    if algorithm.__class__.__name__ in ('VanillaTextRank', 'PositionBiasedTextRank'):
                        top_tokens = encoder.decode(top_tokens)
                    score = calculate_recall(top_tokens, keywords)

                    inner_dict = {theme: score}
                    # rank_dict[algorithm.__class__.__name__] = rank_dict.get(algorithm.__class__.__name__, {})
                    if algorithm.__class__.__name__ not in rank_dict:
                        rank_dict[algorithm.__class__.__name__] = {}
                    rank_dict[algorithm.__class__.__name__].update(inner_dict)
        self.report = rank_dict
        return rank_dict

    # Step 12.4
    def save_to_csv(self, path: Path) -> None:
        """
        Saves comparison report to csv
        Parameters
        ----------
            path: Path
                a path where to save the report file
        """
        report_path = path / 'report.csv'
        with open(report_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            headers = 'name', *self.themes
            writer.writerow(headers)
            for algorithm in self.report:
                writer.writerow((algorithm, *self.report[algorithm].values()))
