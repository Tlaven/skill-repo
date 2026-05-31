"""
core/table.py — Table write operations.

Mixin for SafeDocument. Methods assume self.model, self._rebuild() exist.
"""

from __future__ import annotations

from lxml import etree

from .types import Anchor


class TableMixin:

    def replace_table(self, anchor_or_index: Anchor | int, data: list[list[str]]) -> bool:
        """Replace all cells in an existing table. Does NOT call save()."""
        if isinstance(anchor_or_index, int):
            t_idx = anchor_or_index
        elif isinstance(anchor_or_index, Anchor):
            if anchor_or_index.media_index is not None:
                t_idx = anchor_or_index.media_index
            else:
                t_idx = self._resolve_table_index_by_anchor(anchor_or_index)
                if t_idx is None:
                    return False
        else:
            return False

        tables = self.model._doc.tables
        if t_idx < 0 or t_idx >= len(tables) or not data or not data[0]:
            return False

        table = tables[t_idx]

        w_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

        # Adjust rows
        while len(table.rows) < len(data):
            table.add_row()
        while len(table.rows) > len(data):
            tr = table.rows[-1]._tr
            tr.getparent().remove(tr)

        # Adjust columns
        target_cols = max(len(row) for row in data)
        current_cols = len(table.columns)
        if current_cols < target_cols:
            grid = table._tbl.find(f'{w_ns}tblGrid')
            widths = []
            if grid is not None:
                widths = [int(gc.get(f'{w_ns}w')) for gc in grid.findall(f'{w_ns}gridCol') if gc.get(f'{w_ns}w')]
            default_width = widths[-1] if widths else 914
            for _ in range(target_cols - current_cols):
                table.add_column(default_width)
        elif current_cols > target_cols:
            self._remove_extra_table_columns(table, target_cols)

        # Fill cells
        for r_idx, row_data in enumerate(data):
            for c_idx, cell_text in enumerate(row_data):
                cell = table.cell(r_idx, c_idx)
                for p in cell.paragraphs[1:]:
                    p._element.getparent().remove(p._element)
                first_p = cell.paragraphs[0]
                for run in first_p.runs:
                    run._element.getparent().remove(run._element)
                if cell_text:
                    first_p.add_run(cell_text)

        self.model._build_table_index()
        return True

    def insert_table(self, after: Anchor, data: list[list[str]],
                     caption: str | None = None, three_line: bool = False) -> bool:
        """Insert a new table after the specified paragraph. Does NOT call save()."""
        if after.kind != "paragraph" or after.paragraph_index is None:
            return False
        if not data or not data[0]:
            return False

        idx = after.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        num_rows = len(data)
        num_cols = max(len(row) for row in data)
        padded = [row + [""] * (num_cols - len(row)) for row in data]

        table = self.model._doc.add_table(rows=num_rows, cols=num_cols)
        for r_idx, row_data in enumerate(padded):
            for c_idx, cell_text in enumerate(row_data):
                table.cell(r_idx, c_idx).text = str(cell_text)

        if three_line:
            self._apply_three_line_table(table._tbl, num_rows, num_cols)

        # Detach from default position and reposition
        tbl_element = table._tbl
        tbl_element.getparent().remove(tbl_element)
        ref_elem = self.model._doc.paragraphs[idx]._element

        if caption:
            caption_style = self._detect_caption_style()
            cap_p = self.model._doc.add_paragraph(caption, style=caption_style or "Normal")
            cap_p._element.getparent().remove(cap_p._element)
            ref_elem.addnext(cap_p._element)
            cap_p._element.addnext(tbl_element)
        else:
            ref_elem.addnext(tbl_element)

        self._rebuild()
        return True

    # -- Private helpers --

    def _resolve_table_index_by_anchor(self, anchor: Anchor) -> int | None:
        for i, t in enumerate(self.model._tables):
            if t.para_index == anchor.paragraph_index:
                return i
        return None

    def _remove_extra_table_columns(self, table, keep_count: int):
        w_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        for tr in table._tbl.findall(f'{w_ns}tr'):
            cells = tr.findall(f'{w_ns}tc')
            for cell in cells[keep_count:]:
                tr.remove(cell)
        # Also remove extra gridCol elements from tblGrid
        tblGrid = table._tbl.find(f'{w_ns}tblGrid')
        if tblGrid is not None:
            gridCols = tblGrid.findall(f'{w_ns}gridCol')
            for gc in gridCols[keep_count:]:
                tblGrid.remove(gc)

    def _apply_three_line_table(self, tbl_element, num_rows: int, num_cols: int):
        """Apply three-line table border style (academic standard)."""
        w_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

        for r_idx, tr in enumerate(tbl_element.findall(f'{w_ns}tr')):
            for tc in tr.findall(f'{w_ns}tc'):
                tcPr = tc.find(f'{w_ns}tcPr')
                if tcPr is None:
                    tcPr = etree.SubElement(tc, f'{w_ns}tcPr')
                    tc.insert(0, tcPr)
                for old_b in tcPr.findall(f'{w_ns}tcBorders'):
                    tcPr.remove(old_b)
                borders = etree.SubElement(tcPr, f'{w_ns}tcBorders')
                if r_idx == 0:
                    top = etree.SubElement(borders, f'{w_ns}top')
                    top.set(f'{w_ns}val', 'single')
                    top.set(f'{w_ns}sz', '12')
                    top.set(f'{w_ns}space', '0')
                    top.set(f'{w_ns}color', '000000')
                if r_idx == 0 or r_idx == num_rows - 1:
                    bottom = etree.SubElement(borders, f'{w_ns}bottom')
                    bottom.set(f'{w_ns}val', 'single')
                    bottom.set(f'{w_ns}sz', '4')
                    bottom.set(f'{w_ns}space', '0')
                    bottom.set(f'{w_ns}color', '000000')
