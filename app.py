import streamlit as st
import json
import zipfile
import io
from pathlib import Path

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

ORIGINAL_IMAGE_SIZE = 1536
ORIGINAL_CENTER = 768

BASE_DIR = Path(__file__).parent

# --------------------------------------------------
# LOAD BASE GRIDS (CACHED)
# --------------------------------------------------

@st.cache_data
def load_grids():
    with open(BASE_DIR / "DMP03.json") as f:
        dmp = json.load(f)

    with open(BASE_DIR / "HDT03.json") as f:
        hdt = json.load(f)

    return dmp, hdt


# --------------------------------------------------
# GRID SHIFT FUNCTION
# --------------------------------------------------

def shift_grid(original_points, new_center_x, new_center_y, image_size):

    scale_factor = image_size / ORIGINAL_IMAGE_SIZE
    scaled_old_center = ORIGINAL_CENTER * scale_factor

    new_points = []

    for p in original_points:

        old_x_pixel = p["x_perc"] * ORIGINAL_IMAGE_SIZE
        old_y_pixel = p["y_perc"] * ORIGINAL_IMAGE_SIZE

        old_x_pixel *= scale_factor
        old_y_pixel *= scale_factor

        dx = old_x_pixel - scaled_old_center
        dy = old_y_pixel - scaled_old_center

        new_x_pixel = new_center_x + dx
        new_y_pixel = new_center_y + dy

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

# Load grids safely
try:
    dmp_data, hdt_data = load_grids()
except Exception as e:
    st.error("Failed to load grid templates.")
    st.exception(e)
    st.stop()

# ---- ID INPUT ----

id_eye = st.text_input("ID_eye (e.g., 21222_OD)")

# ---- RESOLUTION ----

resolution_mode = st.radio(
    "Select Scan Mode",
    ["High Resolution (1536x1536)", "High Speed (768x768)"]
)

IMAGE_SIZE = 1536 if "1536" in resolution_mode else 768

# ---- CENTER INPUTS ----

new_center_x = st.number_input(
    "New Center X",
    min_value=0,
    max_value=IMAGE_SIZE,
    value=IMAGE_SIZE // 2,
    step=1
)

new_center_y = st.number_input(
    "New Center Y",
    min_value=0,
    max_value=IMAGE_SIZE,
    value=IMAGE_SIZE // 2,
    step=1
)

st.divider()

# --------------------------------------------------
# GENERATE FILES
# --------------------------------------------------

if id_eye:

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
        "Generate & Download Both Files",
        data=zip_buffer,
        file_name=f"{id_eye}_grids.zip",
        mime="application/zip"
    )

else:
    st.info("Enter ID_eye to enable download.")
