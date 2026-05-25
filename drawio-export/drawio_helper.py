#!/usr/bin/env python3
"""Draw.io helper - create, inspect, and export .drawio diagrams for academic papers."""

import argparse
import base64
import difflib
import json
import os
import subprocess
import sys
import urllib.parse
import uuid
import zlib
import xml.etree.ElementTree as ET
from xml.dom import minidom

DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"

# ── Shape styles ──────────────────────────────────────────────────────────────

SHAPE_STYLES = {
    "rectangle":     "rounded=0;whiteSpace=wrap;html=1;fontSize=13;",
    "rounded":       "rounded=1;whiteSpace=wrap;html=1;arcSize=10;fontSize=13;",
    "ellipse":       "ellipse;whiteSpace=wrap;html=1;fontSize=13;",
    "diamond":       "rhombus;whiteSpace=wrap;html=1;fontSize=13;",
    "parallelogram": "shape=parallelogram;whiteSpace=wrap;html=1;fontSize=13;",
    "hexagon":       "shape=hexagon;whiteSpace=wrap;html=1;fontSize=13;",
    "cylinder":      "shape=cylinder3;whiteSpace=wrap;html=1;size=15;fontSize=13;",
    "trapezoid":     "shape=trapezoid;whiteSpace=wrap;html=1;fontSize=13;",
    "cloud":         "ellipse;shape=cloud;whiteSpace=wrap;html=1;fontSize=13;",
    "note":          "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;fontSize=13;",
    "process":       "shape=process;whiteSpace=wrap;html=1;fontSize=13;",
    "double-arrow":  "shape=doubleArrow;whiteSpace=wrap;html=1;fontSize=13;",
    "single-arrow":  "shape=singleArrow;whiteSpace=wrap;html=1;fontSize=13;",
    "actor":         "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;fontSize=13;",
    "container":     "swimlane;whiteSpace=wrap;html=1;container=1;startSize=30;collapsible=0;fontSize=13;",
    "text":          "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;fontSize=13;",
}

