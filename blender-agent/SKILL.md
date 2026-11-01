---
name: blender-agent
description: "Use when driving a live Blender session (MCP or headless bpy) to build or edit 3D scenes and assets, especially game assets exported as GLB for three.js/Babylon. Covers the build→refine→verify loop, small-step bpy calls, driving GUI-only add-ons from code, preferring modifiers and geometry nodes over hand-written vertices, and the GLB export traps (modifier baking, lost procedural textures, name mangling) plus triangle and file-size budgets."
category: creative
risk: safe
source: composed
source_type: composed
license: none-specified
date_added: "2026-10-26"
tags: [blender, bpy, mcp, 3d, geometry-nodes, glb, gltf, game-assets, decimation]
tools: [blender, bpy]
---

# Blender: driving it as an agent

Blender work has exactly one failure mode that matters: **producing something that exists
but is wrong, and declaring it done.** Everything below is built to prevent that.

Two rules frame the rest:

1. **"It generated" ≠ "it's right."** A bare import, or a pile of primitives, is not a result.
2. **Geometry is Blender's job, not yours.** Modifiers and geometry nodes exist. Hand-computing
   vertices is the last resort, never the default.

---

## 1. The loop: build → REFINE → verify

Never skip refine.

| Step | What it means concretely |
|---|---|
| **Decompose** | List the actual objects, real-world sizes, positions, materials, lighting *before* touching bpy. |
| **Base geometry** | Prefer a generator or ready-made asset **only when it genuinely fits**. Otherwise build from primitives + modifiers + bmesh + geometry nodes. Do not force an ill-fitting asset to avoid modeling. |
| **Refine** | Transforms are the floor, not the goal: correct proportions and real dimensions; add/remove geometry; fix topology; model the details the thing implies; tune materials instead of accepting defaults; make parts relate (contact, alignment, consistent scale). |
| **Verify** | Render or screenshot, compare against what was asked, fix the gaps, repeat. Then re-read the scene to confirm the change actually landed. |

**Stop condition is "matches", not "runs without error."**

## 2. Work in small steps, and look between them

- One logical operation per call: add objects → materials → modifiers → verify. A single
  monolithic script that builds everything is unreviewable and undebuggable; when it fails you
  cannot tell which step broke.
- **State lives in `bpy.data`, not in your Python variables.** Each `execute_blender_code` call is
  a fresh namespace. Identify objects by stable name, never by a remembered handle.
- Take a screenshot after every structural change. If you can't see it, you don't know it worked.
- **Save the file before any heavy operation.** Decimate / remesh / boolean on a multi-million-tri
  object can occupy Blender for minutes and lock the UI. Do that in a scratch session, not in
  someone's working file.

## 3. Reconnoiter before acting

Never assume what's installed or what the scene contains:

```python
import bpy
print([a.module for a in bpy.context.preferences.addons])          # enabled add-ons
print([o.name for o in bpy.data.objects][:50])                    # what's already there
print([x for x in dir(bpy.ops.mesh) if not x.startswith("__")])   # available operators
```

Add-on sets differ per machine. Guessing wastes entire sessions.

## 4. Where geometry comes from (in priority order)

1. **A ready-made asset or generator** — only if it genuinely matches. Check dimensions and
   bounding box on import, normalize scale/orientation, place it, then keep refining.
2. **A modifier stack** — array, bevel, solidify, mirror, boolean, displacement, decimate. Cheap,
   non-destructive, adjustable later by a human in the viewport.
3. **Geometry nodes** — the right tool for anything repeated or scattered: dune fields, tree
   scatter, rock distribution, facade modules, cable runs. One node tree with exposed inputs
   (density, amplitude, seed) replaces hundreds of placed objects and stays editable.
4. **`bmesh`** — for real per-face surgery that modifiers can't express.
5. **Raw vertex math** — last resort. If you reach for it, first ask which of 1–4 you skipped.

**Generators produce one item, not a scene.** Never ask a generator for a whole environment or
the ground plane.

### Scatter the standard way

`Distribute Points on Faces` → `Instance on Points`, with density/size/rotation randomized by a
seeded `Random Value`. Expose density and seed as modifier inputs so a human can tune them in the
viewport without touching code.

## 5. Driving add-ons from code

Two kinds, handled differently:

**Operator-based** (archimesh, landscape, tissue, most add-ons) — operator names are global and do
not depend on how the add-on was installed:

```python
bpy.ops.mesh.landscape_add(...)
```

Many such operators `poll()` against a viewport, so calling them headless raises a poll error.
Wrap with a temporary context override:

```python
import bpy
win = bpy.context.window_manager.windows[0]
area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')   # not areas[0] — that may be the timeline
region = next(r for r in area.regions if r.type == 'WINDOW')
with bpy.context.temp_override(window=win, area=area, region=region):
    bpy.ops.mesh.landscape_add(...)
```

If an operator returns `{'FINISHED'}` but nothing appears, the usual cause is missing context or
missing required state on a companion object — check what the add-on's UI panel sets up before it
enables its own button.

