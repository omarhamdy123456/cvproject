"""Build the DMET 901 Milestone 1 slide deck from the figures and the audit."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
OUT = ROOT / "slides" / "DMET901_Milestone1_RoadDamage.pptx"

NAVY = "1B3A4B"
INK = "1C2830"
MUTED = "5C6B73"
GOLD = "A68456"
PAPER = "F7F4EE"
WHITE = "FFFFFF"
CARD = "FFFCF8"
LINE = "E4DDD2"
SOFT = "E7F0EA"

TOTAL = 11


def rgb(value: str) -> RGBColor:
    value = value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _anchor(text_frame, anchor: str) -> None:
    values = {"top": "t", "middle": "ctr", "bottom": "b"}
    text_frame._txBody.bodyPr.set("anchor", values[anchor])


def add_rect(slide, left, top, width, height, fill, line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1)
    # Keep rectangles from inheriting a shadow.
    sp_pr = shape.fill._xPr.getparent()
    effect = sp_pr.find(qn("a:effectLst"))
    if effect is not None:
        sp_pr.remove(effect)
    return shape


def add_text(
    slide,
    left,
    top,
    width,
    height,
    text,
    size,
    color,
    bold=False,
    align="left",
    anchor="top",
    spacing=0,
):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = Emu(0)
    frame.margin_right = Emu(0)
    frame.margin_top = Emu(0)
    frame.margin_bottom = Emu(0)
    _anchor(frame, anchor)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
    paragraph.space_after = Pt(spacing)
    run = paragraph.add_run()
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    return box


def add_lines(slide, left, top, width, height, lines, size=18, color=INK, spacing=10, bold=False):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = Emu(0)
    frame.margin_right = Emu(0)
    frame.margin_top = Emu(0)
    frame.margin_bottom = Emu(0)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.space_after = Pt(spacing)
        paragraph.line_spacing = 1.05
        run = paragraph.add_run()
        run.text = line
        run.font.name = "Calibri"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)
    return box


def notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


def footer(slide, number: int) -> None:
    add_rect(slide, 0, 7.22, 13.333, 0.28, NAVY)
    add_text(
        slide,
        0.42,
        7.22,
        9.5,
        0.28,
        "DMET 901   ·   Milestone 1   ·   Road damage detection",
        12,
        WHITE,
        anchor="middle",
    )
    add_text(
        slide,
        10.6,
        7.22,
        2.3,
        0.28,
        f"{number}   /   {TOTAL}",
        12,
        WHITE,
        align="right",
        anchor="middle",
    )


def new_slide(prs, kicker: str, title: str, number: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, 13.333, 7.5, PAPER)
    add_rect(slide, 0, 0, 0.08, 7.5, NAVY)
    add_text(slide, 0.42, 0.18, 12.4, 0.26, kicker.upper(), 12, GOLD, bold=True)
    add_text(slide, 0.42, 0.40, 12.4, 0.55, title, 26, NAVY, bold=True)
    footer(slide, number)
    return slide


def load_summary() -> dict:
    return json.loads((FIG / "summary.json").read_text(encoding="utf-8"))


def build() -> Path:
    summary = load_summary()
    czech = summary["czech"]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    prs.core_properties.title = "DMET 901 Milestone 1 — Road damage detection"
    prs.core_properties.subject = "Computer Vision"
    prs.core_properties.category = "Milestone 1"

    title_slide(prs)
    problem_slide(prs)
    motivation_slide(prs)
    composition_slide(prs)
    sample_slide(prs, czech)
    distribution_slide(prs)
    challenges_slide(prs, czech)
    justification_slide(prs)
    training_slide(prs, czech)
    tools_slide(prs)
    references_slide(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    return OUT


def title_slide(prs) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, 13.333, 7.5, NAVY)
    add_rect(slide, 0, 0, 0.16, 7.5, GOLD)
    add_text(slide, 0.7, 0.42, 11, 0.3, "GERMAN UNIVERSITY IN CAIRO", 14, GOLD, bold=True)
    add_text(slide, 0.7, 0.72, 11, 0.3, "Media Engineering and Technology    ·    Dr. Mohamed Karam", 16, "D5E2E8")
    add_text(slide, 0.7, 1.55, 11.5, 0.35, "DMET 901  —  COMPUTER VISION", 18, GOLD, bold=True)
    add_text(slide, 0.7, 2.05, 11.8, 1.7, "Detecting road damage\nin a single camera frame", 44, WHITE, bold=True)
    add_text(
        slide,
        0.7,
        4.15,
        10.5,
        0.7,
        "Milestone 1    ·    Object detection on RDD2022, starting from YOLOv8s",
        20,
        "E7D7C3",
    )
    add_rect(slide, 0.7, 5.15, 2.2, 0.045, GOLD)
    add_text(slide, 0.7, 5.4, 8, 0.35, "Presenter:  your name", 18, WHITE)
    add_text(slide, 0.7, 6.55, 10, 0.3, "26 September 2026", 16, "D5E2E8")
    notes(
        slide,
        "Open with the task in one sentence: one road photo in, a set of boxes out, four kinds of damage. "
        "Say that Milestone 1 fixes the problem, the dataset, and the starting model, and that the rest of the talk defends those three choices. "
        "Put your name on this slide before you present.",
    )


def problem_slide(prs) -> None:
    slide = new_slide(prs, "3.1  Problem", "One frame in, damage boxes out", 2)
    rows = [
        (
            "Task",
            "Object detection. In one road image, find every longitudinal crack, transverse crack, alligator crack, and pothole, and return each as a bounding box.",
            1.45,
            18,
        ),
        ("Input", "One RGB image", 1.15, 22),
        (
            "Output",
            "Each damaged part of the road, marked with a box and its type: longitudinal crack, transverse crack, alligator crack, or pothole.",
            1.55,
            18,
        ),
    ]
    top = 1.4
    for heading, body, height, size in rows:
        add_rect(slide, 0.42, top, 2.15, height, NAVY)
        add_text(slide, 0.52, top, 1.95, height, heading, 18, WHITE, bold=True, align="center", anchor="middle")
        add_rect(slide, 2.57, top, 10.3, height, CARD, LINE)
        add_text(slide, 2.9, top, 9.7, height, body, size, INK, anchor="middle")
        top += height + 0.1
    notes(
        slide,
        "Be precise if someone asks about video. This milestone detects damage in one frame. "
        "A clean road is a valid output: the set of boxes can be empty. "
        "Pixel masks and a severity grade are outside this task, because the labels do not contain them.",
    )


def motivation_slide(prs) -> None:
    slide = new_slide(prs, "3.1", "Motivation", 3)
    rows = [
        ("Feature", "A camera in the car finds damaged parts of the road ahead.", 1.35, 20),
        ("Driver", "The driver is warned in time to steer around them.", 1.35, 20),
        ("Result", "The car avoids the damage instead of hitting it.", 1.35, 20),
    ]
    top = 1.45
    for heading, body, height, size in rows:
        add_rect(slide, 0.42, top, 2.15, height, NAVY)
        add_text(slide, 0.52, top, 1.95, height, heading, 18, WHITE, bold=True, align="center", anchor="middle")
        add_rect(slide, 2.57, top, 10.3, height, CARD, LINE)
        add_text(slide, 2.9, top, 9.7, height, body, size, INK, anchor="middle")
        top += height + 0.28
    notes(
        slide,
        "This is a driver-assistance feature, not a repair schedule. "
        "The camera sees the damage early. The driver steers around it and does not hit it. "
        "Mention Cairo as the place you would want to deploy this. RDD2022 has no Egyptian roads.",
    )


def composition_slide(prs) -> None:
    slide = new_slide(prs, "3.2  Dataset", "RDD2022", 4)
    add_text(
        slide,
        0.45,
        1.02,
        12.4,
        0.28,
        "Source: Arya et al. 2024, Figshare  ·  License: CC BY 4.0  ·  Files: JPEG and XML",
        14,
        MUTED,
    )
    headers = ["Country", "Train", "Test", "Resolution", "Camera"]
    rows = [
        ["Japan", "10,506", "2,627", "600 × 600", "Phone on a car"],
        ["India", "7,706", "1,959", "720 × 720", "Phone on a car"],
        ["Czech Republic", "2,829", "709", "600 × 600", "Phone on a car"],
        ["Norway", "8,161", "2,040", "3650 × 2044", "Two survey cameras"],
        ["United States", "4,805", "1,200", "640 × 640", "Street View"],
        ["China, motorbike", "1,977", "500", "512 × 512", "Motorbike, ~30 km/h"],
        ["China, drone", "2,401", "0", "512 × 512", "Drone, top-down"],
        ["Total", "38,385", "9,035", "JPEG + XML", "47,420 images"],
    ]
    widths = [2.5, 1.45, 1.35, 2.15, 4.55]
    left0 = 0.42
    top = 1.38
    row_h = 0.55
    x = left0
    for width, header in zip(widths, headers):
        add_rect(slide, x, top, width, row_h, NAVY)
        add_text(slide, x + 0.1, top, width - 0.16, row_h, header, 14, WHITE, bold=True, anchor="middle")
        x += width
    for r, row in enumerate(rows):
        y = top + (r + 1) * row_h
        fill = "E7EEF2" if r == len(rows) - 1 else (WHITE if r % 2 == 0 else "F3F0EA")
        x = left0
        for c, (width, value) in enumerate(zip(widths, row)):
            add_rect(slide, x, y, width, row_h, fill, LINE)
            add_text(
                slide,
                x + 0.1,
                y,
                width - 0.16,
                row_h,
                value,
                14,
                NAVY if r == len(rows) - 1 else INK,
                bold=(c == 0 or r == len(rows) - 1),
                anchor="middle",
            )
            x += width
    notes(
        slide,
        "CC BY 4.0 means the images can be used in this course as long as Arya et al. are cited. The full archive is 12.36 GB. "
        "These counts are Figure 4 of that paper. India was shot at 960 by 720 and resized to 720 by 720. "
        "China drone images are training only. Files are JPEG. Training labels are XML. Test images have no public XML.",
    )


def sample_slide(prs, czech: dict) -> None:
    slide = new_slide(prs, "3.2  Dataset", "Four classes, one image each", 5)
    add_text(
        slide,
        0.45,
        1.08,
        12.4,
        0.36,
        "Ground truth: a class and a box, in Pascal VOC XML. No mask and no severity.",
        13,
        MUTED,
    )
    order = ["D00", "D10", "D20", "D40"]
    names = {
        "D00": "Longitudinal crack",
        "D10": "Transverse crack",
        "D20": "Alligator crack",
        "D40": "Pothole",
    }
    for index, code in enumerate(order):
        col, row = index % 2, index // 2
        left = 0.42 + col * 6.45
        top = 1.5 + row * 2.8
        path = ROOT / "figures" / "samples" / f"{code}_road.jpg"
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), Inches(3.54), Inches(2.55))
        add_text(slide, left + 3.7, top + 0.7, 2.5, 0.45, code, 22, NAVY, bold=True)
        add_text(slide, left + 3.7, top + 1.25, 2.5, 0.7, names[code], 16, INK)
    notes(
        slide,
        "These are training images from the Czech zip, not diagrams. The rectangles are the dataset boxes, not model predictions. "
        "Point out that a crack is a thin mark inside a much larger rectangle. That is why a high IoU is a hard target. "
        "Filenames: "
        + ", ".join(czech["samples"][code]["source_image"] for code in order)
        + ".",
    )


def distribution_slide(prs) -> None:
    slide = new_slide(prs, "3.2  Dataset", "D00 is 47% of the boxes", 6)
    slide.shapes.add_picture(str(FIG / "class_distribution.png"), Inches(0.3), Inches(1.15), Inches(8.3), Inches(5.7))
    add_rect(slide, 8.7, 1.4, 4.2, 5.2, CARD, LINE)
    add_lines(
        slide,
        8.95,
        1.65,
        3.75,
        4.7,
        [
            "55,007 training boxes. 4 classes.",
            "D00 longitudinal — 26,016",
            "D10 transverse — 11,830",
            "D20 alligator — 10,617",
            "D40 pothole — 6,544",
        ],
        size=15,
        spacing=12,
    )
    notes(
        slide,
        "The chart is the training split only. Test labels were not released, so they are not in this plot. "
        "Read the four numbers. Then say you will report per-class AP later, because the average will be pulled by D00. "
        "The counts are Figure 5 of Arya et al. The country rows sum to 55,007, which matches Figure 4.",
    )


def challenges_slide(prs, czech: dict) -> None:
    slide = new_slide(prs, "3.2  Dataset", "What will make the detector fail", 7)
    geo = czech["geometry"]
    pothole_area = geo["D40"]["median_box_area_fraction"] * 100
    items = [
        ("Class imbalance", "D00 is 47% of the boxes."),
        ("Small objects", f"A typical pothole is {pothole_area:.1f}% of the frame."),
        ("Occlusion", "Vehicles and shadows cover the pavement."),
        ("Motion blur", "Cars and motorbikes are moving."),
        ("Lighting", "Sun, shade, wet pavement, and snow."),
        ("Domain shift", "Six countries and five camera types."),
        ("Label noise", "Crack edges are a judgment."),
        ("Duplicate images", "Neighboring frames repeat the same road."),
    ]
    for index, (heading, body) in enumerate(items):
        col, row = index % 2, index // 2
        left = 0.42 + col * 6.4
        top = 1.15 + row * 1.45
        add_rect(slide, left, top, 6.15, 1.32, CARD, LINE)
        add_rect(slide, left, top, 0.08, 1.32, GOLD)
        add_text(slide, left + 0.28, top + 0.16, 5.7, 0.38, heading, 18, NAVY, bold=True)
        add_text(slide, left + 0.28, top + 0.64, 5.7, 0.52, body, 15, INK)
    notes(
        slide,
        "India has thousands of potholes and only 68 transverse cracks. The United States is the reverse. Validate inside each country, or a pooled model hides that. "
        "The 53% figure is filename adjacency in the Czech training set, which is evidence of repeated road, not a pixel-duplicate count. The split still has to keep a sequence together. "
        "The Japan-to-India drop is the finding in Arya et al. that motivated RDD2020 and then RDD2022. "
        "Occlusion is part of capture conditions: vehicles, shadows, and lane paint sit on top of the pavement.",
    )


def justification_slide(prs) -> None:
    slide = new_slide(prs, "3.2  Dataset", "Justification", 8)
    rows = [
        ("Fits", "Same task: one RGB image, and a box for each of the four damage types.", 1.7, 20),
        ("Does not fit", "No Egyptian roads. No severity. No pixel mask.", 1.7, 20),
    ]
    top = 1.7
    for heading, body, height, size in rows:
        add_rect(slide, 0.42, top, 2.5, height, NAVY)
        add_text(slide, 0.55, top, 2.25, height, heading, 18, WHITE, bold=True, align="center", anchor="middle")
        add_rect(slide, 2.92, top, 9.95, height, CARD, LINE)
        add_text(slide, 3.2, top, 9.4, height, body, size, INK, anchor="middle")
        top += height + 0.35
    notes(
        slide,
        "RDD2022 matches the detection task. It is a weak stand-in for Cairo streets, because the set has no Egyptian roads, dust, or local pavement practice.",
    )


def training_slide(prs, czech: dict) -> None:
    slide = new_slide(prs, "3.3  Model", "YOLOv8s", 9)
    d00 = czech["geometry"]["D00"]["median_width_over_height"]
    d10 = czech["geometry"]["D10"]["median_width_over_height"]
    items = [
        ("Weights", "Fine-tune COCO. Do not train from scratch."),
        ("Layers", "Update every layer."),
        ("Split", "Hold out 20% inside each country."),
        ("Augmentation", "Flip and mosaic. No rotation."),
        ("Metrics", "mAP50, mAP50–95, per-class AP."),
    ]
    for index, (heading, body) in enumerate(items):
        top = 1.45 + index * 1.05
        add_text(slide, 0.45, top, 2.5, 0.8, heading, 18, NAVY, bold=True)
        add_text(slide, 3.1, top, 9.7, 0.85, body, 18, INK)
    notes(
        slide,
        "The model line is only the name. If asked why this family: the labels are boxes, and one frame can contain several damages. "
        "If asked about U-Net: there are no masks. If asked about a larger model: the GPU is 4 GB. YOLOv8n is the fallback if YOLOv8s runs out of memory. "
        f"Rotation stays at zero because a quarter turn would swap D00 and D10. Czech median width/height is {d00:.2f} for D00 and {d10:.2f} for D10. Horizontal flip is safe. "
        "Learning rate starts near 0.001, for up to 100 epochs, with early stopping on validation mAP. Input size 640 for the first run.",
    )


def tools_slide(prs) -> None:
    slide = new_slide(prs, "3.3  Tooling", "Tools", 10)
    blocks = [
        ("Libraries", "PyTorch, Ultralytics, OpenCV"),
        ("Labels", "Pascal VOC XML → YOLO text"),
        ("Hardware", "RTX 3050, 4 GB · 640 px · batch 8"),
        ("Where", "Local. Colab only if 4 GB is not enough."),
    ]
    for index, (heading, body) in enumerate(blocks):
        top = 1.2 + index * 1.42
        add_rect(slide, 0.42, top, 12.5, 1.3, CARD, LINE)
        add_text(slide, 0.65, top + 0.12, 2.4, 1.0, heading, 16, NAVY, bold=True, anchor="middle")
        add_text(slide, 3.2, top + 0.18, 9.4, 1.0, body, 15, INK, anchor="middle")
    notes(
        slide,
        "Milestone 1 did not train the detector. It fixed the stack so the next milestone can. "
        "Say the GPU name and the 4 GB limit out loud. That limit is the reason the starting model is YOLOv8s and the starting image size is 640. "
        "The Czech subset used for the figures is already on disk. The other country archives can be pulled from the same Figshare zip.",
    )


def references_slide(prs) -> None:
    slide = new_slide(prs, "References", "Sources", 11)
    refs = [
        "Arya, D., Maeda, H., Ghosh, S. K., Toshniwal, D., & Sekimoto, Y. (2024). RDD2022. Geoscience Data Journal, 11(4), 846–862.",
        "Arya, D., et al. (2022). RDD2022. figshare. https://doi.org/10.6084/m9.figshare.21431547. CC BY 4.0.",
        "Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8. https://github.com/ultralytics/ultralytics",
    ]
    add_lines(slide, 0.5, 1.5, 12.3, 4.5, refs, size=18, spacing=18)
    notes(
        slide,
        "The image counts, resolutions, and class totals come from the 2024 data article, which is the journal version of arXiv:2209.08538. "
        "The license and the DOI come from the figshare record. "
        "The 2018 and 2021 papers are there if someone asks where the four class codes, or the cross-country failure, came from.",
    )


if __name__ == "__main__":
    print(build())