EDGE_STYLES = {
    "straight":   "endArrow=block;endFill=1;html=1;",
    "orthogonal": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;",
    "curved":     "curved=1;html=1;endArrow=block;endFill=1;",
    "no-arrow":   "endArrow=none;html=1;",
    "dashed":     "endArrow=block;endFill=1;html=1;dashed=1;dashPattern=8 4;",
    "dot-arrow":  "endArrow=block;endFill=0;html=1;",
    "open-arrow": "endArrow=open;endFill=0;html=1;",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _uid():
    return uuid.uuid4().hex[:8]


def _apply_overrides(style, overrides):
    """Merge style key=value pairs into a base style string.

    Later values override earlier ones (mxGraph convention).
    """
    if not overrides:
        return style
    for k, v in overrides.items():
        style += f"{k}={v};"
    return style


def _node_style(ntype, overrides):
    base = SHAPE_STYLES.get(ntype, SHAPE_STYLES["rectangle"])
    return _apply_overrides(base, overrides)


def _edge_style(etype, overrides):
    base = EDGE_STYLES.get(etype, EDGE_STYLES["orthogonal"])
    return _apply_overrides(base, overrides)


def _prettify(elem):
    raw = ET.tostring(elem, encoding="unicode")
    dom = minidom.parseString(raw)
    lines = [l for l in dom.toprettyxml(indent="  ").split("\n") if l.strip()]
    return "\n".join(lines)


def _decode_diagram_content(text):
    """Handle compressed (base64+deflate+url-encode) or plain XML content."""
    text = text.strip()
    if text.startswith("<"):
        return text
    try:
        raw = base64.b64decode(text)
        inflated = zlib.decompress(raw, -zlib.MAX_WBITS)
        return urllib.parse.unquote(inflated.decode("utf-8"))
    except Exception:
        return text


def _out(msg):
    print(json.dumps(msg, ensure_ascii=False))


# ── Validation ────────────────────────────────────────────────────────────────

def _fuzzy_match(typ, valid_set):
    """Suggest closest match from valid_set for an unknown type name."""
    matches = difflib.get_close_matches(typ.lower(), valid_set, n=1, cutoff=0.4)
    return matches[0] if matches else None


def _validate_spec(spec):
    """Validate JSON spec and return (errors, warnings).

    Errors: will cause draw.io to malfunction (refuse to generate).
    Warnings: cosmetic or best-practice (still generate, but report).
    """
    errors = []
    warnings = []

    pages = spec.get("pages", [])
    if not pages and ("nodes" in spec or "edges" in spec):
        pages = [{"name": "Page-1", "nodes": spec.get("nodes", []), "edges": spec.get("edges", [])}]
    if not pages:
        pages = [{"name": "Page-1", "nodes": [], "edges": []}]

    all_shape_types = set(SHAPE_STYLES.keys())
    all_edge_types = set(EDGE_STYLES.keys())

    for pi, page in enumerate(pages):
        page_path = f"pages[{pi}]"
        nodes = page.get("nodes", [])
        edges = page.get("edges", [])

        # Collect expected IDs to detect duplicates
        seen_ids = set()
        node_ids = set()

        for ni, node in enumerate(nodes):
            nid = node.get("id")
            np = f"{page_path}.nodes[{ni}]"
            if not nid:
                errors.append({"path": np, "field": "id", "msg": "Node missing 'id'"})
                continue
            if nid in seen_ids:
                errors.append({"path": np, "field": "id", "msg": f"Duplicate id '{nid}'"})
            seen_ids.add(nid)
            node_ids.add(nid)

            ntype = node.get("type", "rectangle")
            if ntype not in all_shape_types:
                suggestion = _fuzzy_match(ntype, all_shape_types)
                msg = f"Unknown shape type '{ntype}'"
                if suggestion:
                    msg += f", did you mean '{suggestion}'?"
                warnings.append({"path": np, "field": "type", "msg": msg})

            w = node.get("w", 120)
            h = node.get("h", 60)
            if (isinstance(w, (int, float)) and w <= 0) or (isinstance(h, (int, float)) and h <= 0):
                warnings.append({"path": np, "field": "w/h", "msg": "Width and height should be positive"})

            parent = node.get("parent")
            if parent is not None and str(parent) != "1":
                # Will verify parent exists after collecting all node IDs
                pass

        # Verify parent references (must be checked after all node IDs collected)
        for ni, node in enumerate(nodes):
            parent = node.get("parent")
            if parent is not None and str(parent) != "1":
                if parent not in node_ids:
                    errors.append({
                        "path": f"{page_path}.nodes[{ni}]",
                        "field": "parent",
                        "msg": f"Parent '{parent}' not found in page"
                    })

        for ei, edge in enumerate(edges):
            ep = f"{page_path}.edges[{ei}]"
            eid = edge.get("id")
            if eid:
                if eid in seen_ids:
                    errors.append({"path": ep, "field": "id", "msg": f"Duplicate id '{eid}'"})
                seen_ids.add(eid)

            frm = edge.get("from")
            to = edge.get("to")
            if not frm:
                errors.append({"path": ep, "field": "from", "msg": "Edge missing 'from'"})
            elif frm not in node_ids:
                errors.append({"path": ep, "field": "from", "msg": f"Edge references unknown node '{frm}'"})
            if not to:
                errors.append({"path": ep, "field": "to", "msg": "Edge missing 'to'"})
            elif to not in node_ids:
                errors.append({"path": ep, "field": "to", "msg": f"Edge references unknown node '{to}'"})

            etype = edge.get("type", "orthogonal")
            if etype not in all_edge_types:
                suggestion = _fuzzy_match(etype, all_edge_types)
                msg = f"Unknown edge type '{etype}'"
                if suggestion:
                    msg += f", did you mean '{suggestion}'?"
                warnings.append({"path": ep, "field": "type", "msg": msg})

            # Validate waypoints
            waypoints = edge.get("waypoints")
            if waypoints is not None:
                if not isinstance(waypoints, list) or len(waypoints) < 1:
                    warnings.append({"path": ep, "field": "waypoints", "msg": "waypoints should be a non-empty array of [x,y] pairs"})
                else:
                    for wpi, wp in enumerate(waypoints):
                        if not isinstance(wp, (list, tuple)) or len(wp) < 2:
                            warnings.append({"path": f"{ep}.waypoints[{wpi}]", "msg": "Each waypoint should be [x, y]"})

    return errors, warnings


# ── Auto layout (Graphviz) ────────────────────────────────────────────────────

SHAPE_TO_DOT = {
    "rectangle": "box", "rounded": "box", "ellipse": "ellipse",
    "diamond": "diamond", "parallelogram": "parallelogram", "hexagon": "hexagon",
    "cylinder": "cylinder", "trapezoid": "trapezium", "cloud": "cloud",
    "note": "note", "container": "box", "actor": "box", "text": "plaintext",
    "process": "box", "double-arrow": "box", "single-arrow": "box",
}

DOT_INCH = 72.0


def _needs_layout(nodes):
    """Auto-layout needed if no node has explicit x/y."""
    for n in nodes:
        if n.get("x") is not None or n.get("y") is not None:
            return False
    return len(nodes) > 0


def _spec_to_dot(nodes, edges, max_width, rankdir):
    lines = ["digraph G {"]
    lines.append(f"  rankdir={rankdir};")
    lines.append("  splines=polyline;")
    lines.append("  nodesep=0.6;")
    lines.append("  ranksep=0.8;")
    if max_width:
        lines.append(f'  size="{max_width},";')
    for node in nodes:
        nid = node["id"]
        label = node.get("label", "")
        shape = SHAPE_TO_DOT.get(node.get("type", "rectangle"), "box")
        w = node.get("w", 120) / DOT_INCH
        h = node.get("h", 60) / DOT_INCH
        escaped = label.replace("\\", "\\\\").replace("\"", "\\\"")
        lines.append(f'  "{nid}" [label="{escaped}", shape="{shape}", width={w:.3f}, height={h:.3f}];')
    for edge in edges:
        frm = edge.get("from", "")
        to = edge.get("to", "")
        label = edge.get("label", "")
        if label:
            escaped = label.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(f'  "{frm}" -> "{to}" [label="{escaped}"];')
        else:
            lines.append(f'  "{frm}" -> "{to}";')
    lines.append("}")
    return "\n".join(lines)


def _run_dot_layout(nodes, edges, max_width, rankdir):
    """Run Graphviz dot layout. Returns (ok, message, positioned_nodes)."""
    try:
        which = subprocess.run(["dot", "-V"], capture_output=True, timeout=5)
        if which.returncode != 0:
            return False, "Graphviz (dot) not found. Install from https://graphviz.org/download/", None
    except Exception:
        return False, "Graphviz (dot) not found. Install from https://graphviz.org/download/", None

    dot_source = _spec_to_dot(nodes, edges, max_width, rankdir)
    try:
        proc = subprocess.run(["dot", "-Tplain"],
                              input=dot_source.encode("utf-8"),
                              capture_output=True, timeout=30)
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")[:300]
            return False, f"dot layout failed: {stderr}", None
    except Exception as e:
        return False, f"dot layout error: {e}", None

    stdout = proc.stdout.decode("utf-8", errors="replace")

    # Parse plain output
    graph_h = 0
    result = {}
    for line in stdout.strip().split("\n"):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "graph":
            # Format: graph scale width height
            graph_h = float(parts[3]) * DOT_INCH
        elif parts[0] == "node":
            nid = parts[1]
            cx = float(parts[2]) * DOT_INCH
            cy = float(parts[3]) * DOT_INCH
            w = float(parts[4]) * DOT_INCH
            h = float(parts[5]) * DOT_INCH
            # Graphviz: y-up, origin bottom-left
            # draw.io: y-down, origin top-left
            # Flip: drawio_y = graph_h - gv_y - h
            result[nid] = {"x": cx - w / 2, "y": graph_h - cy - h, "w": w, "h": h}

    if not result:
        return False, "dot returned no node positions", None

    return True, None, result


# ── create ────────────────────────────────────────────────────────────────────

def cmd_create(args):
    if args.spec_file:
        with open(args.spec_file, "r", encoding="utf-8") as f:
            spec = json.load(f)
    elif args.spec:
        spec = json.loads(args.spec)
    else:
        _out({"status": "error", "message": "provide --spec or --spec-file"})
        sys.exit(1)

    # Validate before generating
    errors, warnings = _validate_spec(spec)
    if errors:
        _out({"status": "error", "message": "Spec validation failed, file not generated",
              "errors": errors, "warnings": warnings})
        sys.exit(1)

    pages = spec.get("pages", [])

    # If no pages key, treat top-level as a single page
    if not pages and ("nodes" in spec or "edges" in spec):
        pages = [{"name": "Page-1", "nodes": spec.get("nodes", []), "edges": spec.get("edges", [])}]

    if not pages:
        pages = [{"name": "Page-1", "nodes": [], "edges": []}]

    # Auto-layout for pages without explicit coordinates
    for page in pages:
        nodes = page.get("nodes", [])
        edges = page.get("edges", [])
        if _needs_layout(nodes):
            ok, msg, positions = _run_dot_layout(nodes, edges, args.max_width, args.rankdir)
            if not ok:
                _out({"status": "error", "message": f"Auto-layout failed: {msg}"})
                sys.exit(1)
            for node in nodes:
                pos = positions.get(node["id"])
                if pos:
                    node["x"] = pos["x"]
                    node["y"] = pos["y"]
                    if node.get("w") is None:
                        node["w"] = pos["w"]
                    if node.get("h") is None:
                        node["h"] = pos["h"]

    mxfile = ET.Element("mxfile", {"host": "drawio-helper", "modified": "2026-01-01T00:00:00.000Z",
                                    "agent": "drawio-helper", "version": "1.0"})

    for page_spec in pages:
        root = ET.Element("root")
        root.append(ET.Element("mxCell", id="0"))
        root.append(ET.Element("mxCell", id="1", parent="0"))

        id_map = {}

        for node in page_spec.get("nodes", []):
            nid = node.get("id", _uid())
            id_map[nid] = nid
            style = _node_style(node.get("type", "rectangle"), node.get("style"))
            parent_id = node.get("parent")
            parent = str(parent_id) if parent_id is not None else "1"
            cell = ET.Element("mxCell", {
                "id": nid,
                "value": node.get("label", ""),
                "style": style,
                "vertex": "1",
                "parent": parent,
            })
            ET.SubElement(cell, "mxGeometry", {
                "x": str(node.get("x", 0)),
                "y": str(node.get("y", 0)),
                "width": str(node.get("w", 120)),
                "height": str(node.get("h", 60)),
                "as": "geometry",
            })
            root.append(cell)

        for edge in page_spec.get("edges", []):
            eid = edge.get("id", _uid())
            style = _edge_style(edge.get("type", "orthogonal"), edge.get("style"))

            # Connection point overrides — control which side of a node the edge connects to.
            # Values are relative (0-1): exitX=0.5,exitY=1 = bottom center of source.
            for key in ("exitX", "exitY", "exitDx", "exitDy",
                        "entryX", "entryY", "entryDx", "entryDy"):
                if key in edge:
                    style += f"{key}={edge[key]};"

            # Label positioning via style properties
            for key in ("labelPosition", "verticalLabelPosition", "labelBackgroundColor"):
                if key in edge:
                    style += f"{key}={edge[key]};"

            cell = ET.Element("mxCell", {
                "id": eid,
                "value": edge.get("label", ""),
                "style": style,
                "edge": "1",
                "source": str(edge.get("from", "")),
                "target": str(edge.get("to", "")),
                "parent": "1",
            })

            # Build geometry with optional label offset and waypoints
            waypoints = edge.get("waypoints")
            label_x = edge.get("labelX")
            label_y = edge.get("labelY")

            if waypoints or label_x is not None or label_y is not None:
                geom_attrs = {"relative": "1", "as": "geometry"}
                if label_x is not None:
                    geom_attrs["x"] = str(label_x)
                if label_y is not None:
                    geom_attrs["y"] = str(label_y)
                geom = ET.SubElement(cell, "mxGeometry", geom_attrs)
                if waypoints:
                    arr = ET.SubElement(geom, "Array", {"as": "points"})
                    for wp in waypoints:
                        ET.SubElement(arr, "mxPoint", {"x": str(wp[0]), "y": str(wp[1])})
            else:
                ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            root.append(cell)

        graph_model = ET.Element("mxGraphModel")
        graph_model.append(root)

        diagram = ET.Element("diagram", {"name": page_spec.get("name", "Page-1"), "id": _uid()})
        diagram.append(graph_model)
        mxfile.append(diagram)

    output = args.output or "diagram.drawio"
    with open(output, "w", encoding="utf-8") as f:
        f.write(_prettify(mxfile))

    result = {"status": "success", "output": os.path.abspath(output), "pages": len(pages)}
    if warnings:
        result["warnings"] = warnings
    _out(result)


# ── export ────────────────────────────────────────────────────────────────────

def cmd_export(args):
    if not os.path.exists(args.input):
        _out({"status": "error", "message": f"File not found: {args.input}"})
        sys.exit(1)

    fmt = args.format
    output = args.output

    # Infer format from output extension
    if output:
        ext = os.path.splitext(output)[1].lstrip(".")
        if ext in ("pdf", "png", "jpg", "jpeg", "svg", "xml", "html"):
            fmt = ext if ext != "jpeg" else "jpg"

    cmd = [DRAWIO_EXE, "--export", "--format", fmt, "--no-sandbox"]

    if output:
        cmd += ["--output", os.path.abspath(output)]
    if args.page_index:
        cmd += ["--page-index", str(args.page_index)]
    if args.scale:
        cmd += ["--scale", str(args.scale)]
    if args.width:
        cmd += ["--width", str(args.width)]
    if args.height:
        cmd += ["--height", str(args.height)]
    if args.border is not None:
        cmd += ["--border", str(args.border)]
    if args.transparent:
        cmd += ["--transparent"]
    if args.crop:
        cmd += ["--crop"]
    if args.embed:
        cmd += ["--embed-diagram"]
    if args.embed_svg_images:
        cmd += ["--embed-svg-images"]
    if args.embed_svg_fonts is not None:
        cmd += ["--embed-svg-fonts", str(args.embed_svg_fonts).lower()]
    if args.all_pages:
        cmd += ["--all-pages"]
    if args.uncompressed:
        cmd += ["--uncompressed"]

    cmd.append(os.path.abspath(args.input))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not output:
            base = os.path.splitext(args.input)[0]
            output = f"{base}.{fmt}"

        if result.returncode != 0:
            _out({"status": "error", "message": (result.stderr or result.stdout)[:500],
                  "output": output if output else None})
            sys.exit(1)

        # Post-process: strip the global SVG <switch> fallback if --clean
        if args.clean and fmt == "svg":
            raw = open(output, 'r', encoding='utf-8').read()
            last_switch = raw.rfind('<switch>')
            svg_close = raw.rfind('</svg>')
            if 0 < last_switch < svg_close:
                switch_end = raw.find('</switch>', last_switch)
                if switch_end > 0:
                    raw = raw[:last_switch] + raw[switch_end + len('</switch>'):]
                    open(output, 'w', encoding='utf-8').write(raw)

        _out({"status": "success", "output": os.path.abspath(output), "format": fmt})
    except subprocess.TimeoutExpired:
        _out({"status": "error", "message": "Export timed out (120s)"})
        sys.exit(1)
    except Exception as e:
        _out({"status": "error", "message": str(e)})
        sys.exit(1)


# ── info ──────────────────────────────────────────────────────────────────────

def cmd_info(args):
    if not os.path.exists(args.input):
        _out({"status": "error", "message": f"File not found: {args.input}"})
        sys.exit(1)

    try:
        tree = ET.parse(args.input)
        mxfile = tree.getroot()
    except ET.ParseError:
        _out({"status": "error", "message": "Invalid XML"})
        sys.exit(1)

    diagrams = []
    for diag in mxfile.findall("diagram"):
        name = diag.get("name", "Unnamed")
        content = ""
        # Check if diagram has direct mxGraphModel child (uncompressed)
        gm = diag.find("mxGraphModel")
        if gm is not None:
            root = gm.find("root")
        else:
            # Compressed content - decode it
            content = (diag.text or "").strip()
            if not content:
                diagrams.append({"name": name, "id": diag.get("id", ""), "nodes": 0, "edges": 0})
                continue
            try:
                decoded = _decode_diagram_content(content)
                sub_root = ET.fromstring(decoded)
                if sub_root.tag == "mxGraphModel":
                    root = sub_root.find("root")
                else:
                    root = sub_root
            except Exception:
                diagrams.append({"name": name, "id": diag.get("id", ""), "nodes": "?", "edges": "?"})
                continue

        nodes = edges = 0
        if root is not None:
            for cell in root.findall("mxCell"):
                if cell.get("vertex") == "1":
                    nodes += 1
                elif cell.get("edge") == "1":
                    edges += 1

        diagrams.append({"name": name, "id": diag.get("id", ""), "nodes": nodes, "edges": edges})

    _out({"status": "success", "file": os.path.abspath(args.input),
          "pages": len(diagrams), "diagrams": diagrams})


# ── check ──────────────────────────────────────────────────────────────────────

def cmd_check(args):
    result = {"status": "success", "platform": sys.platform}

    # Check draw.io desktop at default path
    exe_default = DRAWIO_EXE
    exe_found = None
    if os.path.exists(exe_default):
        exe_found = exe_default
    else:
        # Try PATH lookup
        try:
            which = subprocess.run(["where", "draw.io"], capture_output=True, text=True, timeout=5)
            if which.returncode == 0:
                exe_found = which.stdout.strip().split("\n")[0].strip()
        except Exception:
            pass

    result["drawio_exe"] = exe_found

    if exe_found and os.path.normpath(exe_found) != os.path.normpath(exe_default):
        result["path_mismatch"] = True
        result["suggestion"] = (
            f"draw.io found at '{exe_found}' but SKILL default is '{exe_default}'. "
            "Tell the Agent to update DRAWIO_EXE in drawio_helper.py for permanent fix."
        )
    elif not exe_found:
        result["path_mismatch"] = False
        result["suggestion"] = (
            f"draw.io not found. Download from https://github.com/jgraph/drawio-desktop/releases "
            f"and install to default path (or tell the Agent your custom path to update SKILL)."
        )
    else:
        result["path_mismatch"] = False

    # Check Docker availability (informational)
    try:
        docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        result["docker_available"] = docker_check.returncode == 0
    except Exception:
        result["docker_available"] = False

    # Check Graphviz availability (auto-layout)
    try:
        gv_check = subprocess.run(["dot", "-V"], capture_output=True, timeout=5)
        result["graphviz_available"] = gv_check.returncode == 0
    except Exception:
        result["graphviz_available"] = False

    # Determine if export is possible
    if exe_found:
        result["can_export"] = True
        result["export_method"] = "desktop"
    elif result["docker_available"]:
        result["can_export"] = True
        result["export_method"] = "docker"
    else:
        result["can_export"] = False
        result["export_method"] = None

    _out(result)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Draw.io helper for academic papers")
    sub = parser.add_subparsers(dest="command")

    # check
    p = sub.add_parser("check", help="Check draw.io availability and export methods")

    # create
    p = sub.add_parser("create", help="Create .drawio from JSON spec")
    p.add_argument("--spec", help="JSON spec string")
    p.add_argument("--spec-file", help="JSON spec file path")
    p.add_argument("-o", "--output", help="Output .drawio file")
    p.add_argument("--max-width", type=float, default=5.5,
                   help="Max diagram width in inches (default 5.5 ≈ 14cm, auto-layout only). "
                        "~5.5 inches ≈ 14cm for thesis, ~7 inches ≈ A4 portrait.")
    p.add_argument("--rankdir", choices=["TB", "LR", "BT", "RL"], default="TB",
                   help="Graphviz layout direction: TB=top-bottom (tall), LR=left-right (wide). "
                        "Default TB. Use LR for wide diagrams with many nodes.")


    # export
    p = sub.add_parser("export", help="Export .drawio to SVG/PNG/PDF")
    p.add_argument("input", help="Input .drawio file")
    p.add_argument("-f", "--format", default="svg", choices=["svg", "png", "pdf", "jpg", "xml", "html"])
    p.add_argument("-o", "--output", help="Output file path")
    p.add_argument("--page-index", type=int, help="Page index (1-based)")
    p.add_argument("--scale", type=float, help="Scale factor")
    p.add_argument("--width", type=int, help="Fit width (px)")
    p.add_argument("--height", type=int, help="Fit height (px)")
    p.add_argument("--border", type=int, help="Border width around diagram")
    p.add_argument("--transparent", action="store_true", help="Transparent background (PNG)")
    p.add_argument("--crop", action="store_true", help="Crop to diagram size")
    p.add_argument("--embed", action="store_true", help="Embed diagram copy")
    p.add_argument("--embed-svg-images", action="store_true", help="Embed images in SVG")
    p.add_argument("--embed-svg-fonts", type=lambda x: x.lower() == "true", nargs="?", const=False, default=None,
                   help="Embed fonts in SVG (default: draw.io default). Pass --embed-svg-fonts false for simple SVG text.")
    p.add_argument("--all-pages", action="store_true", help="Export all pages")
    p.add_argument("--uncompressed", action="store_true", help="Uncompressed SVG/XML output")
    p.add_argument("--clean", action="store_true",
                   help="Post-process SVG to remove global <switch> fallback message.")

    # info
    p = sub.add_parser("info", help="Show .drawio file info")
    p.add_argument("input", help="Input .drawio file")

    args = parser.parse_args()
    if args.command == "create":
        cmd_create(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "check":
        cmd_check(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
