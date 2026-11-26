"""
NutriScan AI — Main Application Entrypoint
Camera-first, real-time AI food recognition and nutritional analysis platform.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any, cast

# Ensure project root is on sys.path regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    CANONICAL_FOOD_CLASSES,
    CUSTOM_CSS_PATH,
    DEFAULT_CONFIDENCE_THRESHOLD,
    MEDIA_STREAM_CONSTRAINTS,
    RTC_CONFIGURATION,
    UNCERTAIN_LABEL,
)
from modules.camera import FoodVideoProcessor
from modules.detector import FoodDetector
from modules.history import MealHistoryManager
from modules.nutrition import NutritionAnalyzer
from modules.portion import PortionManager
from modules.recommendations import generate_meal_insights
from modules.visualization import (
    create_food_contribution_chart,
    create_macro_donut_chart,
    create_macro_grams_bar_chart,
)

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — Live Food Recognition",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Cached Core Services
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Initializing NutriScan AI detection engine...")
def get_detector() -> FoodDetector:
    return FoodDetector()


@st.cache_resource
def get_portion_manager() -> PortionManager:
    return PortionManager()


@st.cache_resource
def get_nutrition_analyzer() -> NutritionAnalyzer:
    return NutritionAnalyzer(portion_manager=get_portion_manager())


def get_history_manager() -> MealHistoryManager:
    return MealHistoryManager()


# ---------------------------------------------------------------------------
# Session State & Theme Helpers
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "dark_mode": False,
        "confirmed_detections": [],
        "latest_analysis": None,
        "nav_page": "Home / Live Scanner",
        "conf_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def apply_styling() -> None:
    if CUSTOM_CSS_PATH.exists():
        css = CUSTOM_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    if st.session_state.get("dark_mode", False):
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0B1120;
                color: #F8FAFC;
            }
            [data-testid="stSidebar"] {
                background-color: #111827;
                color: #F8FAFC;
            }
            .nutri-card {
                background: rgba(30, 41, 59, 0.72);
                border-color: rgba(148, 163, 184, 0.2);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


def make_detection_entry(
    food_name: str,
    confidence: float | None,
    bbox: list[int] | None,
    is_uncertain: bool,
    bbox_area_ratio: float = 0.0,
    source_tag: str = "Estimated default",
) -> dict[str, Any]:
    portion_mgr = get_portion_manager()
    safe_food = food_name if food_name in CANONICAL_FOOD_CLASSES else CANONICAL_FOOD_CLASSES[0]
    default_qty, default_unit = portion_mgr.get_default_portion(safe_food)
    visual_est_g = (
        portion_mgr.experimental_visual_estimate_grams(bbox_area_ratio)
        if bbox_area_ratio > 0
        else None
    )
    return {
        "uid": str(uuid.uuid4())[:8],
        "food_name": safe_food,
        "original_ai_label": food_name,
        "confidence": confidence,
        "bbox": bbox or [0, 0, 0, 0],
        "is_uncertain": is_uncertain,
        "quantity": default_qty,
        "unit": default_unit,
        "portion_source": source_tag,
        "experimental_visual_grams": visual_est_g,
        "confirmed": not is_uncertain,
    }


def sync_detections_from_live_stream(raw_detections: list[dict[str, Any]]) -> None:
    entries: list[dict[str, Any]] = []
    for det in raw_detections:
        raw_label = str(det.get("label", UNCERTAIN_LABEL))
        is_uncertain = bool(det.get("is_uncertain", False))
        mapped_name = raw_label if raw_label in CANONICAL_FOOD_CLASSES else CANONICAL_FOOD_CLASSES[0]
        entries.append(
            make_detection_entry(
                food_name=mapped_name if not is_uncertain else raw_label,
                confidence=det.get("confidence"),
                bbox=det.get("bbox"),
                is_uncertain=is_uncertain,
                bbox_area_ratio=float(det.get("bbox_area_ratio", 0.0)),
                source_tag="Estimated default",
            )
        )
    st.session_state["confirmed_detections"] = entries


# ---------------------------------------------------------------------------
# Page 1: Home / Live Scanner (Primary Feature)
# ---------------------------------------------------------------------------
def render_live_scanner_page(detector: FoodDetector) -> None:
    st.markdown(
        f"""
        <div class="nutri-hero">
            <h1>🥗 {APP_NAME} — Live Meal Scanner</h1>
            <p>{APP_TAGLINE} • Point your camera at a meal for continuous multi-food detection.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status = detector.get_status_summary()

    if not status["ready"]:
        st.error(
            f"**AI Model Not Ready:** {status['error']}\n\n"
            "Run `python models/download_weights.py` in your terminal and refresh the app."
        )
    elif status["mode"] == "custom":
        st.success(
            "**Model Active:** Custom 40-Class Indian & International Food YOLO Model "
            f"(`{status['weights_path']}`)"
        )
    else:
        st.info(
            "**Model Active:** Base Pretrained YOLO (`yolo11n.pt`). Directly detects standard COCO "
            "foods (Apple, Banana, Orange, Pizza, Sandwich, Cake) and flags bowls/cups/other "
            "items as *Uncertain Food Item* for quick confirmation. Train on the 40-class dataset "
            "in `training/` to unlock full Indian + International dish recognition."
        )

    ctrl_col1, ctrl_col2 = st.columns([2, 1])
    with ctrl_col1:
        conf_threshold = st.slider(
            "AI Detection Confidence Threshold",
            min_value=0.15,
            max_value=0.85,
            value=float(st.session_state["conf_threshold"]),
            step=0.05,
            help="Lower values detect more items but may increase uncertain labels.",
        )
        st.session_state["conf_threshold"] = conf_threshold
    with ctrl_col2:
        st.markdown(
            "<div class='nutri-card'><strong>Camera Permissions</strong><br/>"
            "<span style='font-size:0.85rem;opacity:0.85;'>Click <b>START</b> below and allow "
            "browser camera access. Mobile browsers automatically prefer the rear camera.</span></div>",
            unsafe_allow_html=True,
        )

    scanner_col, info_col = st.columns([1.45, 1.0], gap="large")

    with scanner_col:
        st.subheader("Live Camera Feed")

        initial_conf = float(conf_threshold)

        def processor_factory() -> FoodVideoProcessor:
            proc = FoodVideoProcessor(detector=detector)
            proc.set_confidence_threshold(initial_conf)
            return proc

        webrtc_ctx = webrtc_streamer(
            key="nutriscan-live-camera",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints=MEDIA_STREAM_CONSTRAINTS,
            video_processor_factory=processor_factory,
            async_processing=True,
        )

        video_proc = cast(FoodVideoProcessor | None, webrtc_ctx.video_processor)
        if video_proc is not None:
            video_proc.set_confidence_threshold(conf_threshold)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            sync_clicked = st.button(
                "Capture & Sync Live Detections",
                type="primary",
                use_container_width=True,
                disabled=not webrtc_ctx.state.playing,
            )
        with btn_col2:
            if st.button("Clear Current Detections", use_container_width=True):
                st.session_state["confirmed_detections"] = []
                st.rerun()

        if sync_clicked and video_proc is not None:
            live_dets = video_proc.get_latest_detections()
            if live_dets:
                sync_detections_from_live_stream(live_dets)
                st.success(f"Synced {len(live_dets)} detected item(s) into the confirmation panel.")
            else:
                st.warning(
                    "No food items detected in the current live frame. "
                    "Hold the camera steady, improve lighting, or adjust the confidence slider."
                )

        if webrtc_ctx.state.playing and video_proc is not None:
            fps = video_proc.get_fps()
            live_now = video_proc.get_latest_detections()
            st.caption(f"Streaming live • ~{fps:.1f} FPS • {len(live_now)} object(s) in current frame")
        elif not webrtc_ctx.state.playing:
            st.caption(
                "Stream stopped. Press START above to activate your camera. "
                "If camera access fails on a mobile browser over LAN HTTP, see 'About NutriScan' for HTTPS setup."
            )

        with st.expander("Fallback: Analyze Meal Photo Upload (When Browser Camera Is Blocked)"):
            uploaded_file = st.file_uploader(
                "Upload a meal image (JPG / PNG)",
                type=["jpg", "jpeg", "png"],
                key="fallback_uploader",
            )
            if uploaded_file is not None and detector.is_ready:
                pil_img = Image.open(uploaded_file).convert("RGB")
                img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                dets = detector.detect(img_bgr, conf_threshold=conf_threshold)
                annotated = detector.draw_detections(img_bgr, dets, model_mode=detector.model_mode)
                st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
                if st.button("Load Photo Detections to Panel", key="load_photo_dets"):
                    sync_detections_from_live_stream([d.to_dict() for d in dets])
                    st.success(f"Loaded {len(dets)} detection(s) from image.")

    with info_col:
        st.subheader("Detection Confirmation Panel")
        st.caption(
            "Review AI detections, relabel uncertain items, and confirm real portions before analysis."
        )

        detections_list: list[dict[str, Any]] = st.session_state["confirmed_detections"]
        portion_mgr = get_portion_manager()

        if not detections_list:
            st.markdown(
                "<div class='nutri-card'>"
                "<strong>Waiting for Detections</strong><br/>"
                "<span style='font-size:0.9rem;opacity:0.85;'>"
                "1. Press <b>START</b> on the live camera.<br/>"
                "2. Point at your meal until bounding boxes appear.<br/>"
                "3. Click <b>Capture & Sync Live Detections</b> to confirm portions."
                "</span></div>",
                unsafe_allow_html=True,
            )
        else:
            indices_to_remove: list[int] = []
            for idx, item in enumerate(detections_list):
                uid = item["uid"]
                is_uncertain = item.get("is_uncertain", False)
                conf_val = item.get("confidence")
                conf_str = f"{conf_val * 100:.0f}%" if conf_val is not None else "Manual"
                badge_html = (
                    f"<span class='nutri-badge-warn'>Uncertain ({conf_str})</span>"
                    if is_uncertain
                    else f"<span class='nutri-badge-ok'>AI Detected ({conf_str})</span>"
                )
                provenance_badge = f"<span class='nutri-badge-info'>{item['portion_source']}</span>"

                with st.container(border=True):
                    st.markdown(
                        f"**Item #{idx + 1}** &nbsp; {badge_html} &nbsp; {provenance_badge}",
                        unsafe_allow_html=True,
                    )
                    if is_uncertain:
                        st.caption(
                            f"Raw AI output: `{item['original_ai_label']}` — please select the exact dish below."
                        )
                    st.caption(f"Bounding box [x1, y1, x2, y2]: `{item['bbox']}`")

                    current_idx = (
                        CANONICAL_FOOD_CLASSES.index(item["food_name"])
                        if item["food_name"] in CANONICAL_FOOD_CLASSES
                        else 0
                    )
                    selected_food = st.selectbox(
                        "Food Label (Editable)",
                        options=CANONICAL_FOOD_CLASSES,
                        index=current_idx,
                        key=f"food_select_{uid}",
                    )
                    if selected_food != item["food_name"]:
                        item["food_name"] = selected_food
                        item["is_uncertain"] = False
                        def_qty, def_unit = portion_mgr.get_default_portion(selected_food)
                        item["quantity"] = def_qty
                        item["unit"] = def_unit
                        item["portion_source"] = "Estimated default"

                    avail_units = portion_mgr.get_available_units(item["food_name"])
                    unit_idx = avail_units.index(item["unit"]) if item["unit"] in avail_units else 0

                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        new_qty = st.number_input(
                            "Quantity",
                            min_value=0.1,
                            max_value=2000.0,
                            value=float(item["quantity"]),
                            step=0.5 if item["unit"] != "Grams (g)" else 10.0,
                            key=f"qty_{uid}",
                        )
                    with p_col2:
                        new_unit = st.selectbox(
                            "Unit",
                            options=avail_units,
                            index=unit_idx,
                            key=f"unit_{uid}",
                        )

                    if new_qty != item["quantity"] or new_unit != item["unit"]:
                        item["quantity"] = new_qty
                        item["unit"] = new_unit
                        item["portion_source"] = "User-confirmed"

                    est_grams, conv_note = portion_mgr.convert_to_grams(
                        item["food_name"], item["quantity"], item["unit"]
                    )
                    st.caption(f"Calculated weight: **{est_grams:.1f} g** ({conv_note})")

                    if item.get("experimental_visual_grams"):
                        st.caption(
                            f"Experimental visual bbox estimate: ~{item['experimental_visual_grams']:.0f} g "
                            "(2D camera heuristic only — confirm actual portion above)."
                        )

                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        confirm_toggle = st.checkbox(
                            "Confirmed",
                            value=bool(item.get("confirmed", True)),
                            key=f"confirm_{uid}",
                        )
                        item["confirmed"] = confirm_toggle
                    with act_col2:
                        if st.button("Remove", key=f"remove_{uid}", use_container_width=True):
                            indices_to_remove.append(idx)

            if indices_to_remove:
                for idx in sorted(indices_to_remove, reverse=True):
                    detections_list.pop(idx)
                st.rerun()

        with st.expander("+ Add Missed Food Manually (Secondary Correction)"):
            m_food = st.selectbox(
                "Select Food",
                options=CANONICAL_FOOD_CLASSES,
                key="manual_add_food",
            )
            m_units = portion_mgr.get_available_units(m_food)
            m_def_qty, m_def_unit = portion_mgr.get_default_portion(m_food)
            mc1, mc2 = st.columns(2)
            with mc1:
                m_qty = st.number_input(
                    "Quantity", min_value=0.1, max_value=2000.0, value=float(m_def_qty), key="manual_qty"
                )
            with mc2:
                m_unit = st.selectbox(
                    "Unit",
                    options=m_units,
                    index=m_units.index(m_def_unit) if m_def_unit in m_units else 0,
                    key="manual_unit",
                )
            if st.button("Add to Meal", key="manual_add_btn", use_container_width=True):
                entry = make_detection_entry(
                    food_name=m_food,
                    confidence=None,
                    bbox=None,
                    is_uncertain=False,
                    source_tag="User-entered",
                )
                entry["quantity"] = m_qty
                entry["unit"] = m_unit
                entry["confirmed"] = True
                st.session_state["confirmed_detections"].append(entry)
                st.rerun()

        confirmed_only = [d for d in st.session_state["confirmed_detections"] if d.get("confirmed")]
        if confirmed_only:
            meal_title = st.text_input(
                "Meal Label (Optional)",
                value="Lunch / Meal Scan",
                key="meal_label_input",
            )
            if st.button(
                f"Analyze Nutrition ({len(confirmed_only)} Confirmed Item(s))",
                type="primary",
                use_container_width=True,
            ):
                analyzer = get_nutrition_analyzer()
                analysis = analyzer.analyze_meal(confirmed_only)
                st.session_state["latest_analysis"] = analysis
                history_mgr = get_history_manager()
                history_mgr.save_meal(analysis, meal_label=meal_title)
                st.session_state["nav_page"] = "Nutrition Dashboard"
                st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Nutrition Dashboard
