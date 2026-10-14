from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

DATASET_DIR = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "marine_debris"
    / "md_fls_dataset"
    / "data"
    / "watertank-segmentation"
)

IMAGE_DIR = DATASET_DIR / "Images"
ANNOTATION_DIR = DATASET_DIR / "BoxAnnotations"
MASK_DIR = DATASET_DIR / "Masks"


def main():
    print("=" * 60)
    print("OCEANGUARD AI - SONAR DATASET INSPECTION")
    print("=" * 60)

    for folder in (IMAGE_DIR, ANNOTATION_DIR, MASK_DIR):
        print(f"{folder.name}: {'FOUND' if folder.is_dir() else 'MISSING'}")

    if not ANNOTATION_DIR.is_dir():
        print("\nERROR: Annotation folder not found.")
        return

    xml_files = sorted(ANNOTATION_DIR.glob("*.xml"))

    class_counts = Counter()
    missing_images = []
    invalid_boxes = []
    total_objects = 0
    valid_annotations = 0

    for xml_file in xml_files:
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            print(f"Invalid XML: {xml_file.name}: {exc}")
            continue

        filename = root.findtext("filename")

        if not filename:
            missing_images.append(xml_file.name)
        elif not (IMAGE_DIR / Path(filename).name).is_file():
            missing_images.append(filename)

        size = root.find("size")
        width = int(size.findtext("width", "0")) if size is not None else 0
        height = int(size.findtext("height", "0")) if size is not None else 0

        objects = root.findall("object")
        valid_annotations += 1
        total_objects += len(objects)

        for obj in objects:
            class_name = (obj.findtext("name") or "UNKNOWN").strip()
            class_counts[class_name] += 1

            box = obj.find("bndbox")
            if box is None:
                invalid_boxes.append((xml_file.name, class_name, "missing bndbox"))
                continue

            try:
                x = float(box.findtext("x", "nan"))
                y = float(box.findtext("y", "nan"))
                w = float(box.findtext("w", "nan"))
                h = float(box.findtext("h", "nan"))
            except ValueError:
                invalid_boxes.append((xml_file.name, class_name, "non-numeric box"))
                continue

            if (
                width <= 0
                or height <= 0
                or w <= 0
                or h <= 0
                or x < 0
                or y < 0
                or x + w > width
                or y + h > height
            ):
                invalid_boxes.append((xml_file.name, class_name, (x, y, w, h)))

    image_count = (
        sum(1 for p in IMAGE_DIR.iterdir() if p.is_file())
        if IMAGE_DIR.is_dir()
        else 0
    )
    mask_count = (
        sum(1 for p in MASK_DIR.iterdir() if p.is_file())
        if MASK_DIR.is_dir()
        else 0
    )

    print(f"\nImages: {image_count}")
    print(f"XML annotations: {len(xml_files)}")
    print(f"Parsed annotations: {valid_annotations}")
    print(f"Masks: {mask_count}")
    print(f"Total annotated objects: {total_objects}")

    print("\nCLASS COUNTS")
    print("-" * 40)
    for name, count in class_counts.most_common():
        print(f"{name}: {count}")

    print(f"\nAnnotations referencing missing images: {len(missing_images)}")
    for name in missing_images[:10]:
        print(f"  - {name}")

    print(f"\nInvalid bounding boxes: {len(invalid_boxes)}")
    for item in invalid_boxes[:10]:
        print(f"  - {item}")

    print("\nInspection complete.")


if __name__ == "__main__":
    main()