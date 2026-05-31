"""
core/types.py — Foundational types for the elegant thesis-docx core.

These are the stable building blocks. Everything else (Model, Locator, Persistence)
is built on top of these.

Design goals:
- Clear, minimal, immutable where possible
- Strong support for content-based addressing (Anchor)
- Easy to serialize for Task context snapshots
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Any


# =============================================================================
# Core Data Types (stable references)
# =============================================================================

@dataclass(frozen=True)
class ParagraphInfo:
    """Rich, stable representation of a paragraph."""
    index: int
    text: str
    style: str
    level: Optional[int]  # None for body paragraphs
    chapter_path: str     # e.g. "3.2.1"
    alignment: Optional[str] = None
    first_line_indent_cm: Optional[float] = None
    has_image: bool = False
    char_count: int = 0

    # Format fields (Phase 2: style system foundation)
    font_name: Optional[str] = None
    font_size: Optional[float] = None       # pt
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    line_spacing: Optional[float] = None    # ratio (1.0=单倍, 1.5=一倍半) or pt for exact
    line_spacing_rule: Optional[str] = None # "multiple", "exact", "atLeast"
    space_before: Optional[float] = None    # pt
    space_after: Optional[float] = None     # pt

    # Revisions (Track Changes)
    has_revisions: bool = False
    revision_count: int = 0
    revision_types: frozenset[str] = field(default_factory=frozenset)
    revision_authors: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class SectionNode:
    """Tree node representing a heading/section."""
    level: int
    title: str
    para_range: tuple[int, int]  # (start_index, end_index) inclusive
    chapter_path: str
    children: list["SectionNode"] = field(default_factory=list)

    # Revisions stats (aggregated from paragraphs in this section + descendants)
    # Populated during tree building (Phase 1 enhancement)
    has_revisions: bool = False
    revision_count: int = 0
    revision_types: frozenset[str] = field(default_factory=frozenset)

    def get_revised_paragraphs(self, all_paragraphs: list["ParagraphInfo"]) -> list["ParagraphInfo"]:
        """返回本节范围内所有包含修订的段落（含子节）。方便实用。"""
        start, end = self.para_range
        return [p for p in all_paragraphs[start : end + 1] if p.has_revisions]


@dataclass(frozen=True)
class ImageInfo:
    """Stable info about an image in the document."""
    para_index: int
    r_id: str
    filename: str
    format: str  # png, jpg, etc.
    caption: Optional[str] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    chapter_path: str = ""  # Added in E1 for proper entity addressing


@dataclass(frozen=True)
class TableInfo:
    """Stable info about a table (rich enough for SKILL atomic 'table' object word)."""
    para_index: int
    caption: Optional[str] = None
    header: list[str] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    chapter_path: str = ""


@dataclass(frozen=True)
class FormulaInfo:
    """Stable info about a formula (OMML/OLE/placeholder) in the document."""
    para_index: int
    formula_type: str  # "OMML" | "OLE" | "placeholder"
    content: str       # extracted text from m:t elements (approximate readable form)
    equation_number: Optional[str] = None  # e.g. "3.1"
    chapter_path: str = ""


@dataclass(frozen=True)
class ReferenceInfo:
    """Stable info about a reference entry in the bibliography."""
    index: int         # sequence number [1], [2], ...
    para_index: int
    text: str          # full reference text (without [N] prefix)
    ref_type: Optional[str] = None  # "journal"/"conference"/"book"/"thesis"/"online"
    chapter_path: str = ""


# =============================================================================
# Addressing System (the big elegance win)
# =============================================================================

@dataclass(frozen=True)
class Locator:
    """
    Unified way to describe "what I want to find".

    This replaces the scattered by_text / after_text / chapter:3 / section title logic
    that was duplicated all over the original codebase.
    """
    kind: Literal[
        "text",           # contains this substring
        "after_text",     # the paragraph after the one containing this
        "before_text",    # the paragraph before the one containing this
        "chapter",        # e.g. "3" or "3.2"
        "section_title",  # fuzzy match on heading text
        "paragraph_range", # explicit (start, end)
        "image",          # find images (value can be caption substring or chapter)
        "table",          # find tables (value can be caption substring or chapter)
        "formula",        # find formulas (value can be equation number or chapter)
        "reference",      # find references (value can be index number or text)
        "has_revision",   # find paragraphs with track changes
        "revision_type",  # filter by revision type (insertion/deletion)
        "revision_author", # filter by revision author
    ]
    value: Any = None
    # For paragraph_range
    start: Optional[int] = None
    end: Optional[int] = None


@dataclass(frozen=True)
class Anchor:
    """
    A stable, resolved reference to something in the document.

    Upper layers should prefer working with Anchors over raw indexes.
    """
    kind: Literal["paragraph", "section", "image", "table", "formula", "reference"]
    # For paragraph
    paragraph_index: Optional[int] = None
    text_snippet: Optional[str] = None          # for debugging + re-resolution
    chapter_path: Optional[str] = None

    # For section
    section: Optional[SectionNode] = None

    # For image/table
    media_index: Optional[int] = None
