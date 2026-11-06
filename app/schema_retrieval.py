from __future__ import annotations

import math
import re
from collections import Counter

from .schema_catalog import KEYWORDS, TABLE_DESCRIPTIONS, select_tables

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
ASCII_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    ascii_tokens = ASCII_RE.findall(text)
    cjk_chars = CJK_RE.findall(text)
    bigrams = [cjk_chars[i] + cjk_chars[i + 1] for i in range(len(cjk_chars) - 1)]
    return ascii_tokens + cjk_chars + bigrams


def table_document(table: str, info: dict) -> str:
    parts = [table, TABLE_DESCRIPTIONS.get(table, "")]
    parts.extend(column["name"] for column in info["columns"])
    parts.extend(KEYWORDS.get(table, []))
    return " ".join(parts)


class BM25Retriever:
    def __init__(self, schema: dict[str, dict], k1: float = 1.5, b: float = 0.75):
        self.tables = list(schema)
        self.k1 = k1
        self.b = b
        self.documents = [
            tokenize(table_document(table, schema[table])) for table in self.tables
        ]
        self.doc_lengths = [len(tokens) for tokens in self.documents]
        self.avgdl = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.documents]
        document_frequency: Counter[str] = Counter()
        for tokens in self.documents:
            document_frequency.update(set(tokens))
        total = len(self.documents)
        self.idf = {
            term: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, k: int = 6) -> list[tuple[float, str]]:
        query_tokens = tokenize(query)
        scored: list[tuple[float, str]] = []
        for index, frequencies in enumerate(self.term_frequencies):
            score = 0.0
            for term in query_tokens:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * self.doc_lengths[index] / self.avgdl
                )
                score += (
                    self.idf.get(term, 0.0)
                    * frequency
                    * (self.k1 + 1)
                    / denominator
                )
            if score > 0:
                scored.append((score, self.tables[index]))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[:k]


def build_fk_graph(schema: dict[str, dict]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {table: set() for table in schema}
    for table, info in schema.items():
        for foreign_key in info["foreign_keys"]:
            target = foreign_key["table"]
            if target in graph and target != table:
                graph[table].add(target)
                graph[target].add(table)
    return graph


def _neighbor_priority(table: str) -> tuple[int, str]:
    # Fact tables first: analytical questions often need refunds/order items.
    return (0 if table.startswith("fact_") else 1, table)


def retrieve_tables(
    question: str,
    schema: dict[str, dict],
    top_k: int = 6,
    expand: bool = True,
    retriever: BM25Retriever | None = None,
) -> list[str]:
    retriever = retriever or BM25Retriever(schema)
    hits = retriever.search(question, k=top_k)
    seeds = [table for score, table in hits if score > 0]
    if not seeds:
        return select_tables(question, schema, limit=top_k)

    selected: list[str] = []
    for table in seeds:
        if table not in selected:
            selected.append(table)

    if expand and len(selected) < top_k:
        graph = build_fk_graph(schema)
        changed = True
        while changed and len(selected) < top_k:
            changed = False
            for table in list(selected):
                for neighbor in sorted(graph.get(table, set()), key=_neighbor_priority):
                    if neighbor not in selected and len(selected) < top_k:
                        selected.append(neighbor)
                        changed = True

    return selected[:top_k]
