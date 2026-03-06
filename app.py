import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import streamlit as st
import json
import zipfile
import io

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

ORIGINAL_IMAGE_SIZE = 1536
ORIGINAL_CENTER = 768  # Grid was originally centered at 768,768


# --------------------------------------------------
# LOAD BASE GRIDS
# --------------------------------------------------

with open("DMP03.json", "r") as f:
    dmp_data = json.load(f)

with open("HDT03.json", "r") as f:
    hdt_data = json.load(f)


# --------------------------------------------------
# GRID SHIFT FUNCTION (MATHEMATICALLY CORRECT)
# --------------------------------------------------

def shift_grid(original_points, new_center_x, new_center_y, image_size):

    scale_factor = image_size / ORIGINAL_IMAGE_SIZE
    scaled_old_center = ORIGINAL_CENTER * scale_factor

    new_points = []

    for p in original_points:
        # Convert original percentage back to pixel (1536 reference)
        old_x_pixel = p["x_perc"] * ORIGINAL_IMAGE_SIZE
        old_y_pixel = p["y_perc"] * ORIGINAL_IMAGE_SIZE

        # Scale entire geometry if switching resolution
        old_x_pixel *= scale_factor
        old_y_pixel *= scale_factor

        # Compute offset from scaled original center
        dx = old_x_pixel - scaled_old_center
        dy = old_y_pixel - scaled_old_center

        # Apply shift to new center
        new_x_pixel = new_center_x + dx
        new_y_pixel = new_center_y + dy

        # Convert back to percentage for selected resolution
        new_points.append({
            "id": p["id"],
            "x_perc": round(new_x_pixel / image_size, 5),
            "y_perc": round(new_y_pixel / image_size, 5)
        })

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "label": "Custom Test",
        "points": new_points
    }


# --------------------------------------------------
# UI
# --------------------------------------------------

st.title("Isotropic Grid Generator")

# ---- ID INPUT ----
id_eye = st.text_input("ID_eye (e.g., 21222_OD)")

# ---- RESOLUTION SELECTOR ----
resolution_mode = st.radio(
    "Select Scan Mode",
    ["High Resolution (1536x1536)", "High Speed (768x768)"]
)

if resolution_mode == "High Resolution (1536x1536)":
    IMAGE_SIZE = 1536
else:
    IMAGE_SIZE = 768

# ---- COORDINATE INPUTS (INTEGER ONLY) ----
new_center_x = st.number_input(
    "New Center X",
    min_value=0,
    max_value=IMAGE_SIZE,
    value=IMAGE_SIZE // 2,
    step=1,
    format="%d"
)

new_center_y = st.number_input(
    "New Center Y",
    min_value=0,
    max_value=IMAGE_SIZE,
    value=IMAGE_SIZE // 2,
    step=1,
    format="%d"
)

st.divider()

# --------------------------------------------------
# GENERATE + DOWNLOAD (ONE CLICK)
# --------------------------------------------------

if id_eye:

    # Generate both grids
    new_dmp = shift_grid(
        dmp_data["points"],
        new_center_x,
        new_center_y,
        IMAGE_SIZE
    )

    new_hdt = shift_grid(
        hdt_data["points"],
        new_center_x,
        new_center_y,
        IMAGE_SIZE
    )

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            f"{id_eye}_DMP03.json",
            json.dumps(new_dmp, indent=2)
        )
        zf.writestr(
            f"{id_eye}_HDT03.json",
            json.dumps(new_hdt, indent=2)
        )

    zip_buffer.seek(0)

    st.download_button(
        label="Generate & Download Both Files",
        data=zip_buffer,
        file_name=f"{id_eye}_grids.zip",
        mime="application/zip"
    )

else:
    st.info("Enter ID_eye to enable download.")
