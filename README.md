# Prefab Drop — Image → Radiant

A local Windows app for CoD4 / IW3xo Radiant: image silhouettes become brushes, object images become textured mesh patches, and custom textures get packaged for the game.

## Install and launch

Requirements:

- Windows with Windows PowerShell 5.1 / WPF.
- Standard Windows **Python 3.14**, installed from python.org (MSYS2/MinGW Python is unsupported).
- CoD4 plus the original Mod Tools for material conversion and fastfile builds.

From a PowerShell terminal in the repository:

```powershell
.\scripts\Setup.ps1
.\Launch.cmd
```

Setup creates `.venv` and installs the app in editable mode. You can also double-click `Launch.cmd`. Select your **CoD4 Mod Tools folder** in the app—the folder containing `bin/converter.exe` and `bin/linker_pc.exe`.

Folder choices and settings are local in `preferences.json`. Logs and backups are under `.prefabdrop/logs`. Neither is committed. The UI runs queued jobs in the background; close it after the queue finishes.

## Choose a workflow

| Tab | Input | Result |
| --- | --- | --- |
| Prefabs | Silhouette or transparent PNG | Extruded `.map` brushes, optionally textured |
| Single texture | One image | Compiled CoD4 material and `.iwi` |
| 3D asset | One isolated object image | Textured patch `.map`, OBJ/MTL/textures and GLB |
| Build & package | Existing map BSP and zone CSV | Fastfiles and an image `.iwd` in `usermaps` |

### Image → brush prefab

1. Choose an **existing prefab destination folder**, such as your game's `map_source/prefabs/ai`.
2. Choose the mask: **Dark pixels**, **Light pixels**, or **PNG transparency**. Drop `examples/honeycomb.png` for a first test.
3. Set depth and orientation. **Floor** places the image in XY and extrudes upward; **Wall** places it in XZ and extrudes along Y.
4. Drop the image. The app starts automatically and reports the saved path/material at the bottom.
5. Import the `.map` into Radiant. Duplicate filenames receive a numeric suffix instead of overwriting prior work.

Under **Size and detail**, the default 96 cells × 4 units gives a 384-unit longest edge, including image margins. More cells preserve detail but increase brush counts. This is grid extrusion: diagonal edges are stepped. The rectangle optimization preserves the occupied cells and holes.

### Import a single texture

Drop an image into **Single texture**, optionally giving it a label. The returned material name starts with `pd_` and includes a content hash. Use **Copy material name**, reload textures or restart Radiant, and search under **Generic / floor**. Do not add a `textures/` prefix.

The importer creates an opaque metal world material, flattens transparency onto dark grey, and resizes the colour image to power-of-two dimensions up to 1024 pixels per axis. It does not generate normal or specular maps. Source assets go into `texture_assets` and `source_data`; compiled assets go into `raw/materials`, `raw/images`, and `raw/material_properties`.

### Image → 3D patch prefab (optional)

**Powered by Stability AI.** Stable Fast 3D reconstructs a single object, not an entire playable scene.

Additional requirements: standard Windows **Python 3.11**, an NVIDIA CUDA GPU, Visual Studio 2022 Build Tools with **Desktop development with C++**, and a CUDA Toolkit supported by `scripts/Setup-SF3D.ps1`. The tested local machine uses an RTX 3060 12 GB and CUDA 13.0. Setup currently recognizes CUDA 13.0, 12.8, 12.6 and 12.4; other combinations have not been validated.

