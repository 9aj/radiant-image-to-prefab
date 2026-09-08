# Image → Radiant

A local image-to-brush prefab converter for CoD4 / IW3xo Radiant.

## Run

Double-click **Launch.cmd** to open **Prefab Drop**, a native Windows application.

1. **Choose folder** or paste the path to your map source / prefab folder. Files save directly into this folder.
2. Drag one or more images onto the drop area, or click **or choose images**. Conversion starts automatically.
3. Each image saves as `prefab_<image-name>.map`. Existing files are kept; duplicates get `_1`, `_2`, and so on. Results appear at the bottom.

The folder and conversion settings are remembered in `preferences.json` alongside the app. **Open prefab folder** opens the selected destination in Explorer. The queue runs in the background so the window stays responsive. The app waits for queued work to finish before closing.

Depth, solid area, and orientation are visible; resolution, cell size, and threshold are under **Size and detail**. Default output is 384 units along the longest image edge, 32 units deep. Auto texture is enabled by default; turn it off for caulk-only output. For a quick trial, drop `examples/honeycomb.png`.

The interface uses Windows PowerShell/WPF, with no browser, server, or extra UI packages. The converter uses a local `.venv` when available, then Codex bundled Python, then system Python.
On another Windows machine install standard Windows Python 3.14 (not MSYS2/MinGW), then run:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install --only-binary=:all: -r requirements.txt
```

## Geometry settings and Radiant import

1. Use a front-facing silhouette/mask, ideally black on white, or a transparent PNG.
2. Choose **dark** (dark opaque pixels), **light** (light opaque pixels), or **alpha** (opacity above threshold, ignoring color).
3. Set resolution, units per cell, and extrusion depth. Default 96 cells × 4 units produces a 384-unit longest edge. Image aspect ratio is preserved to the nearest cell; surrounding whitespace contributes to size.
4. Choose **floor** for image in XY, extrusion from Z=0 upward. Choose **wall** for image in XZ, extrusion from Y=0 forward. The image plane is centered on the origin. Top of image maps to positive Y for floors or positive Z for walls.
5. Dropping images starts conversion with the current settings. For the older preview interface, run `python app.py` with a Python installation that has Pillow and Tk. The CLI can also generate preview PNGs.
6. Open the exported `.map` in your CoD4/IW3xo Radiant to inspect it. You can copy its brushes into your map or place the file in your project's prefab directory and use your prefab workflow.
7. Replace `caulk` on visible surfaces with a material from your installation. Caulk is a geometry placeholder and will not provide a visible finished surface in game. Compile and inspect collision in your actual map before using it for jumps.

## What this version does

- Resamples the image to a bounded grid and thresholds it into solid/empty cells.
- Preserves holes and disconnected parts that survive that sampling.
- Chooses the smallest of four rectangle partitions: row-run and greedy rectangle merging in both image orientations. Coverage is exact and brushes do not overlap; the result never uses more brushes than the original row-run method.
- Exports six-plane brushes in `iwmap 4`, in a worldspawn entity, without player spawns or lighting.
- Rejects empty masks, invalid dimensions/material names, excessive brush counts, and geometry beyond the configured coordinate guardrail.
- Processes images locally without uploads.

This is a **grid-based extrusion MVP**. Diagonal and curved edges are stepped, not vector-traced or beveled. More resolution improves those edges but can create many small brushes. The brush limit is an application guardrail, not a statement of engine limits. Very thin features can disappear during sampling. There is no photo-to-3D reconstruction, heightmap interpretation, or patch export yet. The preview is illustrative, not a Radiant renderer.

Rectangle optimization preserves every occupied cell and hole after sampling. It is a heuristic, not a guaranteed globally minimal partition. The tested Iron Man silhouette decreased from 84 to 64 brushes (23.8%) with identical coverage and the same shared texture projection.

## Custom materials

Set **CoD4 Mod Tools folder** to the installation containing `bin/converter.exe`. With automatic texture enabled, dropping an image compiles an opaque metal colour material and assigns it to the prefab. Front/back faces share one fitted projection over the entire image canvas, including margins. CoD4 texture sizes and shifts are in world units. Thin side faces retain tiled mapping.

The **Single texture** tab imports one image without creating geometry. Use **Copy material name**, reload textures or restart Radiant, and find the returned `pd_...` material under **Generic / floor**. No `textures/` prefix is used. The app does not control a running Radiant session.

Images become TGA sources with power-of-two dimensions from 32 to 1024 per axis. Alpha is flattened onto dark grey for the opaque material; PNG transparency can still define the geometry mask. This is source-image colour import, not generated normal/specular maps or reconstructed side artwork.

Sources are saved in `texture_assets` and `source_data`; compiled assets are saved in `raw/materials`, `raw/images`, and `raw/material_properties`. Content-based names prevent collisions. Unchanged verified assets are reused. **Conversion logs** opens `.prefabdrop/logs`. Failure to compile prevents prefab output, while source files and logs remain for diagnosis.

The importer runs `converter.exe -nopause -single material <name>` from the installation's `bin` directory. It verifies the generated files because this converter can return zero after an error. Conversions have a 90-second timeout and are serialized with an OS-managed lock. The selected installation must include the material definitions supplied with the Mod Tools.

Build and package maps normally to include these editor assets in the final game distribution. Installing into `raw` does not itself build a fastfile or IWD.

## CLI

```powershell
python app.py examples/honeycomb.png -o honeycomb.map --resolution 96 --cell 4 --depth 32 --preview honeycomb-preview.png
python app.py logo.png -o wall.map --mode alpha --orientation wall --depth 16
python -m unittest discover -s tests -v
```

## Validation and format reference

Unit tests check exact mask coverage, holes, alpha handling, coordinate orientation, solid volumes, face-plane winding, output structure, and rejection of invalid inputs. The sample map is generated by the same pipeline.

The brush record layout and plane ordering were checked against the [CoD BSP Decompiler's map exporter](https://github.com/kungfooman/CoD-BSP-Decompiler/blob/master/src/map.cpp). The implementation is independent. **An actual load/compile test in your IW3xo Radiant installation has not been performed.** A cube map saved by your editor is a useful fixture if your version needs format adjustments.

Next useful extension: contour tracing and convex decomposition to replace stepped outlines with angled brush sides, followed by a separate curved-patch generator.
