"""Stream an axis-aligned DICOM series into a draft VDB, without loading 3B voxels.

Run with Blender's bundled Python and installed SimpleITK/openvdb dependencies.
This converter is for regular, single-channel, axis-aligned DICOM series only.
It preserves calibrated values and records its endpoint-aligned preview sampling.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/.local/lib/python3.13/site-packages'))
import numpy as np
import SimpleITK as sitk
import openvdb as vdb
from scipy.ndimage import map_coordinates

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('output')
    ap.add_argument('--voxel-size', type=float, default=2.0)
    args = ap.parse_args()
    ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(args.source)
    if len(ids) != 1:
        raise ValueError(f'Expected one series, found {len(ids)}; select a series explicitly.')
    files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(args.source, ids[0])
    headers = []
    for f in files:
        r = sitk.ImageFileReader(); r.SetFileName(f); r.ReadImageInformation()
        if not np.allclose(r.GetDirection(), np.eye(3).ravel(), atol=1e-5):
            raise ValueError('Oblique series requires a general physical-space resampler.')
        headers.append((r.GetSize(), r.GetSpacing(), r.GetOrigin()))
    size, spacing, origin = headers[0]
    positions = np.array([h[2] for h in headers])
    dz = float(np.mean(np.diff(positions[:, 2])))
    if dz <= 0 or not np.allclose(np.diff(positions[:, 2]), dz, atol=1e-4):
        raise ValueError('Non-uniform or reversed slice positions.')
    if not all(h[0] == size and np.allclose(h[1][:2], spacing[:2]) for h in headers):
        raise ValueError('Inconsistent slice dimensions or spacing.')
    if not np.allclose(positions[:, :2], positions[0, :2]):
        raise ValueError('Shifted slices require a general physical-space resampler.')
    source_shape = np.array([size[0], size[1], len(files)])
    source_spacing = np.array([spacing[0], spacing[1], dz])
    target = np.maximum(1, (source_shape * source_spacing / args.voxel_size).astype(int))
    if np.prod(target) > 16000000:
        raise ValueError('Draft converter limited to 16M output voxels; review before upres.')
    # Equivalent axis reversal to DICOMOrient(RAS) for this verified identity-LPS series.
    xs = np.linspace(size[0]-1, 0, target[0])
    ys = np.linspace(size[1]-1, 0, target[1])
    yy, xx = np.meshgrid(ys, xs, indexing='ij')
    coords = np.array([yy, xx])
    result = np.empty(tuple(target), np.float32)
    cache = {}
    for k, z in enumerate(np.linspace(0, len(files)-1, target[2])):
        lo, hi = int(np.floor(z)), min(int(np.floor(z))+1, len(files)-1)
        for i in (lo, hi):
            if i not in cache:
                arr = sitk.GetArrayFromImage(sitk.ReadImage(files[i])).squeeze().astype(np.float32)
                cache[i] = map_coordinates(arr, coords, order=1, mode='nearest', prefilter=False)
        result[:, :, k] = ((1-(z-lo))*cache[lo] + (z-lo)*cache[hi]).T
        cache = {i:a for i,a in cache.items() if i in (lo,hi)}
        if k % 15 == 0:
            print(f'Preview slice {k+1}/{target[2]}', flush=True)
    # Match Bioxel's requested uniform voxel transform; endpoint sampling is recorded.
    affine = np.eye(4)
    affine[:3,:3] *= args.voxel_size
    affine[:3,3] = [-origin[0]-(size[0]-1)*spacing[0], -origin[1]-(size[1]-1)*spacing[1], origin[2]]
    grid = vdb.FloatGrid(); grid.name = 'scan'
    grid.copyFromArray(result)
    grid.transform = vdb.createLinearTransform(affine.T.tolist())
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    vdb.write(str(out), grids=[grid])
    hist, edges = np.histogram(result, bins=64)
    meta = dict(source=args.source, series_id=ids[0], slice_count=len(files), source_shape=source_shape.tolist(),
                source_spacing=source_spacing.tolist(), source_origin=list(origin), output_shape=target.tolist(),
                affine=affine.tolist(), min=float(result.min()), max=float(result.max()),
                sampling='RAS axis reversal; endpoint-aligned trilinear preview; float32; no intensity normalization; no antialias prefilter',
                spatial_policy='Bioxel-compatible uniform output voxel size, not exact source endpoint extent preservation',
                histogram={'counts':hist.tolist(),'edges':edges.tolist()}, reader='SimpleITK '+sitk.Version_VersionString())
    out.with_suffix('.json').write_text(json.dumps(meta, indent=2))
    print(json.dumps({k:meta[k] for k in ['output_shape','min','max','source_spacing']}), flush=True)

if __name__ == '__main__':
    main()
