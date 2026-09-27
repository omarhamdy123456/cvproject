# Milestone 1 — speaking script (≈4 min)

**Slide 1 — Title (10 s)**
Good morning. Our project is road damage detection: a photo of the road goes in, boxes around every crack and pothole come out.

**Slide 2 — Problem (20 s)**
The task is object detection. The input is one RGB image from a camera on a moving car. The output is a list of boxes, each labelled as one of four classes: longitudinal crack, transverse crack, alligator crack, or pothole. If the road is fine, the list is empty.

**Slide 3 — Input → Output (20 s)**
Here it is on a real frame. Left: what the camera captured. Right: the same frame with the ground-truth boxes, drawn by our code. Six boxes, all four damage types in one frame — which is why this is detection, not classification.

**Slide 4 — Motivation (20 s)**
Potholes wreck wheels and cause crashes, and a missed crack becomes a pothole after one rainy season. Drivers would get an in-car warning; road authorities would get damage reports automatically. Today, the driver just spots it by eye — often too late.

**Slide 5 — Dataset (30 s)**
We're using RDD2022: 47,000 images from six countries, 55,000 labelled boxes, Creative Commons licence. Most of it was shot with a phone on a car, the same setup we'd use. Each image has an XML file with the class and a pixel box — no mask, no severity. The Czech subset is on our disk, and every number from it was counted by our own script.

**Slide 6 — Samples (15 s)**
One real training image per class. Longitudinal cracks run along the road, transverse ones go across, alligator cracks cover a whole patch, and potholes — notice — are tiny.

**Slide 7 — Class distribution (20 s)**
The classes are unbalanced: longitudinal cracks are almost half of all boxes, potholes only twelve percent. And potholes are what a driver most needs. So we'll report a separate AP per class, not one average.

**Slide 8 — Challenges (30 s)**
What will make this fail: the imbalance we just saw; small objects — the median pothole is under half a percent of the frame; 62 percent of Czech frames have no damage at all; domain shift across five camera types and six countries; motion blur — this is a real training frame; and near-duplicate frames, so we must split by sequence, not at random.

**Slide 9 — Justification (20 s)**
Is it the right dataset? It fits: the pictures look like what our camera will see, and it labels exactly what we want to find. It falls short: no Egyptian roads, and no severity — a hairline crack and a wheel-breaking pothole get the same label. So we train on RDD2022 first and check the gap with Cairo frames later.

**Slide 10 — Model and tools (30 s)**
We start from YOLOv8s: it outputs boxes and classes, runs in real time, and fits our 4-gigabyte laptop GPU. We fine-tune from COCO weights — 38,000 images is enough to adapt a detector, not to train one from scratch. 640 pixels, flips and mosaic, no rotation, because a quarter turn would swap transverse and longitudinal cracks. Stack: PyTorch, Ultralytics, OpenCV.

**Slide 11 — Evaluation (20 s)**
Primary metric: mAP at IoU 0.5. Also mAP 0.5 to 0.95 for box tightness, per-class AP so potholes can't hide behind cracks, F1 at one confidence threshold — the driver's operating point — and everything per country to expose domain shift. No plain accuracy: with 62 percent empty frames, it means nothing.

**Slide 12 — References (5 s)**
Our sources. Thank you — happy to take questions.

---

## If asked

- **Why not a classifier?** One frame can hold many damages of different types. We need locations.
- **Why not segmentation / U-Net?** There are no masks in the labels.
- **Why not a bigger model?** 4 GB of VRAM. YOLOv8n is the fallback if v8s runs out of memory.
- **Why per-country validation?** India has 3,187 potholes but only 68 transverse cracks; the US is the reverse. A pooled number would hide a failure on one country.
- **Why no rotation augmentation?** Transverse boxes are 5.3× wider than tall; longitudinal ones are 0.77. Rotating 90° swaps the classes.
- **How was the blur frame chosen?** Lowest Laplacian variance over the road region across all 2,829 Czech training frames.
- **Test set?** Official test labels are private, so we hold out 20% of the training set, stratified per country and split by filename sequence.
