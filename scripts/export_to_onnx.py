"""Export sentence-transformers model to ONNX format for lightweight inference."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import EMBEDDING_MODEL_PATH


def export_to_onnx():
    """Export the MiniLM model to ONNX format."""
    print("=" * 60)
    print("Export Sentence-Transformer Model to ONNX")
    print("=" * 60)

    try:
        # Import sentence-transformers (only needed for export)
        from sentence_transformers import SentenceTransformer
        import torch
        from transformers import AutoTokenizer

        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        print(f"\n1. Loading sentence-transformer model: {model_name}")
        model = SentenceTransformer(model_name)

        # Get the underlying transformer model
        transformer_model = model[0].auto_model

        print(f"\n2. Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        print(f"\n3. Preparing dummy inputs for export...")
        # Create dummy inputs
        dummy_text = "This is a sample sentence for export"
        inputs = tokenizer(
            dummy_text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        # Prepare input names and dynamic axes
        input_names = ["input_ids", "attention_mask"]
        output_names = ["last_hidden_state"]
        dynamic_axes = {
            "input_ids": {0: "batch_size", 1: "sequence"},
            "attention_mask": {0: "batch_size", 1: "sequence"},
            "last_hidden_state": {0: "batch_size", 1: "sequence"},
        }

        # Create output directory
        EMBEDDING_MODEL_PATH.mkdir(parents=True, exist_ok=True)
        onnx_model_path = EMBEDDING_MODEL_PATH / "model.onnx"

        print(f"\n4. Exporting to ONNX format...")
        print(f"   Output path: {onnx_model_path}")

        # Export to ONNX
        torch.onnx.export(
            transformer_model,
            (inputs["input_ids"], inputs["attention_mask"]),
            str(onnx_model_path),
            input_names=input_names,
            output_names=output_names,
            dynamic_axes=dynamic_axes,
            opset_version=17,
            do_constant_folding=True,
        )

        print(f"\n5. Saving tokenizer...")
        tokenizer.save_pretrained(str(EMBEDDING_MODEL_PATH))

        # Verify the export
        print(f"\n6. Verifying ONNX model...")
        import onnxruntime as ort

        session = ort.InferenceSession(
            str(onnx_model_path), providers=["CPUExecutionProvider"]
        )

        # Test inference
        onnx_inputs = {
            "input_ids": inputs["input_ids"].numpy(),
            "attention_mask": inputs["attention_mask"].numpy(),
        }

        outputs = session.run(None, onnx_inputs)

        print(f"   ✓ ONNX model runs successfully")
        print(f"   Output shape: {outputs[0].shape}")

        # Get file sizes
        import os

        onnx_size = os.path.getsize(onnx_model_path) / (1024 * 1024)

        print(f"\n" + "=" * 60)
        print("✓ Export completed successfully!")
        print("=" * 60)
        print(f"ONNX model size: {onnx_size:.2f} MB")
        print(f"Location: {EMBEDDING_MODEL_PATH}")
        print(f"\nYou can now:")
        print("  1. Uninstall sentence-transformers and torch (optional)")
        print("  2. Use the lightweight ONNX model for inference")
        print("  3. Enjoy faster inference with smaller dependencies!")

        return 0

    except ImportError as e:
        print(f"\n✗ Error: Missing dependencies for export")
        print(f"   {e}")
        print(f"\nTo export the model, install these packages temporarily:")
        print(f"   pip install sentence-transformers torch")
        print(f"\nAfter export, you can uninstall them and use only onnxruntime")
        return 1

    except Exception as e:
        print(f"\n✗ Error during export: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(export_to_onnx())
