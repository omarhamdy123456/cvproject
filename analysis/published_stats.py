"""RDD2022 training-set counts from Arya et al.

Source: Arya, Maeda, Ghosh, Toshniwal, and Sekimoto, "RDD2022: A multi-national
image dataset for automatic road damage detection" (arXiv:2209.08538; Geoscience
Data Journal, 2024). Figure 4 gives images and label totals. Figure 5 gives the
four damage classes. Row sums were checked against those totals before use.
"""

from __future__ import annotations

# country, train images, test images, D00, D10, D20, D40
COUNTRY_ROWS = [
    ("Japan", 10_506, 2_627, 4_049, 3_979, 6_199, 2_243),
    ("India", 7_706, 1_959, 1_555, 68, 2_021, 3_187),
    ("Czech Republic", 2_829, 709, 988, 399, 161, 197),
    ("Norway", 8_161, 2_040, 8_570, 1_730, 468, 461),
    ("United States", 4_805, 1_200, 6_750, 3_295, 834, 135),
    ("China, motorbike", 1_977, 500, 2_678, 1_096, 641, 235),
    ("China, drone", 2_401, 0, 1_426, 1_263, 293, 86),
]

CLASSES = ("D00", "D10", "D20", "D40")
CLASS_NAMES = {
    "D00": "Longitudinal crack",
    "D10": "Transverse crack",
    "D20": "Alligator crack",
    "D40": "Pothole",
}

# Capture resolution stated in the data article, not measured from every file.
RESOLUTIONS = {
    "Japan": "600 × 600",
    "India": "720 × 720",
    "Czech Republic": "600 × 600",
    "Norway": "3650 × 2044",
    "United States": "640 × 640",
    "China, motorbike": "512 × 512",
    "China, drone": "512 × 512",
}

CAPTURE = {
    "Japan": "Smartphone on a car",
    "India": "Smartphone on a car",
    "Czech Republic": "Smartphone on a car",
    "Norway": "Two survey cameras, stitched",
    "United States": "Google Street View",
    "China, motorbike": "Camera on a motorbike",
    "China, drone": "Drone, top-down",
}


def class_totals() -> dict[str, int]:
    totals = {name: 0 for name in CLASSES}
    for _country, _train, _test, d00, d10, d20, d40 in COUNTRY_ROWS:
        for name, count in zip(CLASSES, (d00, d10, d20, d40)):
            totals[name] += count
    return totals


def train_images() -> int:
    return sum(row[1] for row in COUNTRY_ROWS)


def test_images() -> int:
    return sum(row[2] for row in COUNTRY_ROWS)


def train_instances() -> int:
    return sum(class_totals().values())


def _check() -> None:
    totals = class_totals()
    if train_images() != 38_385 or test_images() != 9_035:
        raise AssertionError("image totals drifted from Arya et al. Figure 4")
    if totals != {"D00": 26_016, "D10": 11_830, "D20": 10_617, "D40": 6_544}:
        raise AssertionError(totals)
    if train_instances() != 55_007:
        raise AssertionError(train_instances())
    for country, _train, _test, d00, d10, d20, d40 in COUNTRY_ROWS:
        # Figure 4 label totals are the sum of the four Figure 5 classes.
        expected = {
            "Japan": 16_470,
            "India": 6_831,
            "Czech Republic": 1_745,
            "Norway": 11_229,
            "United States": 11_014,
            "China, motorbike": 4_650,
            "China, drone": 3_068,
        }[country]
        if d00 + d10 + d20 + d40 != expected:
            raise AssertionError(country)


_check()
