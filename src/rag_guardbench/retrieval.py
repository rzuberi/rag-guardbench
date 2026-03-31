from __future__ import annotations

import math
import re
from collections import Counter

from rag_guardbench.schemas import Chunk, Document


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def chunk_document(document: Document) -> list[Chunk]:
    paragraphs = [part.strip() for part in document.text.split("\n\n") if part.strip()]
    chunks: list[Chunk] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}::chunk{index}",
                doc_id=document.doc_id,
                title=document.title,
                topic=document.topic,
                kind=document.kind,
                text=paragraph,
            )
        )
    return chunks


class TfidfRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self.chunks = [chunk for document in documents for chunk in chunk_document(document)]
        self.df: Counter[str] = Counter()
        self.chunk_term_counts: dict[str, Counter[str]] = {}
        self.chunk_norms: dict[str, float] = {}
        for chunk in self.chunks:
            counts = Counter(tokenize(chunk.text + " " + chunk.title))
            self.chunk_term_counts[chunk.chunk_id] = counts
            for token in counts:
                self.df[token] += 1
        self.total_chunks = max(len(self.chunks), 1)
        self.idf = {
            token: math.log((1 + self.total_chunks) / (1 + count)) + 1.0
            for token, count in self.df.items()
        }
        for chunk in self.chunks:
            vector = self._weighted_counts(self.chunk_term_counts[chunk.chunk_id])
            self.chunk_norms[chunk.chunk_id] = math.sqrt(sum(value * value for value in vector.values())) or 1.0

    def _weighted_counts(self, counts: Counter[str]) -> dict[str, float]:
        return {token: float(freq) * self.idf.get(token, 1.0) for token, freq in counts.items()}

    def retrieve(self, query: str, top_k: int = 4) -> list[Chunk]:
        query_counts = Counter(tokenize(query))
        query_vector = self._weighted_counts(query_counts)
        query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0
        scored: list[Chunk] = []
        for chunk in self.chunks:
            dot = 0.0
            chunk_vector = self._weighted_counts(self.chunk_term_counts[chunk.chunk_id])
            for token, q_value in query_vector.items():
                dot += q_value * chunk_vector.get(token, 0.0)
            score = dot / (query_norm * self.chunk_norms[chunk.chunk_id])
            scored.append(
                Chunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    topic=chunk.topic,
                    kind=chunk.kind,
                    text=chunk.text,
                    score=round(score, 6),
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

