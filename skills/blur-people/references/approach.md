# Technical approach and tradeoffs

This skill went through two real approaches, tested against real photos
each time, not just theory. This doc records both, since the reasoning for
rejecting the first one is as useful as the reasoning for the second.

## v1 (rejected): bounding boxes via opencv-python's built-in detectors

The first version used `cv2`'s built-in HOG pedestrian detector plus a Haar
face cascade extended into a rough body box — both ship inside
`opencv-python` itself, so there was nothing to download. Tested on two real
photos:

- A photo of a person wearing a CRT-monitor "head" showing a video call:
  correctly blurred the face on the screen and the real person's
  torso/shoulders, but also produced a false positive on decorative foil
  foliage in the background (Haar cascades can trigger on high-contrast
  textured patterns that aren't people).
- A product photo of 6 dancers in dynamic poses: **completely missed the
  two clearest, most identifiable dancers in the foreground**, and instead
  drew an oversized blur blob over a cluster of people in the back. HOG is
  trained on upright walking/standing silhouettes; dance poses (leaning,
  twisted, mid-motion) don't match that profile, so it just doesn't fire.

That second result — missing the most identifiable people while blurring
the wrong region — was the reason to drop this approach rather than keep
tuning it. A detector that's blind to non-standing poses isn't good enough
for photos of people actually doing things (dancing, sports, sitting,
candid group shots).

## v2 (current): DeepLabV3+/MobileNet semantic segmentation

Bundled model: `assets/deeplabv3_plus_mobilenet.onnx` +
`assets/deeplabv3_plus_mobilenet.data` (external weights file ONNX splits
out), ~22MB total on disk. Source:
[huggingface.co/qualcomm/DeepLabV3-Plus-MobileNet](https://huggingface.co/qualcomm/DeepLabV3-Plus-MobileNet),
MIT-licensed (original implementation:
[jfzhang95/pytorch-deeplab-xception](https://github.com/jfzhang95/pytorch-deeplab-xception)).
Downloaded with the user's explicit sign-off on filename/source/size before
fetching, per this repo's policy on downloading files into a skill.

**Why this model specifically**: it does general semantic segmentation over
21 Pascal VOC classes (including "person"), trained on varied everyday
scenes with multiple people at different scales — not a single-subject
selfie/video-call model. A 447KB Mediapipe Selfie Segmentation ONNX export
was considered and rejected: its own documentation describes it as built
for "a person" (singular) in selfie/video-call framing, which risked the
exact same failure mode that killed v1 (missing people who aren't the one
dominant close-up subject). A larger 45MB ResNet50-backbone alternative
([Metal3d/deeplabv3p-resnet50-human](https://huggingface.co/Metal3d/deeplabv3p-resnet50-human))
was also considered but rejected for exceeding the ~30MB skill upload limit.

**Inference details** (see `assets/metadata.json`): input is a
520×520×3 RGB image normalized to [0, 1], NCHW layout; output is a
520×520 array of per-pixel class indices (argmax already applied inside the
graph). `assets/labels.txt` maps index → class name; "person" is the
relevant one. The mask is resized back to the original image dimensions
and fed through the same Gaussian-feather-then-composite blur as v1.

**Real test results**:

- Dance photo (6 dancers, dynamic poses): major improvement over v1 — every
  dancer's face is now blurred, including the two that v1 missed entirely.
  But the raw mask (visualized during testing) shows it treats the tightly
  clustered group as **one connected blob**, and that blob stops around the
  torso — **legs stayed completely sharp**, likely because the model
  doesn't recognize brightly colored dancewear/tights as "person" pixels.
  Decision (with user sign-off): accept face+torso coverage as good enough
  for anonymization purposes rather than keep engineering for full-leg
  coverage. Bare legs alone rarely identify someone the way a face does.
- CRT-monitor photo: **worse than v1** here — the model almost entirely
  missed both the real foreground person (dim lighting, dark hoodie — low
  contrast hurts segmentation models) and the face shown on the video-call
  screen within the photo. This is a genuinely hard, somewhat unusual scene
  (a photo of a screen showing a person, plus a dim real person) that
  doesn't closely resemble typical training data for either detector
  approach tried so far.

Net assessment: v2 is a meaningfully better default than v1 for typical
photos of people, worse for unusual/dim/screen-within-photo framing. Neither
approach is uniformly better — this was a real, measured tradeoff, not a
strict upgrade.

## What could still improve this, if it becomes a real complaint

- **Combine v1 and v2**: run the segmentation mask as primary, fall back to
  HOG/Haar boxes to catch what it misses (dim scenes, screens-within-photos).
  More coverage, more complexity, still no fix for the leg-coverage gap.
- **Morphological closing on the mask** (dilate/erode to bridge small gaps)
  might help borderline cases but won't fix wholesale misclassification of
  unusual clothing as non-person.
- A model specifically trained on diverse clothing/lighting would be the
  real fix for both remaining gaps, but that's a bigger sourcing/vetting
  effort than this skill's current scope.

## Known open risk: Desktop/claude.ai support

Still unverified. `opencv-python` and `onnxruntime` are both fairly heavy
compiled dependencies; whether the Desktop/claude.ai sandboxed
code-execution environment can import them (with or without network access
to install them) hasn't been tested live on that surface. This is the same
category of risk that got the subway skill built twice and pulled — don't
assume it works there until someone actually runs it.

## Dependency note discovered during testing

The local dev environment already had `onnxruntime==1.12.0` pinned by
another installed package (`rembg`). That version fails to load this model
with `Unsupported model IR version: 9, max supported IR version: 8` —
upgrading to `onnxruntime==1.19.2` fixed it. If a user's environment has an
older `onnxruntime` (or something else pinning it low), they'll hit this
same error; the fix is `pip install --upgrade onnxruntime`.
