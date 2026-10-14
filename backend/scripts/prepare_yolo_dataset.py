from collections import Counter
from pathlib import Path
import random
import shutil
import xml.etree.ElementTree as ET

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = (
    PROJECT_ROOT
    / "backend"
    / "datasets"
    / "marine_debris"
    / "md_fls_dataset"
    / "data"
    / "watertank-segmentation"
)

IMAGE_DIR = SOURCE_DIR / "Images"
ANNOTATION_DIR = SOURCE_DIR / "BoxAnnotations"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "datasets"
    / "marine_debris_yolo"
)

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

# --------------------------------------------------
# HELPERS
# --------------------------------------------------


def parse_annotation(xml_path):
    """Parse XML and return image filename, dimensions and objects."""

    root = ET.parse(xml_path).getroot()

    filename = root.findtext("filename")

    size = root.find("size")
    if size is None:
        raise ValueError(f"Missing image dimensions: {xml_path.name}")

    width = int(size.findtext("width", "0"))
    height = int(size.findtext("height", "0"))

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid image dimensions: {xml_path.name}")

    objects = []

    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        box = obj.find("bndbox")

        if not name or box is None:
            raise ValueError(f"Invalid object annotation: {xml_path.name}")

        x = float(box.findtext("x", "nan"))
        y = float(box.findtext("y", "nan"))
        w = float(box.findtext("w", "nan"))
        h = float(box.findtext("h", "nan"))

        if not all(map(lambda v: v == v and abs(v) != float("inf"), [x, y, w, h])):
            raise ValueError(f"Non-finite box: {xml_path.name}")

        if w <= 0 or h <= 0:
            raise ValueError(f"Non-positive box: {xml_path.name}")

        if x < 0 or y < 0 or x + w > width or y + h > height:
            raise ValueError(f"Out-of-bounds box: {xml_path.name}")

        objects.append((name, x, y, w, h))

    return filename, width, height, objects


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main():
    if not IMAGE_DIR.is_dir() or not ANNOTATION_DIR.is_dir():
        raise FileNotFoundError(
            "Dataset folders not found. Check the extraction path."
        )

    xml_files = sorted(ANNOTATION_DIR.glob("*.xml"))

    if not xml_files:
        raise RuntimeError("No XML annotation files found.")

    records = []
    class_counts = Counter()
    seen_images = set()

    print(f"Reading annotations from: {ANNOTATION_DIR}")

    for xml_path in xml_files:
        filename, width, height, objects = parse_annotation(xml_path)

        if not filename:
            raise ValueError(f"Missing filename in {xml_path.name}")

        image_path = IMAGE_DIR / Path(filename).name

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Image missing for annotation {xml_path.name}: {image_path}"
            )

        if image_path.name in seen_images:
            raise ValueError(f"Duplicate image reference: {image_path.name}")

        seen_images.add(image_path.name)

        for name, *_ in objects:
            class_counts[name] += 1

        records.append(
            {
                "image": image_path,
                "width": width,
                "height": height,
                "objects": objects,
            }
        )

    # Preserve all original classes.
    class_names = sorted(class_counts.keys())
    class_to_id = {name: idx for idx, name in enumerate(class_names)}

    # Split images deterministically.
    random.Random(RANDOM_SEED).shuffle(records)

    total = len(records)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    splits = {
        "train": records[:train_end],
        "val": records[train_end:val_end],
        "test": records[val_end:],
    }

    # Refuse to overwrite a previous prepared dataset.
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise FileExistsError(
            f"Output already exists: {OUTPUT_DIR}\n"
            "Rename or remove it before rebuilding the dataset."
        )

    for split in splits:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    print("\nCopying images and converting annotations...")

    for split, split_records in splits.items():
        for record in split_records:
            source_image = record["image"]
            width = record["width"]
            height = record["height"]

            destination_image = OUTPUT_DIR / "images" / split / source_image.name
            destination_label = (
                OUTPUT_DIR
                / "labels"
                / split
                / f"{source_image.stem}.txt"
            )

            shutil.copy2(source_image, destination_image)

            lines = []

            for name, x, y, w, h in record["objects"]:
                class_id = class_to_id[name]

                # Original XML uses x, y, width, height.
                # YOLO expects normalized center_x, center_y, width, height.
                center_x = (x + w / 2) / width
                center_y = (y + h / 2) / height
                normalized_w = w / width
                normalized_h = h / height

                lines.append(
                    f"{class_id} "
                    f"{center_x:.6f} "
                    f"{center_y:.6f} "
                    f"{normalized_w:.6f} "
                    f"{normalized_h:.6f}"
                )

            destination_label.write_text(
                "\n".join(lines) + ("\n" if lines else ""),
                encoding="utf-8",
            )

    # Generate Ultralytics dataset configuration.
    yaml_lines = [
        f"path: {OUTPUT_DIR.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        f"nc: {len(class_names)}",
        "names:",
    ]

    for idx, name in enumerate(class_names):
        safe_name = name.replace("'", "''")
        yaml_lines.append(f"  {idx}: '{safe_name}'")

    yaml_path = OUTPUT_DIR / "data.yaml"
    yaml_path.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    print("\n" + "=" * 55)
    print("YOLO DATASET PREPARATION COMPLETE")
    print("=" * 55)

    print(f"Total images: {total}")
    print(f"Classes: {len(class_names)}")

    for split, split_records in splits.items():
        print(f"{split}: {len(split_records)} images")

    print("\nClass mapping:")

    for name, idx in class_to_id.items():
        print(f"  {idx}: {name} ({class_counts[name]} objects)")

    print(f"\nDataset configuration: {yaml_path}")
    print(f"Dataset output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()