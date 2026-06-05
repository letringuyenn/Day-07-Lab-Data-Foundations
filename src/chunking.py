from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Split text into fixed-size character windows with optional overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        step = self.chunk_size - self.overlap
        chunks: list[str] = []

        for start in range(0, len(text), step):
            chunks.append(text[start : start + self.chunk_size])
            if start + self.chunk_size >= len(text):
                break

        return chunks


class SentenceChunker:
    """Split text on sentence boundaries and group adjacent sentences."""

    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:[ \t]+|\r?\n+)")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        if max_sentences_per_chunk <= 0:
            raise ValueError("max_sentences_per_chunk must be greater than 0")
        self.max_sentences_per_chunk = max_sentences_per_chunk

    def chunk(self, text: str) -> list[str]:
        stripped_text = text.strip()
        if not stripped_text:
            return []

        sentences = [
            sentence.strip()
            for sentence in self.SENTENCE_BOUNDARY.split(stripped_text)
            if sentence.strip()
        ]

        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using separators in priority order."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        self.separators = (
            list(self.DEFAULT_SEPARATORS) if separators is None else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return FixedSizeChunker(self.chunk_size, overlap=0).chunk(current_text)

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return FixedSizeChunker(self.chunk_size, overlap=0).chunk(current_text)

        if separator not in current_text:
            return self._split(current_text, next_separators)

        pieces = current_text.split(separator)
        chunks: list[str] = []
        current_parts: list[str] = []
        current_length = 0

        for piece in pieces:
            if not piece:
                continue

            added_length = len(piece) + (len(separator) if current_parts else 0)
            if current_parts and current_length + added_length > self.chunk_size:
                chunks.extend(
                    self._split(separator.join(current_parts), next_separators)
                )
                current_parts = []
                current_length = 0

            if len(piece) > self.chunk_size:
                chunks.extend(self._split(piece, next_separators))
            else:
                current_parts.append(piece)
                current_length += len(piece) + (
                    len(separator) if len(current_parts) > 1 else 0
                )

        if current_parts:
            chunks.extend(self._split(separator.join(current_parts), next_separators))

        return [chunk for chunk in chunks if chunk]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same length")
    if not vec_a:
        return 0.0

    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run the built-in chunking strategies and summarize their outputs."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0
                ),
                "chunks": chunks,
            }

        return comparison
