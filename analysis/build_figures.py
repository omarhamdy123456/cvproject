"""Build the Milestone 1 figures from published RDD2022 counts and local XML.

The class charts use the training-set counts in the data article. The sample
images and the box-geometry chart come from the Czech Republic subset, which
is the portion of the archive stored locally.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from published_stats import (
    CAPTURE,
    CLASS_NAMES,
    CLASSES,
    COUNTRY_ROWS,
    RESOLUTIONS,
    class_totals,
    test_images,
    train_images,
    train_instances,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIG = ROOT / "figures"
CANDIDATES = FIG / "candidates"
SAMPLES = FIG / "samples"

NAVY = "#1B3A4B"
INK = "#1C2830"
MUTED = "#5E6A72"
PAPER = "#F7F4EE"
COLORS = {
    "D00": "#1F4E79",
    "D10": "#C47B2B",
    "D20": "#8C3A3A",
    "D40": "#2F6F5E",
}


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Segoe UI",
            "font.size": 13,
            "axes.titlesize": 16,
            "axes.titleweight": "semibold",
            "axes.labelsize": 13,
            "axes.edgecolor": "#D9D3C8",
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def plot_class_distribution(path: Path) -> None:
    totals = class_totals()
    total = sum(totals.values())
    labels = [f"{code}\n{CLASS_NAMES[code]}" for code in CLASSES]
    values = [totals[code] for code in CLASSES]
    fig, ax = plt.subplots(figsize=(10.4, 5.6), dpi=200)
    bars = ax.bar(labels, values, color=[COLORS[c] for c in CLASSES], width=0.72, zorder=3)
    ax.set_ylabel("Annotated instances in the training set")
    ax.set_title("RDD2022 training set — 55,007 damage instances")
    ax.yaxis.grid(True, linestyle="-", linewidth=0.6, color="#E6E1D8", zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ymax = max(values) * 1.16
    ax.set_ylim(0, ymax)
    for bar, value in zip(bars, values):
        share = value / total
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + ymax * 0.02,
            f"{value:,}\n{share:.1%}",
            ha="center",
            va="bottom",
            fontsize=12,
            color=NAVY,
        )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_country_heatmap(path: Path) -> None:
    matrix = np.array([row[3:] for row in COUNTRY_ROWS], dtype=float)
    countries = [row[0] for row in COUNTRY_ROWS]
    fig, ax = plt.subplots(figsize=(10.6, 6.2), dpi=200)
    im = ax.imshow(matrix, cmap="YlOrBr", aspect="auto")
    ax.set_xticks(range(len(CLASSES)), [f"{c}\n{CLASS_NAMES[c]}" for c in CLASSES])
    ax.set_yticks(range(len(countries)), countries)
    ax.set_title("Training instances by country and damage class")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            color = "white" if value > 4000 else INK
            weight = "bold" if value < 200 else "regular"
            ax.text(j, i, f"{value:,}", ha="center", va="center", color=color, fontsize=11, fontweight=weight)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.ax.set_ylabel("Instances", rotation=90, va="bottom")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _find_czech_root(extracted: Path) -> Path:
    xmls = list(extracted.rglob("*.xml"))
    if not xmls:
        raise FileNotFoundError(f"No XML annotations under {extracted}")
    return extracted


def _parse_xml(path: Path) -> tuple[tuple[int, int], list[dict]]:
    root = ET.parse(path).getroot()
    size = root.find("size")
    width = int(size.findtext("width") or 0)
    height = int(size.findtext("height") or 0)
    objects = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        box = obj.find("bndbox")
        if box is None:
            continue
        xmin = float(box.findtext("xmin") or 0)
        ymin = float(box.findtext("ymin") or 0)
        xmax = float(box.findtext("xmax") or 0)
        ymax = float(box.findtext("ymax") or 0)
        objects.append(
            {
                "name": name,
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
            }
        )
    return (width, height), objects


def _image_for(xml_path: Path) -> Path | None:
    stem = xml_path.stem
    for folder in (
        xml_path.parent,
        xml_path.parent.parent / "images",
        xml_path.parent.parent.parent / "images",
    ):
        for ext in (".jpg", ".jpeg", ".JPG", ".png"):
            candidate = folder / f"{stem}{ext}"
            if candidate.exists():
                return candidate
    matches = list(xml_path.parents[2].rglob(f"{stem}.jpg")) if len(xml_path.parents) > 2 else []
    return matches[0] if matches else None


def audit_czech(extracted: Path) -> dict:
    xml_paths = sorted(extracted.rglob("*.xml"))
    instance_counts: Counter[str] = Counter()
    image_has: Counter[str] = Counter()
    resolutions: Counter[str] = Counter()
    empty = 0
    records = []
    for xml_path in xml_paths:
        (width, height), objects = _parse_xml(xml_path)
        resolutions[f"{width}x{height}"] += 1
        names = [obj["name"] for obj in objects]
        if not names:
            empty += 1
        for name in names:
            instance_counts[name] += 1
        for name in set(names):
            image_has[name] += 1
        image_path = _image_for(xml_path)
        records.append(
            {
                "xml": str(xml_path),
                "image": str(image_path) if image_path else "",
                "width": width,
                "height": height,
                "objects": objects,
            }
        )

    geometry = {code: {"ratios": [], "area_fracs": []} for code in CLASSES}
    for record in records:
        area = record["width"] * record["height"]
        if area <= 0:
            continue
        for obj in record["objects"]:
            if obj["name"] not in geometry:
                continue
            bw = max(obj["xmax"] - obj["xmin"], 1)
            bh = max(obj["ymax"] - obj["ymin"], 1)
            geometry[obj["name"]]["ratios"].append(bw / bh)
            geometry[obj["name"]]["area_fracs"].append((bw * bh) / area)

    geometry_summary = {}
    for code, payload in geometry.items():
        ratios = np.array(payload["ratios"]) if payload["ratios"] else np.array([np.nan])
        areas = np.array(payload["area_fracs"]) if payload["area_fracs"] else np.array([np.nan])
        geometry_summary[code] = {
            "n": int(len(payload["ratios"])),
            "median_width_over_height": None if np.isnan(ratios).all() else round(float(np.median(ratios)), 3),
            "share_wider_than_tall": None if np.isnan(ratios).all() else round(float(np.mean(ratios > 1)), 3),
            "median_box_area_fraction": None if np.isnan(areas).all() else round(float(np.median(areas)), 4),
            "share_under_2_percent": None if np.isnan(areas).all() else round(float(np.mean(areas < 0.02)), 3),
        }

    return {
        "xml_files": len(xml_paths),
        "empty_annotations": empty,
        "instance_counts": dict(instance_counts),
        "images_with_class": dict(image_has),
        "resolutions": dict(resolutions),
        "geometry": geometry_summary,
        "records": records,
    }


def plot_box_geometry(audit: dict, path: Path) -> None:
    ratios = []
    labels = []
    for code in CLASSES:
        item = audit["geometry"][code]
        labels.append(f"{code}\n{CLASS_NAMES[code]}")
        ratios.append(item["median_width_over_height"] or 0)
    fig, ax = plt.subplots(figsize=(10.2, 5.4), dpi=200)
    bars = ax.bar(labels, ratios, color=[COLORS[c] for c in CLASSES], width=0.72, zorder=3)
    ax.axhline(1.0, color=MUTED, linewidth=1, linestyle="--", zorder=2)
    ax.set_ylabel("Median box width / box height")
    ax.set_title("Czech training boxes — orientation by class")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="-", linewidth=0.6, color="#E6E1D8", zorder=0)
    for bar, value in zip(bars, ratios):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.03,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            color=NAVY,
            fontsize=12,
        )
    ax.set_ylim(0, max(ratios) * 1.18)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _draw_record(record: dict, destination: Path) -> None:
    image = Image.open(record["image"]).convert("RGB")
    draw = ImageDraw.Draw(image)
    label_font = _font(18, bold=True)
    for obj in record["objects"]:
        color = COLORS.get(obj["name"], "#222222")
        box = [obj["xmin"], obj["ymin"], obj["xmax"], obj["ymax"]]
        draw.rectangle(box, outline=color, width=3)
        caption = obj["name"]
        text_box = draw.textbbox((0, 0), caption, font=label_font)
        tw, th = text_box[2] - text_box[0], text_box[3] - text_box[1]
        x, y = obj["xmin"], max(0, obj["ymin"] - th - 6)
        draw.rectangle([x, y, x + tw + 8, y + th + 4], fill=color)
        draw.text((x + 4, y + 1), caption, fill="white", font=label_font)
    image.save(destination, quality=92)


# Chosen by eye so each class is visible in a presentation crop.
PINNED_SAMPLES = {
    "D00": "Czech_000279.jpg",
    "D10": "Czech_001494.jpg",
    "D20": "Czech_000803.jpg",
    "D40": "Czech_002634.jpg",
}


# One frame that carries all four classes, used for the input -> output demo.
# Czech_003072 has six boxes covering D00, D10, D20 and D40 on a visible patch of road.
IO_SAMPLE = "Czech_003072.jpg"

# Lowest Laplacian variance over the road region of the Czech training set:
# a heavily motion-blurred underpass frame, used on the challenges slide.
BLUR_SAMPLE = "Czech_002611.jpg"

# Dashboard and windscreen glare occupy the top of every Czech frame.
ROAD_CROP_TOP = 168


def export_samples(audit: dict) -> dict[str, dict]:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    by_name = {Path(record["image"]).name: record for record in audit["records"] if record["image"]}
    chosen = {}
    for code, filename in PINNED_SAMPLES.items():
        record = by_name[filename]
        dest = SAMPLES / f"{code}.jpg"
        _draw_record(record, dest)
        image = Image.open(dest)
        image.crop((0, ROAD_CROP_TOP, image.width, image.height)).save(SAMPLES / f"{code}_road.jpg", quality=92)
        chosen[code] = {
            "slide_image": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "source_image": filename,
            "n_boxes": len(record["objects"]),
        }
    return chosen


def export_io_sample(audit: dict) -> dict:
    """Write the raw frame and its annotated twin for the input/output slide."""
    by_name = {Path(record["image"]).name: record for record in audit["records"] if record["image"]}
    record = by_name[IO_SAMPLE]
    raw = Image.open(record["image"]).convert("RGB")
    crop = (0, ROAD_CROP_TOP, raw.width, raw.height)
    raw.crop(crop).save(SAMPLES / "io_input.jpg", quality=92)
    annotated = SAMPLES / "io_output_full.jpg"
    _draw_record(record, annotated)
    Image.open(annotated).crop(crop).save(SAMPLES / "io_output.jpg", quality=92)
    annotated.unlink()
    boxes = [
        {
            "name": obj["name"],
            "xmin": int(obj["xmin"]),
            "ymin": int(obj["ymin"]),
            "xmax": int(obj["xmax"]),
            "ymax": int(obj["ymax"]),
        }
        for obj in record["objects"]
    ]
    return {
        "source_image": IO_SAMPLE,
        "width": record["width"],
        "height": record["height"],
        "input_image": "figures/samples/io_input.jpg",
        "output_image": "figures/samples/io_output.jpg",
        "boxes": boxes,
    }


def export_blur_sample(audit: dict) -> dict:
    """Write a cropped copy of the blurriest training frame for the challenges slide."""
    by_name = {Path(record["image"]).name: record for record in audit["records"] if record["image"]}
    record = by_name[BLUR_SAMPLE]
    raw = Image.open(record["image"]).convert("RGB")
    # Road strip only: below the glare, above the bonnet, where smeared lane
    # markings make the blur readable in a small thumbnail.
    raw.crop((0, 300, raw.width, 545)).save(SAMPLES / "blur.jpg", quality=92)
    return {
        "source_image": BLUR_SAMPLE,
        "image": "figures/samples/blur.jpg",
        "n_boxes": len(record["objects"]),
    }


def build_sample_grid(path: Path) -> None:
    tiles = []
    for code in CLASSES:
        tile = Image.open(SAMPLES / f"{code}.jpg").convert("RGB")
        tiles.append((code, tile))
    width = max(tile.width for _code, tile in tiles)
    height = max(tile.height for _code, tile in tiles)
    gap = 18
    header = 54
    canvas = Image.new("RGB", (width * 2 + gap * 3, height * 2 + gap * 3 + header), PAPER)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(28, bold=True)
    draw.text((gap, 12), "Czech Republic training images, ground-truth boxes", fill=NAVY, font=title_font)
    label_font = _font(22, bold=True)
    for index, (code, tile) in enumerate(tiles):
        fitted = tile.resize((width, height), Image.Resampling.LANCZOS)
        col, row = index % 2, index // 2
        x = gap + col * (width + gap)
        y = header + gap + row * (height + gap)
        canvas.paste(fitted, (x, y))
        caption = f"{code}  {CLASS_NAMES[code]}"
        draw.rectangle([x, y, x + 360, y + 36], fill=COLORS[code])
        draw.text((x + 10, y + 6), caption, fill="white", font=label_font)
    canvas.save(path, quality=92)


def main() -> None:
    _style()
    FIG.mkdir(parents=True, exist_ok=True)
    plot_class_distribution(FIG / "class_distribution.png")
    plot_country_heatmap(FIG / "class_by_country.png")

    zip_path = RAW / "RDD2022_Czech.zip"
    extracted = RAW / "czech"
    already = extracted.exists() and any(extracted.rglob("*.xml"))
    if zip_path.exists() and not already:
        import zipfile

        extracted.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extracted)

    audit = audit_czech(extracted)
    plot_box_geometry(audit, FIG / "czech_box_geometry.png")
    chosen = export_samples(audit)
    io_sample = export_io_sample(audit)
    blur_sample = export_blur_sample(audit)
    build_sample_grid(FIG / "sample_grid.jpg")

    summary = {
        "source": "Arya et al., RDD2022, training-set counts in Figures 4 and 5",
        "train_images": train_images(),
        "test_images": test_images(),
        "total_images": train_images() + test_images(),
        "train_instances": train_instances(),
        "class_totals": class_totals(),
        "resolutions": RESOLUTIONS,
        "capture": CAPTURE,
        "czech": {
            "xml_files": audit["xml_files"],
            "empty_annotations": audit["empty_annotations"],
            "instance_counts": audit["instance_counts"],
            "images_with_class": audit["images_with_class"],
            "resolutions": audit["resolutions"],
            "geometry": audit["geometry"],
            "samples": chosen,
            "io_sample": io_sample,
            "blur_sample": blur_sample,
        },
    }
    (FIG / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "czech"}, indent=2))
    print(json.dumps(summary["czech"], indent=2))


if __name__ == "__main__":
    main()