1. Sign into [Hugging Face](https://huggingface.co/stabilityai/stable-fast-3d) and accept/request the model's gated access. Creating an account alone does not grant model access.
2. Install the separate model environment:

   ```powershell
   .\scripts\Setup-SF3D.ps1
   .\.venv-sf3d\Scripts\huggingface-cli.exe login
   ```

3. Create a Read token in your Hugging Face account and paste it **only into the interactive login prompt**. Do not put it in a script, README, screenshot, Git URL, or commit. Decline adding it as a Git credential. The account used for the token must have model access.
4. In **3D asset**, select an existing output folder, choose the longest edge in Radiant units, and drop an image with one clearly separated object.

Setup downloads upstream source into ignored `tools/stable-fast-3d` and dependencies into `.venv-sf3d`. Model weights download on first use into the Hugging Face cache. Images are processed locally. Downloads and first inference can take time; inspect logs if a job fails.

Default remeshing targets 1,500 vertices. Each output triangle becomes one mesh patch, so this is not a 1,500-patch guarantee. Keep counts modest and test collision in your map. Geometry is centred in X/Y, grounded at Z=0 and fitted to the requested longest edge. Source OBJ/GLB assets are saved beside the prefab in a `_source` folder. Texture UVs and planar lightmap coordinates are exported separately.

### Build fastfiles and package textures

1. Save your map in Radiant and **compile its BSP and lighting first**. This app's build tab does not perform those steps.
2. Open **Build & package** and choose the map, such as `mp_echo_first`.
3. Select a folder of compiled IWI images; `raw/images` is the default. All IWI files beneath that folder are included, preserving subfolders. Use a dedicated folder to make a smaller release archive; this is not automatic dependency discovery.
4. Click **Build fastfiles + bundle textures**. It uses `raw/maps/mp/<map>.d3dbsp` and your existing `zone_source/<map>.csv`, and builds `<map>_load.ff` when its CSV exists. Existing CSVs are preserved; English assets are used.
5. Restart CoD4, then enter `devmap mp_echo_first` (substitute your map name).

Outputs go to `usermaps/<map>/`: `<map>.ff`, optional `<map>_load.ff`, and `<map>_prefabdrop.iwd`. Previous outputs are backed up under the build log directory. Other usermap archives are preserved. **Bundle textures only** updates the IWD without rebuilding fastfiles.

An **IWI is one texture**. An **IWD is a ZIP archive** with entries such as `images/pd_example.iwi`. Naming a ZIP `.iwi` will not make it load. Loose files in `raw` are for the tools; the game needs the packaged files. A successful build is not a substitute for testing your complete map in game.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Drop appears to do nothing | Read the status line; select an existing destination folder and valid Mod Tools installation. |
| Hugging Face 403 | Accept the model access conditions using the token's account; check its gated-model read permissions. |
| Python/Pillow install fails | Use standard python.org Windows Python, not MinGW/MSYS2. Run `scripts/Setup.ps1`. |
| Texture missing in Radiant | Reload textures and search for the exact `pd_` material under Generic / floor. |
| Texture missing in devmap | Rebuild/package, verify `.iwd` with `images/` entries, and restart the game. |
| Lightmap coordinates do not change | Replace older generated prefabs with a fresh export; copies embedded in a map do not update automatically. |
| Backwards tree volume compiling a prefab alone | Place it in a real map with structural brushes; a patch-only prefab is not a complete level. |
| Fastfile build fails | Open `.prefabdrop/logs/build-*`; verify the BSP, zone CSV and referenced assets exist. |

## Development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m prefabdrop.app examples/honeycomb.png -o example.map --preview example.png
powershell -NoProfile -STA -File ui/PrefabDrop.ps1 -SmokeTest
.\.venv\Scripts\python.exe scripts/check_repository.py
```

The CLI also exposes the older Tk preview interface when run without an image. The native WPF app is the primary interface.

```text
src/prefabdrop/    Python conversion, model bridge and packaging code
ui/               Native PowerShell/WPF interface
scripts/          Setup, example generation and repository checks
tests/            Geometry, material, model pipeline and packaging tests
examples/         Small checked-in sample image and prefab
docs/             Project notes and UI reference image
LICENSES/         Third-party licence text
```

Tests cover geometry/UVs/lightmaps, material failures, model worker orchestration, archive layout and failed-build recovery. The repaired hand and ZWA patch prefabs were compiled with `cod4map` in structural test rooms; `mp_echo_first` was built and packaged with the installed linker. GPU inference, Radiant rendering and complete in-game behaviour are not covered by unit tests.

## Credentials, downloads and model licence

`.gitignore` excludes local scripts such as `exec.ps1`, `.env` files, saved tokens, environments, caches, model source/weights, logs and compiled game assets. Gitignore does **not** untrack previously committed files or guarantee arbitrary text contains no secrets. The repository check inspects the Git index for common credential patterns, forbidden outputs and files over 5 MiB; CI runs the same check. Never force-add local credentials. Rotate a credential if it was ever published.

Enable the local commit guard after cloning:

```powershell
git config core.hooksPath .githooks
```

Stable Fast 3D is separately downloaded and governed by the [Stability AI Community License](LICENSES/Stability-AI-Community-License.md); see [NOTICE](NOTICE). We do not include its source or weights. Hobby use is free. Commercial use requires registration and is subject to the licence's total-revenue threshold (US $1 million), attribution and acceptable-use terms. Review the full agreement before commercial deployment. Output ownership is subject to applicable law and does not clear third-party rights in source images. This notice does not place the independently written application code under the model licence.
