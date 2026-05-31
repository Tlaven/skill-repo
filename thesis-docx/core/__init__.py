"""
thesis-docx elegant core package.

This is the new minimal, high-cohesion heart of the refactored project.
All higher layers (adapters, Task system, API facade) are built on top of this.

Current Phase 1 focus: DocumentModel + Locator + Safe persistence with strong invariants.
"""

from .types import (
    ParagraphInfo,
    SectionNode,
    ImageInfo,
    TableInfo,
    FormulaInfo,
    ReferenceInfo,
    Locator,
    Anchor,
)
from .locator import resolve, resolve_all, to_locator, _find_section_by_chapter_path, _norm_title
from .model import DocumentModel
from .persistence import SafeDocument
from .creator import create_thesis

__all__ = [
    "ParagraphInfo",
    "SectionNode",
    "ImageInfo",
    "TableInfo",
    "FormulaInfo",
    "ReferenceInfo",
    "Locator",
    "Anchor",
    "resolve",
    "resolve_all",
    "to_locator",
    "DocumentModel",
    "SafeDocument",
    "create_thesis",
]
