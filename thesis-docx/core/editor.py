"""
core/editor.py — Batch and move paragraph operations.

Mixin for SafeDocument. Methods assume self.model, self._rebuild() exist.
"""

from __future__ import annotations

from .types import Anchor, Locator


class EditorMixin:

    def replace_batch(self, pairs: list[tuple[str, str]], chapter: str | None = None) -> dict:
        """Batch substring replacement across paragraphs.

        Reuses replace_text() for each hit, preserving formatting and revision-awareness.
        Does NOT call save() — caller decides when to persist.
        """
        if not pairs:
            return {"total_replacements": 0, "details": []}

        para_start, para_end = 0, len(self.model._paragraphs) - 1
        if chapter:
            sec_anchor = self.model.resolve(Locator(kind="chapter", value=chapter))
            if not sec_anchor or not sec_anchor.section:
                return {"error": f"Chapter '{chapter}' not found"}
            para_start, para_end = sec_anchor.section.para_range

        total = 0
        details = []
        for old_text, new_text in pairs:
            count = 0
            preview = None
            for i in range(para_start, para_end + 1):
                if i >= len(self.model._paragraphs):
                    break
                p = self.model._paragraphs[i]
                if old_text not in p.text:
                    continue
                full_replacement = p.text.replace(old_text, new_text)
                anchor = Anchor(
                    kind="paragraph", paragraph_index=p.index,
                    text_snippet=p.text[:80], chapter_path=p.chapter_path,
                )
                if self.replace_text(anchor, full_replacement):
                    count += 1
                    if preview is None:
                        preview = full_replacement[:60]
            total += count
            entry = {"old": old_text[:40], "new": new_text[:40], "replacements": count}
            if preview:
                entry["first_match_preview"] = preview
            if count == 0:
                entry["warning"] = "no matches"
            details.append(entry)

        return {"total_replacements": total, "details": details}

    def replace_batch_by_index(self, pairs: dict[str, str] | list[tuple[int, str]]) -> dict:
        """Batch replacement by paragraph index (used by aigc-derate).

        Does NOT call save() — caller decides when to persist.
        """
        if isinstance(pairs, dict):
            items = sorted(pairs.items(), key=lambda x: int(x[0]))
        else:
            items = sorted(pairs, key=lambda x: x[0])

        total = 0
        details = []
        for idx_key, new_text in items:
            idx = int(idx_key) if isinstance(idx_key, str) else idx_key
            if idx < 0 or idx >= len(self.model._doc.paragraphs):
                details.append({"paragraph": idx, "error": "index out of range"})
                continue
            old_text = self.model._paragraphs[idx].text if idx < len(self.model._paragraphs) else ""
            anchor = Anchor(kind="paragraph", paragraph_index=idx, text_snippet=old_text[:80])
            if self.replace_text(anchor, new_text):
                total += 1
                details.append({
                    "paragraph": idx,
                    "old_chars": len(old_text),
                    "new_chars": len(new_text),
                    "old_preview": old_text[:50],
                    "new_preview": new_text[:50],
                })
            else:
                details.append({"paragraph": idx, "error": "replace failed"})

        return {"total_replaced": total, "details": details}

    def move_paragraph(self, source: Anchor, after: Anchor | None = None) -> bool:
        """Atomically move a paragraph. On failure the document is unchanged."""
        if source.kind != "paragraph" or source.paragraph_index is None:
            return False

        src_idx = source.paragraph_index
        if after and after.paragraph_index is not None and src_idx == after.paragraph_index:
            return True  # no-op

        from copy import deepcopy
        src_elem = self.model._doc.paragraphs[src_idx]._element
        cloned = deepcopy(src_elem)

        try:
            if after and after.paragraph_index is not None:
                dst_idx = after.paragraph_index
                if dst_idx < 0 or dst_idx >= len(self.model._doc.paragraphs):
                    return False
                dst_elem = self.model._doc.paragraphs[dst_idx]._element
                dst_elem.addnext(cloned)
            else:
                self.model._doc.element.body.insert(0, cloned)
            src_elem.getparent().remove(src_elem)
            self._rebuild()
            return True
        except Exception:
            if cloned.getparent() is not None:
                cloned.getparent().remove(cloned)
            return False
