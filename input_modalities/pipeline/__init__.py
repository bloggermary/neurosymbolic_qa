"""
Pipeline layer for multimodal medical QA system.

This package exposes:
- IngestionPipeline: builds Prolog knowledge bases from raw text
- QAPipeline: handles question answering over Prolog KBs
- FollowupPipeline: generates follow-up questions based on QA context
"""

from .ingestion_pipeline import IngestionPipeline
from .qa_pipeline import QAPipeline
from .followup_pipeline import FollowupPipeline

__all__ = [
    "IngestionPipeline",
    "QAPipeline",
    "FollowupPipeline"
]