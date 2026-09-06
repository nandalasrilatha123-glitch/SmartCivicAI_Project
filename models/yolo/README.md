# Custom YOLOv8 civic-issue model

`app/cv/yolo_detector.py` looks for a trained model at the path in
`YOLO_WEIGHTS_PATH` (backend `.env`, default: `models/yolo/civic_issues.pt`,
relative to the `backend/` directory). **No such file ships with this
project** — nobody has a pre-trained "pothole vs. garbage vs. water leak"
detector sitting around, and pretending otherwise would violate the
project's own honesty requirement (spec §10).

## What happens without a custom model here
- `CV_PROVIDER=demo` (default): no detection is attempted at all.
- `CV_PROVIDER=yolo` with no file at this path: the code falls back to
  ultralytics' stock COCO-pretrained `yolov8n.pt` (auto-downloaded on first
  use — needs network). It will genuinely detect real-world COCO classes
  like `car`, `person`, `traffic light` — useful for a Traffic-module photo,
  basically useless for "is this pothole bad" — and every detection from
  this fallback is prefixed `coco:` and marked as demo-status, never
  presented as if it were a real civic-issue classifier.

## To train a real one
1. **Collect and label images** for the classes you care about per module:
   - Traffic: pothole, damaged_road, broken_signal, illegal_parking
   - Government Schools: damaged_infrastructure, unsafe_condition
   - Healthcare: unclean_area, damaged_equipment
   - Agriculture: crop_disease_visible, pest_damage
   Use a tool like [Roboflow](https://roboflow.com) or
   [LabelImg](https://github.com/HumanSignal/labelImg) to draw bounding
   boxes and export in YOLO format.

2. **Fine-tune YOLOv8** (needs `requirements-ai.txt` installed):
   ```python
   from ultralytics import YOLO

   model = YOLO("yolov8n.pt")  # start from the COCO-pretrained base
   model.train(data="path/to/your_dataset.yaml", epochs=50, imgsz=640)
   ```
   This produces a `best.pt` under `runs/detect/train/weights/`.

3. **Place it here**: copy that file to
   `models/yolo/civic_issues.pt` (or update `YOLO_WEIGHTS_PATH` in
   `backend/.env` to point wherever you put it).

4. **Set `CV_PROVIDER=yolo`** in `backend/.env` and restart the backend.
   New complaint image uploads will now run through your model, and
   `cv_analysis.status` will read `ANALYZED_MODEL` (not `ANALYZED_DEMO`)
   to confirm the real model is the one that ran.

## Verifying which path actually ran
Check the `cv_analysis` table for a given image, or look at the `note`
field returned alongside detections — it always says explicitly whether
a custom model, the generic COCO fallback, or no detection at all was used.
