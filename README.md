# SimpleITK Converter v4 for Houdini 21

This Houdini project reads a regular DICOM image series with SimpleITK and converts it into a Houdini volume for viewing and further SOP processing. The project is portable: its scan, Python dependency, and cache are stored beside the HIP file and should be referenced through `$HIP`.

## Preview

![Render](images/1.mp4)
![Render](images/2.mp4)
![Render](images/3.mp4)
![Render](images/4.mp4)
![Volume Slice](images/5.mp4)

## Requirements

- Houdini 21.0 on Windows
- The complete `SimpleITK_Converter.v4` folder kept together
- Enough memory for the selected preview resolution

SimpleITK 2.5.5 for Houdini's Python 3.11 is already included in the `dependencies` folder. A separate Python installation is not required.

## Folder layout

```text
SimpleITK_Converter.v4/
├── SimpleITK_Converter.v4.hip
├── dependencies/               SimpleITK for Houdini Python 3.11
├── scan/                       DICOM source images
├── cache/
│   └── dicom_reader/           Persistent Houdini .bgeo.sc previews
├── scripts/                    Reference conversion script
└── backup/                     Earlier HIP backups
```

`$HIP` means the folder containing the open HIP file. Keep the HIP inside this folder so paths such as `$HIP/scan`, `$HIP/dependencies`, and `$HIP/cache/dicom_reader` continue to work.

## Quick start

1. Open `SimpleITK_Converter.v4.hip` in Houdini 21.
2. At `/obj`, make sure the blue display flag is enabled on `SimpleITK_Viewer`.
3. Enter `SimpleITK_Viewer` and select `read_dicom_SimpleITK_Converter`.
4. Keep **Force Rebuild** off for normal use. The included `.bgeo.sc` preview should load from the cache.
5. Display the desired output node. `OUT_volume` is the volume-viewing output; `OUT_polygon` is the polygon-processing output when that branch is needed.
6. Press `G` in the Scene View to frame the displayed result if it is outside the current camera view.

## DICOM Import controls

The Python SOP `read_dicom_SimpleITK_Converter` contains the visible conversion code and these controls:

| Control | Purpose | Recommended/default value |
| --- | --- | --- |
| **Source Folder** | Folder containing one spatial DICOM series | A folder under `$HIP/scan` |
| **Series UID** | Selects a series when the folder contains more than one | Leave empty when the folder contains exactly one series |
| **Preview Voxel Spacing** | Uniform output voxel size; larger values produce a lighter preview | `2.0` |
| **Interpolation** | Sampling method | `Trilinear` for smooth scalar scans; `Nearest` for label-like data |
| **Max Output Voxels** | Safety limit for preview allocation | `16000000` |
| **Field Name** | Name assigned to the Houdini volume primitive | `scan` |
| **Dependencies** | Location of the bundled SimpleITK package | `$HIP/dependencies` |
| **Cache Directory** | Persistent geometry-cache location | `$HIP/cache/dicom_reader` |
| **Force Rebuild** | Ignores the matching cache and rereads the DICOM files | Off during normal use |

## Cache behavior

The converter builds a cache key from the source path, series UID, preview spacing, interpolation mode, voxel limit, and field name. A matching cache is loaded directly from:

```text
$HIP/cache/dicom_reader/dicom_preview_<key>.bgeo.sc
```

Cache files are written through a temporary file and published only after the DICOM conversion finishes. An interrupted conversion therefore should not replace a valid cache with a partial file.

To rebuild the preview:

1. Enable **Force Rebuild**.
2. Allow the Python SOP to finish cooking. The included scan has 993 slices, so the first conversion can take some time.
3. Disable **Force Rebuild** after the cache is written.
4. Save the HIP file.

Leaving **Force Rebuild** enabled makes Houdini reread the full DICOM series whenever the SOP recooks.

## Using a different DICOM series

1. Copy the new DICOM files into their own folder under `$HIP/scan`.
2. Set **Source Folder** to that folder. Use a `$HIP` path when possible.
3. Leave **Series UID** empty if the folder contains one series. If Houdini reports multiple series, enter the required UID.
4. Start with **Preview Voxel Spacing** at `2.0` or higher.
5. Enable **Force Rebuild** and wait for the cook to finish.
6. Disable **Force Rebuild** and save.

The reader is intended for a regular, axis-aligned, single-channel, static DICOM series. It rejects oblique orientation, shifted slices, nonuniform or reversed slice spacing, color/vector images, and series with fewer than two slices. Those cases require a general physical-space resampling workflow.

## Finding CT data

You can find medical and other CT datasets through the [Medical Imaging Datasets collection](https://github.com/sfikas/medical-imaging-datasets).

The typewriter CT scan included with this project came from [MorphoSource media 000509681](https://www.morphosource.org/concern/media/000509681?locale=en).

Before downloading or redistributing a dataset, review its license, attribution requirements, access terms, and any restrictions on medical or sensitive data.

## Output and metadata

The reader produces one native Houdini Volume and preserves calibrated scalar values without intensity normalization. It adds these detail attributes:

- `source_path`
- `source_metadata`
- `source_resolution`
- `source_spacing`
- `data_range`
- `field_role`

Inspect them in the Geometry Spreadsheet using the **Detail** view. `source_metadata` contains JSON describing the source series, preview dimensions, spacing, origin, interpolation, scalar range, DICOM tags, and reader version.

## Troubleshooting

### Nothing appears in the viewport

- At `/obj`, enable the blue display flag on `SimpleITK_Viewer`.
- Inside the Geometry object, enable the blue flag on the output you want to view.
- Press `G` over the Scene View to frame the geometry.
- Check whether the cook was interrupted. If it was, either let one rebuild finish or turn **Force Rebuild** off to use the existing cache.

### `SimpleITK unavailable`

Set **Dependencies** to:

```text
$HIP/dependencies
```

Keep the supplied `dependencies` folder beside the HIP file.

### `No DICOM series found`

Set **Source Folder** to the directory that directly contains the `.dcm` files, rather than to a higher-level parent directory.

### Multiple series are found

Enter the desired DICOM series identifier in **Series UID**, or separate each series into its own source folder.

### Output exceeds Max Output Voxels

Increase **Preview Voxel Spacing** to reduce the preview resolution. Increase **Max Output Voxels** only after checking available memory.

### A setting changed but the old result remains

Most conversion settings create a different keyed cache automatically. If source files were replaced in place without changing the source path, enable **Force Rebuild** once.

## Moving the project

Move or copy the whole `SimpleITK_Converter.v4` folder. Do not move only the HIP file. Keeping the folder structure intact preserves all `$HIP`-relative scan, dependency, and cache paths.

