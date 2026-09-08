# Radiant Automation notes

Repository: https://github.com/9aj/radiant-image-to-prefab

Reference supplied by the user: https://github.com/AFirstTimeMapMaker/ObjToCODMap/tree/master
Keep this as a reference for future CoD map and mesh export work. Its implementation has not yet been reviewed.

## Material integration

- CoD4 installation: `C:\Code\Cod4\Call of Duty 4`.
- Run `bin/converter.exe -nopause -single material <name>` with working directory `bin`. Absolute `-gamedir` produced doubled paths on the installed build.
- Verify compiled material, IWI image, and `raw/material_properties/<name>`. Exit code zero alone is insufficient.
- Use the plain material name in maps. The earlier proposed `textures/` prefix was unsupported and must not be added without evidence.
- The installed `deffiles/materials/locale.txt` lists `case`, `test`, `tools`, `decal`, `Middle East`, `Chechnya`, and `Generic`. Initial generated assets used `locale_Industrial`, which is absent from that list. The importer now uses `locale_Generic`.
- `pd_honeycomb_e04b7ea18f3d` was recompiled with Generic for an editor visibility test. Its actual appearance in the running Radiant browser still needs user confirmation.
- Auto texture currently imports the source colour image as an opaque metal world material and assigns it to all faces. It does not synthesize normal/specular maps or reconstruct textures from perspective concepts.
