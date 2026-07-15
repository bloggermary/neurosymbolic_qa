"""
Lightweight Retrieval-Augmented Generation service.

Responsibilities:

- Load knowledge documents
- Split documents into chunks
- Retrieve relevant chunks
- Return source metadata

This module intentionally does not generate answers.
The LLM and Prolog layers remain responsible for reasoning.
"""

from __future__ import annotations


from dataclasses import dataclass
from pathlib import Path

import re

from typing import List


@dataclass(frozen=True)
class DocumentChunk:
    """
    Represents a piece of retrieved knowledge.
    """

    text: str

    source: str

    chunk_id: int



class RAGService:
    """
    Simple retrieval engine.

    Current implementation:
        keyword based retrieval

    Future replacement:
        embeddings + vector database
    """

    def __init__(
        self,
        data_directory: str = "data/snippets",
    ) -> None:

        self.data_directory = Path(
            data_directory
        )

        self.documents: list[DocumentChunk] = []


    def load_documents(self) -> None:
        """
        Load all text files and split them.
        """

        self.documents.clear()


        for file in self.data_directory.glob(
            "*.txt"
        ):

            text = file.read_text(
                encoding="utf-8"
            )


            chunks = self._split_text(
                text
            )


            for index, chunk in enumerate(chunks):

                self.documents.append(
                    DocumentChunk(
                        text=chunk,
                        source=file.name,
                        chunk_id=index,
                    )
                )


    def _split_text(
        self,
        text: str,
        chunk_size: int = 120,
    ) -> list[str]:
        """
        Split text into small chunks.

        Uses words instead of characters
        because medical concepts should
        stay together.
        """

        words = text.split()

        chunks = []

        for i in range(
            0,
            len(words),
            chunk_size,
        ):

            chunk = " ".join(
                words[
                    i:i + chunk_size
                ]
            )

            chunks.append(chunk)


        return chunks



    def _score(
        self,
        query: str,
        document: str,
    ) -> float:
        """
        Simple similarity score.

        Based on word overlap.

        This can later be replaced
        with cosine similarity.
        """

        query_words = set(
            self._normalize(query)
        )


        document_words = set(
            self._normalize(document)
        )


        if not query_words:

            return 0.0


        overlap = (
            query_words
            &
            document_words
        )


        return (
            len(overlap)
            /
            len(query_words)
        )



    def _normalize(
        self,
        text: str,
    ) -> list[str]:
        """
        Basic text preprocessing.
        """

        text = text.lower()


        text = re.sub(
            r"[^a-zA-ZäöüÄÖÜß ]",
            "",
            text,
        )


        return text.split()



    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve relevant chunks.

        Returns UI-friendly objects.
        """

        if not self.documents:

            self.load_documents()



        ranked = []


        for document in self.documents:

            score = self._score(
                query,
                document.text,
            )


            if score > 0:

                ranked.append(
                    {
                        "text": document.text,

                        "title": document.source,

                        "chunk_id": document.chunk_id,

                        "score": score,
                    }
                )


        ranked.sort(
            key=lambda x: x["score"],
            reverse=True,
        )


        return ranked[:top_k]



rag_service = RAGService()