# ---------------------------------------------------------------------------
def render_dashboard_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <h1>📊 Nutrition Dashboard</h1>
            <p>Detailed macronutrient breakdown, food-level contributions, and educational meal balance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analysis = st.session_state.get("latest_analysis")
    if not analysis or not analysis.get("items"):
        st.info("No meal analyzed yet. Head to **Home / Live Scanner** to scan a meal first.")
        if st.button("Go to Live Scanner", type="primary"):
            st.session_state["nav_page"] = "Home / Live Scanner"
            st.rerun()
        return

    totals = analysis["totals"]
    items = analysis["items"]
    dark_mode = bool(st.session_state.get("dark_mode", False))

    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "Calories", f"{totals['total_calories']:.0f} kcal"),
        (k2, "Protein", f"{totals['total_protein_g']:.1f} g"),
        (k3, "Carbs", f"{totals['total_carbs_g']:.1f} g"),
        (k4, "Fat", f"{totals['total_fat_g']:.1f} g"),
        (k5, "Fibre", f"{totals['total_fibre_g']:.1f} g"),
    ]
    for col, label, val in kpis:
        with col:
            st.markdown(
                f"<div class='nutri-kpi'><div class='nutri-kpi-label'>{label}</div>"
                f"<div class='nutri-kpi-value'>{val}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            create_macro_donut_chart(analysis, dark_mode=dark_mode),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            create_food_contribution_chart(analysis, dark_mode=dark_mode),
            use_container_width=True,
        )

    st.plotly_chart(
        create_macro_grams_bar_chart(analysis, dark_mode=dark_mode),
        use_container_width=True,
    )

    st.subheader("Confirmed Meal Items & Portion Provenance")
    for item in items:
        with st.container(border=True):
            top_l, top_r = st.columns([2, 1])
            with top_l:
                st.markdown(
                    f"**{item['food_name']}** ({item['category']}) — "
                    f"`{item['quantity']} {item['unit']}` (~{item['grams']:.1f} g)"
                )
                st.caption(
                    f"Portion source: **{item['portion_source']}** | "
                    f"Data ref: {item['source']} | Note: {item['notes']}"
                )
            with top_r:
                st.markdown(
                    f"**{item['calories']:.0f} kcal** • "
                    f"P: {item['protein_g']:.1f}g | C: {item['carbs_g']:.1f}g | "
                    f"F: {item['fat_g']:.1f}g | Fib: {item['fibre_g']:.1f}g"
                )

    st.subheader("General Meal-Balance Insights (Educational)")
    for insight in generate_meal_insights(analysis):
        if insight["type"] == "positive":
            st.success(f"**{insight['title']}:** {insight['message']}")
        elif insight["type"] == "tip":
            st.warning(f"**{insight['title']}:** {insight['message']}")
        else:
            st.info(f"**{insight['title']}:** {insight['message']}")

    st.caption(
        "Disclaimer: Nutritional estimates are derived from standard USDA FoodData Central and "
        "ICMR-NIN reference values. Actual values vary based on recipe, cooking oil/ghee, and "
        "exact weights. NutriScan AI provides general informational insights and is not a medical tool."
    )

    export_df = pd.DataFrame(items)
    st.download_button(
        label="Export Meal Breakdown (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="nutriscan_meal_analysis.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Page 3: Meal History
# ---------------------------------------------------------------------------
def render_history_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <h1>🕒 Meal History</h1>
            <p>Review previously scanned meals and export your nutrition log.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history_mgr = get_history_manager()
    df = history_mgr.load_history()

    if df.empty:
        st.info("No saved meals yet. Analyze a meal from the Live Scanner to record history.")
        return

    avg_cal = float(pd.to_numeric(df["total_calories"], errors="coerce").fillna(0).mean())
    sum_prot = float(pd.to_numeric(df["total_protein_g"], errors="coerce").fillna(0).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Logged Meals", len(df))
    m2.metric("Average Meal Calories", f"{avg_cal:.0f} kcal")
    m3.metric("Total Protein Logged", f"{sum_prot:.1f} g")

    st.dataframe(df, use_container_width=True, hide_index=True)

    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.download_button(
            "Download Full History (CSV)",
            data=history_mgr.export_csv_bytes(),
            file_name="nutriscan_meal_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with h_col2:
        if st.button("Clear Meal History", use_container_width=True):
            history_mgr.clear_history()
            st.success("Meal history cleared.")
            st.rerun()


# ---------------------------------------------------------------------------
# Page 4: Food Database
# ---------------------------------------------------------------------------
def render_database_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <h1>📚 Food Nutrition & Portion Database</h1>
            <p>Traceable Indian & International reference data (per 100g) and standard serving weights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analyzer = get_nutrition_analyzer()
    portion_mgr = get_portion_manager()

    f1, f2 = st.columns([2, 1])
    with f1:
        search_q = st.text_input("Search food name", placeholder="e.g., Dal, Idli, Grilled chicken...")
    with f2:
        category_filter = st.selectbox("Category", ["All", "Indian", "International"])

    df = analyzer.df.copy()
    if category_filter != "All":
        df = df[df["category"] == category_filter]
    if search_q.strip():
        df = df[df["food_name"].str.contains(search_q.strip(), case=False, na=False)]

    st.subheader(f"Nutritional Composition ({len(df)} foods)")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Standard Portion Weight References (g)")
    st.dataframe(portion_mgr.df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 5: About NutriScan
# ---------------------------------------------------------------------------
def render_about_page() -> None:
    st.markdown(
        f"""
        <div class="nutri-hero">
            <h1>ℹ️ About {APP_NAME} (v{APP_VERSION})</h1>
            <p>Technical architecture, honest AI boundaries, and mobile HTTPS deployment guide.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Real-Time Computer Vision Architecture
        NutriScan AI uses **Ultralytics YOLO** over a live **Streamlit-WebRTC** media stream
        and **OpenCV** frame pipeline to detect multiple food items simultaneously in real time.

        ### Model Transparency & Custom Training
        - **Base Pretrained Mode (`yolo11n.pt`):** Ready out-of-the-box for standard COCO food
          categories (`Apple`, `Banana`, `Orange`, `Pizza`, `Sandwich`, `Cake`). When bowls,
          cups, or unfamiliar dishes appear, NutriScan AI flags them honestly as
          *Uncertain Food Item* rather than guessing an unverified dish name.
        - **Custom 40-Class Mode (`models/nutriscan_food_yolo.pt`):** Use the included
          `training/` pipeline (`prepare_dataset.py`, `dataset.yaml`, `train.py`, `validate.py`)
          to fine-tune YOLO across all 20 Indian and 20 International dishes.

        ### RGB Portion Estimation Limitations
        A standard 2D RGB camera cannot measure food depth, density, oil absorption, or exact mass.
        NutriScan AI clearly distinguishes:
        - **User-confirmed** portions (grams, pieces, cups, katoris, ml, servings)
        - **Estimated default** reference servings
        - **Experimental visual estimates** (2D bounding-box area heuristics)

        ### Mobile Browser Camera & HTTPS Requirements
        Modern mobile browsers (iOS Safari, Android Chrome) enforce **Secure Context** rules:
        `navigator.mediaDevices.getUserMedia()` is **blocked** on plain `http://192.168.x.x:8501` LAN URLs.
        `localhost` camera access works on the host computer only — it does **not** automatically grant
        camera permission to a phone on the same Wi-Fi.

        To test live mobile rear-camera scanning from your phone:
        1. **Cloudflare Tunnel (Fastest, Free):** Run `cloudflared tunnel --url http://localhost:8501`
           and open the generated `https://...trycloudflare.com` URL on your phone.
        2. **ngrok:** Run `ngrok http 8501` and open the `https://` forwarding URL on your phone.
        3. **Cloud Deployment:** Deploy to Streamlit Community Cloud or any HTTPS-enabled server.
        """
    )


# ---------------------------------------------------------------------------
# Main Application Shell
# ---------------------------------------------------------------------------
def main() -> None:
    init_session_state()
    apply_styling()

    detector = get_detector()

    with st.sidebar:
        st.markdown(f"## 🥗 {APP_NAME}")
        st.caption(f"Version {APP_VERSION}")

        pages = [
            "Home / Live Scanner",
            "Nutrition Dashboard",
            "Meal History",
            "Food Database",
            "About NutriScan",
        ]
        current_idx = (
            pages.index(st.session_state["nav_page"])
            if st.session_state["nav_page"] in pages
            else 0
        )
        selected_page = st.radio("Navigation", pages, index=current_idx)
        st.session_state["nav_page"] = selected_page

        st.divider()
        dark_toggle = st.toggle("Dark Theme", value=bool(st.session_state["dark_mode"]))
        if dark_toggle != st.session_state["dark_mode"]:
            st.session_state["dark_mode"] = dark_toggle
            st.rerun()

        st.divider()
        status = detector.get_status_summary()
        st.caption(
            f"**Engine:** {'Custom 40-Class' if status['mode'] == 'custom' else 'Base Pretrained' if status['ready'] else 'Weights Missing'}"
        )

    if selected_page == "Home / Live Scanner":
        render_live_scanner_page(detector)
    elif selected_page == "Nutrition Dashboard":
        render_dashboard_page()
    elif selected_page == "Meal History":
        render_history_page()
    elif selected_page == "Food Database":
        render_database_page()
    elif selected_page == "About NutriScan":
        render_about_page()


if __name__ == "__main__":
    main()