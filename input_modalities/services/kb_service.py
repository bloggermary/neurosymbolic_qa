"""
Knowledge Base Service.

Responsible for:
- loading medical documents
- generating Prolog knowledge bases
- managing symbolic files
- loading KBs into the Prolog engine
"""

from __future__ import annotations


from dataclasses import dataclass
from pathlib import Path

import janus_swi as janus

from llm.kb_generator import generate_prolog_kb


@dataclass(frozen=True)
class KnowledgeBase:
    """
    Represents one symbolic knowledge base.
    """

    name: str

    source_file: Path

    prolog_file: Path



class KnowledgeBaseService:
    """
    Handles creation and loading of Prolog knowledge bases.
    """

    def __init__(
        self,
        snippets_directory: str = "data/snippets",
        generated_directory: str = "prolog/generated_kbs",
    ) -> None:

        self.snippets_directory = Path(
            snippets_directory
        )

        self.generated_directory = Path(
            generated_directory
        )

        self.generated_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


    def available_databases(self) -> list[str]:
        """
        Returns available medical domains.

        Example:

        [
            "diabetes",
            "asthma",
            "hypertension"
        ]
        """

        return [
            file.stem
            for file in self.snippets_directory.glob(
                "*.txt"
            )
        ]


    def get_database(
        self,
        name: str,
    ) -> KnowledgeBase:
        """
        Create a KnowledgeBase object.
        """

        source = (
            self.snippets_directory
            / f"{name}.txt"
        )

        generated = (
            self.generated_directory
            / f"{name}.pl"
        )


        if not source.exists():

            raise FileNotFoundError(
                f"No medical snippet found for {name}"
            )


        return KnowledgeBase(
            name=name,
            source_file=source,
            prolog_file=generated,
        )


    def build(
        self,
        name: str,
    ) -> KnowledgeBase:
        """
        Generate a Prolog knowledge base.

        The LLM transforms:

        medical text
              |
              v
        Prolog rules
        """

        kb = self.get_database(name)


        text = kb.source_file.read_text(
            encoding="utf-8"
        )


        prolog_code = generate_prolog_kb(
            text
        )


        kb.prolog_file.write_text(
            prolog_code,
            encoding="utf-8",
        )


        return kb



    def load(
        self,
        name: str,
    ) -> KnowledgeBase:
        """
        Build and load the knowledge base
        into SWI-Prolog.
        """

        kb = self.build(name)


        janus.consult(
            str(kb.prolog_file)
        )


        return kb



kb_service = KnowledgeBaseService()