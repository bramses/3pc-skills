#!/usr/bin/env python3
"""Blur full-body people regions in an image.

Usage:
    python blur_people.py <input_image> [output_image] [--strength N]

Uses a bundled DeepLabV3+/MobileNet semantic segmentation model
(assets/deeplabv3_plus_mobilenet.onnx, ~22MB total with its external weights
file) to get a real per-pixel "is this a person" mask — not a bounding box.
The model ships inside this skill folder and is loaded purely from local
disk via onnxruntime; there is no network call or model download at request
time. See references/approach.md for why this replaced an earlier
bounding-box (HOG/Haar) approach: it missed people in non-standing poses and
falsely flagged textured non-person objects as people.

The mask is feathered (Gaussian-blurred) before compositing so edges look
intentional rather than a hard cutout.
"""
import sys
import argparse
from pathlib import Path

try:
    import cv2
    import numpy as np
    import onnxruntime as ort
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e}. Install with:\n"
        f"    pip install opencv-python numpy onnxruntime\n"
        f"(This script does not auto-install packages so you can see what's "
        f"happening on your machine.)"
    )

MODEL_PATH = Path(__file__).parent.parent / "assets" / "deeplabv3_plus_mobilenet.onnx"
LABELS_PATH = Path(__file__).parent.parent / "assets" / "labels.txt"
MODEL_INPUT_SIZE = 520  # matches assets/metadata.json


def person_class_index():
    labels = LABELS_PATH.read_text().splitlines()
    return labels.index("person")


def compute_person_mask(image_bgr, session):
    h, w = image_bgr.shape[:2]

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (MODEL_INPUT_SIZE, MODEL_INPUT_SIZE), interpolation=cv2.INTER_LINEAR)
    tensor = resized.astype(np.float32) / 255.0  # model expects [0, 1]
    tensor = np.transpose(tensor, (2, 0, 1))[None, ...]  # NCHW

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    class_map = session.run([output_name], {input_name: tensor})[0]  # (1, 520, 520) uint8
    class_map = class_map[0]

    person_mask = (class_map == person_class_index()).astype(np.float32)
    return cv2.resize(person_mask, (w, h), interpolation=cv2.INTER_LINEAR)


def blur_with_mask(image, mask, strength):
    feather = max(15, strength * 2 | 1)  # odd kernel size
    mask = cv2.GaussianBlur(mask, (feather, feather), 0)
    mask = np.clip(mask, 0, 1)[:, :, None]

    k = strength | 1  # ensure odd
    blurred = cv2.GaussianBlur(image, (k, k), 0)

    out = image.astype(np.float32) * (1 - mask) + blurred.astype(np.float32) * mask
    return out.astype(np.uint8)


def adaptive_strength(image, factor=0.10, minimum=31):
    """Scale the blur kernel to the image's resolution instead of a fixed
    pixel count — a fixed kernel is proportionally weak on a large photo and
    disproportionately strong on a small one."""
    h, w = image.shape[:2]
    k = int(round(min(h, w) * factor))
    return max(minimum, k) | 1  # ensure odd


def main():
    parser = argparse.ArgumentParser(description="Blur full-body people regions in an image.")
    parser.add_argument("input", help="Path to input image")
    parser.add_argument("output", nargs="?", help="Path to output image (default: <input>_blurred.<ext>)")
    parser.add_argument("--strength", type=int, default=None,
                         help="Gaussian blur kernel size (odd). Default: scaled to image "
                              "resolution (roughly 10%% of the shorter side) so the blur is "
                              "consistently strong regardless of photo size.")
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        sys.exit(f"Segmentation model not found at {MODEL_PATH} — is assets/ present alongside this script?")

    in_path = Path(args.input)
    if not in_path.exists():
        sys.exit(f"Input image not found: {in_path}")

    image = cv2.imread(str(in_path))
    if image is None:
        sys.exit(f"Could not read image (unsupported format?): {in_path}")

    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    mask = compute_person_mask(image, session)

    person_pixels = int(mask.sum())
    if person_pixels == 0:
        print("No people detected — writing image unchanged. "
              "Try a clearer photo, or one where people take up more of the frame.")
    else:
        coverage = person_pixels / mask.size * 100
        print(f"Detected person pixels covering ~{coverage:.1f}% of the frame, blurring...")

    strength = args.strength if args.strength is not None else adaptive_strength(image)
    result = blur_with_mask(image, mask, strength)

    out_path = Path(args.output) if args.output else in_path.with_name(in_path.stem + "_blurred" + in_path.suffix)
    cv2.imwrite(str(out_path), result)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
