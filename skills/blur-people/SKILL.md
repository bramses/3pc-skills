---
name: blur-people
description: Blur out people (faces and torsos) in a photo, given an image file path, to anonymize or redact them. Use this whenever the user wants to anonymize, censor, redact, or hide people in a picture — phrases like "blur the people in this image," "hide the people in this photo," "anonymize this picture," "blur out everyone in this pic," or "censor the people" should all trigger this skill, even if they only mention "faces" loosely while sharing a photo with full bodies in it. Also use it for workshop/demo requests to redact bystanders from photos before sharing them publicly. Leg/lower-body coverage is inconsistent (see limitations below) — this reliably hides identity via face+torso, not necessarily every limb.
---

# Blur people

Detect people in an image and blur them out, producing an edited copy.
Confirmed working in both Claude Code and Claude Desktop/claude.ai.

## How it works

Run the bundled script:

```bash
python3 scripts/blur_people.py <input_image> [output_image] [--strength N]
```

- `input_image`: path to the photo the user gave you.
- `output_image`: optional; defaults to `<input>_blurred.<ext>` next to the
  input.
- `--strength`: odd integer, Gaussian blur kernel size. Defaults to ~10% of
  the image's shorter side (not a fixed number) so the blur is consistently
  strong regardless of photo resolution — a fixed kernel was proportionally
  weak on large photos and too strong on small ones. Pass a value to
  override.

Detection uses a bundled DeepLabV3+/MobileNet semantic segmentation model
(`assets/deeplabv3_plus_mobilenet.onnx` + `assets/deeplabv3_plus_mobilenet.data`,
~22MB total, run locally via `onnxruntime`) to get a real per-pixel "is this
a person" mask — not a bounding box. No model download or network call
happens at request time; the model ships inside this skill folder. The mask
is feathered (Gaussian-blurred) before compositing so edges look intentional
rather than a hard cutout. See [references/approach.md](references/approach.md)
for the full history — an earlier version used `opencv-python`'s built-in
HOG/Haar detectors instead, and was replaced after real-photo testing showed
it missed people in non-standing poses.

## Using it

1. Confirm you have an image path (ask the user to share/upload if you don't).
2. Check dependencies once per environment:
   ```bash
   python3 -c "import cv2, numpy, onnxruntime" || pip install opencv-python numpy onnxruntime
   ```
   Run this visibly — don't silently install packages the user can't see.
   Note: `onnxruntime` needs to be recent enough to load this model (tested
   working at 1.19.2; version 1.12 failed with "Unsupported model IR
   version" — if that error shows up, `pip install --upgrade onnxruntime`).
3. Run the script on the image.
4. Show the user the output path (and the image itself, if the surface
   supports inline display). If the script reports "No people detected,"
   say so plainly and suggest a clearer photo, or one where people take up
   more of the frame, rather than silently returning the unedited image as
   if it worked.

## Known limitations (confirmed via real-photo testing, not theoretical)

- **Legs/lower body are often missed**, especially in brightly colored or
  unusual clothing (tested: a dance photo in colorful tights/leotards got
  every face and torso blurred, but legs stayed completely sharp). Treat
  this as face+torso anonymization, not guaranteed full-body coverage. If
  a user specifically needs limbs covered too, say so rather than assuming
  it's handled.
- **Dim lighting and unusual framing hurt detection** — a test photo with a
  person in a dark hoodie under low light, plus a face shown *within* a
  video-call screen inside the photo, was almost entirely missed by this
  model. If the output looks unchanged or under-blurred, say so plainly
  rather than assuming the photo had no people in it.
- **The model doesn't separate individual people** — it's a person-vs-not
  mask, not per-instance detection, so a tight cluster of people blurs as
  one connected blob rather than as distinguishable individuals. This is
  fine for anonymization but means you can't ask it to "blur only the
  person on the left."

## Desktop / claude.ai support

Confirmed working live on Desktop/claude.ai — `opencv-python` and
`onnxruntime` do import in that sandboxed code-execution environment. This
was the open risk flagged during design (same category of constraint that
got an earlier skill in this repo, "subway," built twice and pulled after
its bundled script's network calls turned out to be blocked there); it's now
verified rather than assumed.