**Python-API add-ons installed as extensions (Blender 4.2+)** — the module is namespaced by
*repository*, not importable under the bare name:

```python
import importlib, bpy
# repo module is usually 'blender_org' or 'user_default'
mod = next((m for m in bpy.context.preferences.addons.keys() if m.endswith('.my_addon')), None)
api = importlib.import_module(mod + '.services')
```

Never hardcode `bl_ext.user_default.*` — the repository prefix differs per install.

## 6. Export discipline (GLB for a web engine)

**Export from the command line, not through the MCP bridge.** Long exports time out over the
socket:

```
blender -b scene.blend -P export_script.py
```

### `export_apply` decides what you're actually shipping

- `export_apply=True` **bakes modifiers and geometry nodes** into the exported mesh.
- `export_apply=False` keeps the base mesh and lets the engine see modifiers as nothing (they don't
  survive glTF).

So: decide deliberately, and **measure triangles on the exported GLB, never on the .blend.** A
node tree with a density input can be 2k tris in one setting and 400k in another; only the GLB
tells you the truth.

### What silently dies on export

| Lost | Why | Fix |
|---|---|---|
| Noise / Voronoi / Wave / Musgrave nodes | not representable in glTF | bake to an image, or replace with a flat value |
| Color Ramp / Mix remapping | only the BSDF socket's default is read | bake, or set the final value |
| Procedural bump | same | bake a normal map |
| Modifier stacks (with `export_apply=False`) | not exported | bake, or replicate at runtime |

### Names get rewritten

Blender → glTF: dots are dropped, spaces become underscores.

```
Sphere.003   →  Sphere003
RING ball L  →  RING_ball_L
```

Any runtime code that looks up a mesh **by exact name** breaks on duplicates. Keep names free of
dots and spaces; never rely on an auto-suffixed `.001`.

### Optimizing the file

Do individual steps, in this order:

```
gltf-transform resize in.glb out.glb --width 1024 --height 1024
gltf-transform webp   in.glb out.glb --quality 90
gltf-transform draco  in.glb out.glb        # last; irreversible
```

**Do not use `gltf-transform optimize`** — it includes simplification, which rewrites the mesh.
Draco also commits you to shipping a decoder in the engine; for meshes that are already small,
it is not worth the dependency.

### Always verify after export

- triangle count and per-object breakdown of the exported file
- file size against the project budget
- one render or engine screenshot — the file opening without error is not the same as looking right

## 7. Game-asset specifics

- **Budget is a design constraint, not a cleanup task.** Set a triangle and file-size ceiling
  before modeling; when you exceed it, remove something rather than promising to optimize later.
- **Spend polygons where they're seen.** Facade thickness, window frames, and the insides of solid
  objects are invisible at gameplay distance; terrain silhouettes and skyline are not.
- **Static collision is not the visual mesh.** Export a simple proxy (box, cylinder, coarse
  trimesh) and name it by convention so the engine can pair it with the visual.
- **LOD pays only when the mesh is heavy.** Below a few thousand triangles per object, LODs add
  files and switching logic for no gain.
- **One material per draw call matters more than texture resolution** at this scale. Merge objects
  that share a material before worrying about texture size.

## 8. Anti-patterns

| Don't | Because |
|---|---|
| One giant script that builds the whole scene | can't isolate a failure; every change re-runs everything |
| Hand-computing sine-wave vertices for terrain | modifiers and geometry nodes do it better and stay editable |
| Running decimate/remesh on a huge mesh in a live session | locks the UI; do it in a scratch run, after saving |
| Trusting a screenshot of the viewport as proof of export correctness | the export can drop textures and rename objects |
| Declaring done when the object merely exists | the bar is "matches the request" |
| Installing many add-ons at once | you won't read them, and you'll keep guessing |

## 9. When applying this to a concrete project

Keep project rules out of this skill. Put them in the repository's own `AGENTS.md`:

- naming conventions for visual / collision / reference objects
- polygon and file-size budgets
- what the regression tests assert on the exported file
- which add-ons are actually installed and verified

A skill teaches method; a repository instruction file states constraints. Mixing them makes both rot.

---

## 参考（思路来源，本文为自写，未逐字复制）

| 来源 | 提供了什么 | 许可 |
|---|---|---|
| `vladmdgolam/agent-skills` → `skills/blender-mcp` | GLB 导出的具体陷阱：`export_apply`、程序化贴图丢失、名字改写、gltf-transform 顺序 | 未核实 |
| `QwenLM/Qwen-MM-Plugins` → blender skill | `build → refine → verify` 工作流；插件分两类；`temp_override` 驱动 GUI 算子 | 未核实 |
| `RobLe3/cc-blender-skill` | 命名沿用 Blender Studio 约定；"状态在 `bpy.data`，Python 变量不跨调用" | MIT |
| `ra100/blender-claude-plugin` | 几何节点 / 修改器 / 着色节点的 API 参考库（查资料用） | MIT |
| `PatrykIti/blender-ai-mcp` LLM guide（已归档） | 原则：不要让模型即兴写脚本；确定性检查与断言才是真值层；视觉只作辅助 | 未核实 |
