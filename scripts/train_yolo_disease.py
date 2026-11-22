"""YOLOv11 Training Script for Crop Disease Detection.

This script trains a YOLOv11 model on the PlantVillage dataset (or custom Indian crop dataset)
for production-grade disease detection in AI Farmer.

Usage:
    python scripts/train_yolo_disease.py --data data/disease_dataset.yaml --epochs 100 --imgsz 640

Dataset Structure Expected:
    data/disease_dataset/
        train/
            rice_blast/
                img001.jpg
                img002.jpg
                ...
            tomato_early_blight/
                ...
        val/
            rice_blast/
                ...
        test/
            ...
"""
import os
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO


def create_dataset_yaml(dataset_path: str, output_path: str = "data/disease_dataset.yaml"):
    """Auto-generate dataset YAML for YOLO training."""
    dataset_path = Path(dataset_path)

    # Discover classes from directory structure
    train_dir = dataset_path / "train"
    if not train_dir.exists():
        raise FileNotFoundError(f"Train directory not found: {train_dir}")

    classes = sorted([d.name for d in train_dir.iterdir() if d.is_dir()])

    dataset_config = {
        "path": str(dataset_path.absolute()),
        "train": "train",
        "val": "val",
        "test": "test",
        "nc": len(classes),
        "names": {i: name for i, name in enumerate(classes)}
    }

    with open(output_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    print(f"✅ Dataset YAML created: {output_path}")
    print(f"   Classes ({len(classes)}): {classes}")
    return output_path


def train_model(data_yaml: str, model_size: str = "n", epochs: int = 100, 
                imgsz: int = 640, batch: int = 16, device: str = "0"):
    """Train YOLOv11 model on disease dataset."""

    # Load pretrained YOLOv11
    model_name = f"yolo11{model_size}-cls.pt"  # Classification model
    print(f"📥 Loading pretrained model: {model_name}")
    model = YOLO(model_name)

    # Training configuration
    print(f"🚀 Starting training...")
    print(f"   Epochs: {epochs}")
    print(f"   Image size: {imgsz}")
    print(f"   Batch size: {batch}")
    print(f"   Device: {device}")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        patience=20,  # Early stopping
        save=True,
        project="runs/disease_detection",
        name=f"yolo11_disease_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
    )

    print(f"✅ Training complete!")
    print(f"   Best model: {results.best}")
    print(f"   mAP: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")

    return results


def export_model(model_path: str, format: str = "onnx"):
    """Export trained model to deployment format."""
    print(f"📦 Exporting model to {format.upper()}...")
    model = YOLO(model_path)

    export_path = model.export(format=format, imgsz=640, half=True)
    print(f"✅ Exported to: {export_path}")
    return export_path


def validate_model(model_path: str, data_yaml: str):
    """Validate trained model on test set."""
    print(f"🧪 Validating model...")
    model = YOLO(model_path)
    metrics = model.val(data=data_yaml)

    print(f"📊 Validation Results:")
    print(f"   mAP50: {metrics.box.map50:.4f}")
    print(f"   mAP50-95: {metrics.box.map:.4f}")
    print(f"   Precision: {metrics.box.mp:.4f}")
    print(f"   Recall: {metrics.box.mr:.4f}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv11 for Crop Disease Detection")
    parser.add_argument("--data", type=str, default="data/disease_dataset", help="Path to dataset directory")
    parser.add_argument("--yaml", type=str, default=None, help="Path to dataset YAML (auto-generated if not provided)")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"], help="YOLO model size")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size for training")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="0", help="GPU device (0 for first GPU, cpu for CPU)")
    parser.add_argument("--export", type=str, default="onnx", choices=["onnx", "torchscript", "engine", "tflite"], help="Export format")
    parser.add_argument("--validate", action="store_true", help="Run validation after training")

    args = parser.parse_args()

    # Create YAML if not provided
    yaml_path = args.yaml or create_dataset_yaml(args.data)

    # Train
    results = train_model(
        data_yaml=yaml_path,
        model_size=args.model_size,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device
    )

    # Validate
    if args.validate:
        validate_model(results.best, yaml_path)

    # Export
    export_model(results.best, args.export)

    print("\n🌾 AI Farmer Disease Detection Model Ready!")
    print(f"   Model path: {results.best}")
    print(f"   Copy to: data/models/disease_detection.pt")


if __name__ == "__main__":
    main()
