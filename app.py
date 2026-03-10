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
ORIGINAL_CENTER_PERC = ORIGINAL_CENTER / ORIGINAL_IMAGE_SIZE

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
# GRID SHIFT FUNCTION (SAFE VERSION)
# --------------------------------------------------

def shift_grid(original_points, new_center_x, new_center_y, image_size):

    # Convert new center into percentage coordinates
    new_center_perc_x = new_center_x / image_size
    new_center_perc_y = new_center_y / image_size

    new_points = []

    for p in original_points:

        dx = p["x_perc"] - ORIGINAL_CENTER_PERC
        dy = p["y_perc"] - ORIGINAL_CENTER_PERC

        new_points.append({
            "id": p["id"],
            "x_perc": round(new_center_perc_x + dx, 5),
            "y_perc": round(new_center_perc_y + dy, 5)
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
