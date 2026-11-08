"""Convert RDD2022 Pascal VOC XML boxes into YOLO detection labels.

Each output line is: class_id x_center y_center width height
with the four numbers normalized by the image width and height.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

CLASS_TO_ID = {"D00": 0, "D10": 1, "D20": 2, "D40": 3}


def yolo_lines(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    width = float(size.findtext("width"))
    height = float(size.findtext("height"))
    lines = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        if name not in CLASS_TO_ID:
            continue
        box = obj.find("bndbox")
        xmin = float(box.findtext("xmin"))
        ymin = float(box.findtext("ymin"))
        xmax = float(box.findtext("xmax"))
        ymax = float(box.findtext("ymax"))
        lines.append(
            f"{CLASS_TO_ID[name]} "
            f"{((xmin + xmax) / 2) / width:.6f} "
            f"{((ymin + ymax) / 2) / height:.6f} "
            f"{(xmax - xmin) / width:.6f} "
            f"{(ymax - ymin) / height:.6f}"
        )
    return lines


def convert_tree(xml_root: Path, label_root: Path) -> tuple[int, int]:
    files = 0
    boxes = 0
    for xml_path in sorted(xml_root.rglob("*.xml")):
        lines = yolo_lines(xml_path)
        destination = label_root / f"{xml_path.stem}.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        files += 1
        boxes += len(lines)
    return files, boxes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml_root", type=Path)
    parser.add_argument("label_root", type=Path)
    args = parser.parse_args()
    files, boxes = convert_tree(args.xml_root, args.label_root)
    print(f"{files} files, {boxes} boxes")


if __name__ == "__main__":
    main()
