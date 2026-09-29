# Document Trust India — Model Assets (FP32)

Place trained/exported models in this directory.

## Required for Milestone 1

| File | Description |
|------|-------------|
| `yolo26n_seg_document.onnx` | Fine-tuned YOLO26n-seg, single class: `document` |

## Required for later pipeline stages

| Path | Description |
|------|-------------|
| `mobilenetv3_indian_docs.onnx` | MobileNetV3-Large classifier (aadhaar/pan/passport/dl/voter_id/unknown) |
| `pp_lcnet_doc_ori/` | PP-LCNet_x1_0_doc_ori orientation model bundle |
| `uvdoc/` | Optional UVDoc ONNX for severe distortion (disabled by default) |

## Export commands

**Important:** run these from the `backend/` directory (not the repo root).

```bash
cd backend
source .venv/bin/activate   # if you use the project venv

# YOLO26n-seg (train then export FP32 ONNX)
# Replace datasets/document/document.yaml with your real dataset YAML.
python3 scripts/models/train_yolo_document_seg.py --data datasets/document/document.yaml --device auto
python3 scripts/models/export_yolo_onnx.py \
  --weights runs/segment/document_yolo26n_seg/weights/best.pt \
  --output models/yolo26n_seg_document.onnx

# MobileNetV3 classifier
python3 scripts/models/train_mobilenetv3_classifier.py --data-dir path/to/ImageFolder
python3 scripts/models/export_classifier_onnx.py \
  --weights runs/classifier/mobilenetv3_indian_docs.pt \
  --output models/mobilenetv3_indian_docs.onnx

# PP-LCNet orientation (optional local bundle)
python3 scripts/models/setup_pp_lcnet_orientation.py
```

If you prefer to stay in the repo root, prefix paths with `backend/`:

```bash
backend/.venv/bin/python3 backend/scripts/models/train_yolo_document_seg.py --data path/to/document.yaml
backend/.venv/bin/python3 backend/scripts/models/export_yolo_onnx.py \
  --weights backend/runs/segment/document_yolo26n_seg/weights/best.pt \
  --output backend/models/yolo26n_seg_document.onnx
```

## Notes

- Keep models in **FP32** (no INT8/FP16 quantization initially).
- Prefer **ONNX Runtime**; OpenCV DNN is supported via `ONNX_INFERENCE_BACKEND=opencv_dnn`.
- GPU is auto-selected when `CUDAExecutionProvider` is available.
