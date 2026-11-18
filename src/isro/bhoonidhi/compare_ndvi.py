from pathlib import Path
import csv
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform
import matplotlib.pyplot as plt

ROOT = Path("data/satellite_experiments")
OUTPUT = ROOT / "comparison"
OUTPUT.mkdir(parents=True, exist_ok=True)

LAT = 13.294219
LON = 78.624294

SCENES = {
    "2026-10-07": ROOT / "resourcesat2a_20261007",
    "2026-10-31": ROOT / "resourcesat2a_20261031",
}

SIZES = (1, 3, 5, 9)
results = []

def calculate_ndvi(folder, size):
    red_path = next(folder.rglob("BAND3.tif"))
    nir_path = next(folder.rglob("BAND4.tif"))

    with rasterio.open(red_path) as red_src, \
         rasterio.open(nir_path) as nir_src:

        if (red_src.crs != nir_src.crs or
            red_src.transform != nir_src.transform or
            red_src.shape != nir_src.shape):
            raise ValueError("Red and NIR rasters are not aligned")

        xs, ys = transform(
            "EPSG:4326", red_src.crs,
            [LON], [LAT]
        )

        row, col = red_src.index(xs[0], ys[0])
        half = size // 2

        window = Window(
            col - half,
            row - half,
            size,
            size
        )

        if (
            window.col_off < 0 or
            window.row_off < 0 or
            window.col_off + size > red_src.width or
            window.row_off + size > red_src.height
        ):
            raise ValueError("AOI extends beyond the raster")

        red = red_src.read(
            1, window=window, masked=True
        ).astype("float32").filled(np.nan)

        nir = nir_src.read(
            1, window=window, masked=True
        ).astype("float32").filled(np.nan)

        denominator = nir + red

        ndvi = np.full(red.shape, np.nan, dtype="float32")

        valid = (
            np.isfinite(red) &
            np.isfinite(nir) &
            (red > 0) &
            (nir > 0) &
            (denominator != 0)
        )

        np.divide(
            nir - red,
            denominator,
            out=ndvi,
            where=valid
        )

        ndvi[~valid] = np.nan

        pixels = ndvi[np.isfinite(ndvi)]
        total = size * size

        return {
            "mean": float(pixels.mean()) if pixels.size else np.nan,
            "minimum": float(pixels.min()) if pixels.size else np.nan,
            "maximum": float(pixels.max()) if pixels.size else np.nan,
            "std": float(pixels.std()) if pixels.size else np.nan,
            "valid_pixels": int(pixels.size),
            "total_pixels": total,
        }

for date, folder in SCENES.items():
    print(f"\nSCENE: {date}")

    if not folder.exists():
        raise FileNotFoundError(folder)

    for size in SIZES:
        stats = calculate_ndvi(folder, size)

        result = {
            "date": date,
            "window": f"{size}x{size}",
            **stats,
        }
        results.append(result)

        print(
            f"{size}x{size}: "
            f"mean={stats['mean']:.4f} "
            f"min={stats['minimum']:.4f} "
            f"max={stats['maximum']:.4f} "
            f"valid={stats['valid_pixels']}/{stats['total_pixels']}"
        )

csv_path = OUTPUT / "resourcesat_ndvi_aoi_comparison.csv"

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

fig, ax = plt.subplots(figsize=(9, 5))

labels = [f"{s}x{s}" for s in SIZES]
positions = np.arange(len(SIZES))

for i, date in enumerate(SCENES):
    values = [
        next(
            r["mean"] for r in results
            if r["date"] == date and r["window"] == label
        )
        for label in labels
    ]

    ax.bar(
        positions + (i - 0.5) * 0.36,
        values,
        width=0.36,
        label=date
    )

ax.set_xticks(positions, labels)
ax.set_ylabel("Mean raw-band NDVI")
ax.set_xlabel("Sampling window")
ax.set_title("MangoTwin | Resourcesat-2A NDVI Comparison")
ax.legend()
ax.grid(axis="y", alpha=0.2)

plt.tight_layout()

chart_path = OUTPUT / "resourcesat_ndvi_aoi_comparison.png"
plt.savefig(chart_path, dpi=180)
plt.close()

print("\nComparison CSV:", csv_path)
print("Comparison chart:", chart_path)

for size in SIZES:
    label = f"{size}x{size}"

    earlier = next(
        r["mean"] for r in results
        if r["date"] == "2026-10-07" and r["window"] == label
    )

    later = next(
        r["mean"] for r in results
        if r["date"] == "2026-10-31" and r["window"] == label
    )

    print(
        f"Change for {label}: "
        f"{later - earlier:+.4f} NDVI units"
    )

print("\nNOTE: Uncalibrated exploratory NDVI, not validated surface reflectance.")
print("Cloud masking and radiometric calibration are still required.")
