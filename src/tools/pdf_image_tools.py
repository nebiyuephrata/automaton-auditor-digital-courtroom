from pathlib import Path
from typing import List

from pypdf import PdfReader

from src.state import Evidence


def extract_images_from_pdf(path: str, output_dir: str) -> List[str]:
    reader = PdfReader(path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    extracted: List[str] = []
    image_index = 0
    for page in reader.pages:
        resources = page.get("/Resources")
        if not resources:
            continue
        x_object = resources.get("/XObject") if hasattr(resources, "get") else None
        if not x_object:
            continue

        x_object = x_object.get_object()
        for obj in x_object.values():
            obj_data = obj.get_object()
            if obj_data.get("/Subtype") == "/Image":
                ext = ".bin"
                filt = obj_data.get("/Filter")
                if filt == "/DCTDecode":
                    ext = ".jpg"
                elif filt == "/FlateDecode":
                    ext = ".png"

                image_path = output / f"image_{image_index}{ext}"
                image_path.write_bytes(obj_data.get_data())
                extracted.append(str(image_path))
                image_index += 1

    return extracted


def classify_diagram(image_path: str) -> Evidence:
    name = Path(image_path).name.lower()
    if "graph" in name or "langgraph" in name:
        classification = "stategraph"
        rationale = "Filename indicates graph/state machine visualization."
        confidence = 0.8
    elif "arch" in name:
        classification = "architecture_diagram"
        rationale = "Filename indicates architecture depiction."
        confidence = 0.75
    else:
        classification = "generic_diagram"
        rationale = "Could not confirm explicit StateGraph flow from filename only."
        confidence = 0.55

    return Evidence(
        goal="Swarm Visual Classification",
        found=True,
        content=classification,
        location=image_path,
        rationale=rationale,
        confidence=confidence,
    )
