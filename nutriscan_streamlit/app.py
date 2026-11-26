"""
NutriScan AI — Main Application Entrypoint
Scan. Understand. Nourish.
Intelligent food recognition, portion confirmation, and Meal Intelligence platform.
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

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

try:
    import cv2
except ModuleNotFoundError:
    st.error(
        "OpenCV (`cv2`) is not installed in this environment. "
        "Make sure `requirements.txt` (with `opencv-python-headless`) and `packages.txt` "
        "are in the root of your repository, select Python 3.11 in Streamlit Cloud Advanced Settings, "
        "and click Manage app -> Reboot app."
    )
    st.stop()

try:
    from streamlit_webrtc import WebRtcMode, webrtc_streamer
except ModuleNotFoundError as exc:
    st.error(
        f"Missing Python package `{exc.name}`. Check that `requirements.txt` is in your "
        f"repository root (`{PROJECT_ROOT}`) and reboot the app."
    )
    st.stop()

from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    APP_VERSION,
    CANONICAL_FOOD_CLASSES,
    CUSTOM_CSS_PATH,
    DEFAULT_CONFIDENCE_THRESHOLD,
    MEDIA_STREAM_CONSTRAINTS,
    RTC_CONFIGURATION,
    UNCERTAIN_LABEL,
)


def _import_project_modules() -> tuple[Any, ...]:
    """
    Imports NutriScan domain modules cleanly across standard (`modules/`),
    capitalized (`Modules/`), or flat-root repository layouts.
    """
    import importlib

    # Support repositories where files were uploaded inside `Modules/` or flat in root
    alt_dirs = [PROJECT_ROOT / "Modules", PROJECT_ROOT / "nutriscan_streamlit"]
    for alt in alt_dirs:
        if alt.is_dir() and str(alt) not in sys.path:
            sys.path.insert(0, str(alt))

    def _load(mod_name: str):
        for prefix in ("modules.", ""):
            try:
                return importlib.import_module(f"{prefix}{mod_name}")
            except ModuleNotFoundError as exc:
                # Only fall back if the missing module is the prefix/module itself,
                # not a third-party dependency inside the module (e.g. `av`, `ultralytics`).
                if exc.name not in ("modules", f"modules.{mod_name}", mod_name):
                    raise
        raise ModuleNotFoundError(
            f"Could not locate '{mod_name}.py' in '{PROJECT_ROOT / 'modules'}' or '{PROJECT_ROOT}'",
            name=f"modules.{mod_name}",
        )

    camera_mod = _load("camera")
    detector_mod = _load("detector")
    history_mod = _load("history")
    intel_mod = _load("meal_intelligence")
    nutrition_mod = _load("nutrition")
    portion_mod = _load("portion")
    viz_mod = _load("visualization")

    return (
        camera_mod.FoodVideoProcessor,
        detector_mod.FoodDetector,
        history_mod.MealHistoryManager,
        intel_mod.analyze_meal_intelligence,
        nutrition_mod.NutritionAnalyzer,
        portion_mod.PortionManager,
        viz_mod.create_food_contribution_chart,
        viz_mod.create_history_trend_chart,
        viz_mod.create_macro_donut_chart,
        viz_mod.create_macro_grams_bar_chart,
        viz_mod.create_top_foods_chart,
    )


try:
    (
        FoodVideoProcessor,
        FoodDetector,
        MealHistoryManager,
        analyze_meal_intelligence,
        NutritionAnalyzer,
        PortionManager,
        create_food_contribution_chart,
        create_history_trend_chart,
        create_macro_donut_chart,
        create_macro_grams_bar_chart,
        create_top_foods_chart,
    ) = _import_project_modules()
except ModuleNotFoundError as exc:
    root_entries = sorted(p.name for p in PROJECT_ROOT.iterdir())
    modules_dir = PROJECT_ROOT / "modules"
    mod_entries = sorted(p.name for p in modules_dir.iterdir()) if modules_dir.is_dir() else []
    st.error(
        f"**ModuleNotFoundError:** Missing `{exc.name}`\n\n"
        f"- **Repo root (`{PROJECT_ROOT}`):** `{root_entries}`\n"
        f"- **`modules/` contents:** `{mod_entries if mod_entries else 'folder not found'}`\n\n"
        "Make sure all module files (`camera.py`, `detector.py`, `history.py`, "
        "`meal_intelligence.py`, `nutrition.py`, `portion.py`, `visualization.py`) "
        "are committed to GitHub inside `modules/` and all packages in `requirements.txt` are installed."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="leaf",
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
# Session State & Styling
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "confirmed_detections": [],
        "latest_analysis": None,
        "nav_page": "Home / Live Scanner",
        "conf_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "scanner_active": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def apply_styling() -> None:
    if CUSTOM_CSS_PATH.exists():
        css = CUSTOM_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def make_detection_entry(
    food_name: str,
    confidence: float | None,
    bbox: list[int] | None,
    is_uncertain: bool,
    bbox_area_ratio: float = 0.0,
    source_tag: str = "Estimated default",
    verification_status: str = "Confirmed by user",
) -> dict[str, Any]:
    portion_mgr = get_portion_manager()
    is_known = food_name in CANONICAL_FOOD_CLASSES
    safe_food = food_name if is_known else ""
    default_qty, default_unit = (
        portion_mgr.get_default_portion(safe_food) if safe_food else (1.0, "Servings")
    )
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
        "is_uncertain": is_uncertain or not is_known,
        "quantity": default_qty,
        "unit": default_unit,
        "portion_source": source_tag,
        "experimental_visual_grams": visual_est_g,
        "confirmed": (not is_uncertain) and is_known,
        "verification_status": (
            "Uncertain — requires verification" if (is_uncertain or not is_known) else verification_status
        ),
    }


def sync_detections_from_live_stream(raw_detections: list[dict[str, Any]]) -> None:
    entries: list[dict[str, Any]] = []
    for det in raw_detections:
        raw_label = str(det.get("label", UNCERTAIN_LABEL))
        is_uncertain = bool(det.get("is_uncertain", False))
        entries.append(
            make_detection_entry(
                food_name=raw_label,
                confidence=det.get("confidence"),
                bbox=det.get("bbox"),
                is_uncertain=is_uncertain,
                bbox_area_ratio=float(det.get("bbox_area_ratio", 0.0)),
                source_tag="Estimated default",
                verification_status="Confirmed AI prediction",
            )
        )
    st.session_state["confirmed_detections"] = entries


# ---------------------------------------------------------------------------
# Shared UI Components: Meal Intelligence & AI Detection Insights
# ---------------------------------------------------------------------------
def render_meal_intelligence_card(analysis: dict[str, Any]) -> None:
    intel = analyze_meal_intelligence(analysis)
    balance = intel["nutritional_balance"]
    variety = intel["food_group_variety"]
    composition = intel["composition"]
    suggestions = intel["contextual_suggestions"]

    st.markdown(
        """
        <div class="nutri-intelligence-card">
            <div class="nutri-intelligence-header">
                <div class="nutri-hero-kicker">Signature Feature</div>
                <h2 class="nutri-editorial" style="margin:0;font-size:1.6rem;">NutriScan Meal Intelligence</h2>
                <p style="margin:0.35rem 0 0 0;color:#758276;font-size:0.94rem;">
                    Holistic educational analysis of your complete plate, food-group representation, and nutrient balance.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='nutri-section-title'>1. Meal Composition</div>", unsafe_allow_html=True)
        if not composition:
            st.caption("No database-matched items available for composition breakdown.")
        else:
            for entry in composition:
                st.markdown(
                    f"""
                    <div class="nutri-card" style="padding:0.85rem 1rem;margin-bottom:0.65rem;">
                        <div style="display:flex;justify-content:space-between;align-items:baseline;">
                            <strong>{entry['food_name']}</strong>
                            <span style="font-variant-numeric:tabular-nums;font-weight:600;color:#294C38;">
                                {entry['calories']:.0f} kcal ({entry['calorie_share_pct']:.0f}%)
                            </span>
                        </div>
                        <div class="nutri-meta-row">
                            {entry['food_group']} &middot; {entry['portion_label']} ({entry['grams']:.0f} g) &middot;
                            P {entry['protein_g']:.1f}g &middot; C {entry['carbs_g']:.1f}g &middot; F {entry['fat_g']:.1f}g
                        </div>
                        <div class="nutri-bar-track">
                            <div class="nutri-bar-fill" style="width:{min(entry['calorie_share_pct'], 100):.0f}%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with c2:
        st.markdown("<div class='nutri-section-title'>2. Nutritional Balance</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="nutri-card-mint">
                <p style="margin:0;color:#25352B;line-height:1.6;">{balance['summary']}</p>
                <div class="nutri-meta-row" style="margin-top:0.65rem;color:#294C38;">
                    Protein: <strong>{balance['protein_g']:.1f} g ({balance['protein_pct']:.0f}%)</strong> &middot;
                    Carbs: <strong>{balance['carbs_g']:.1f} g ({balance['carbs_pct']:.0f}%)</strong> &middot;
                    Fat: <strong>{balance['fat_g']:.1f} g ({balance['fat_pct']:.0f}%)</strong> &middot;
                    Fibre: <strong>{balance['fibre_g']:.1f} g</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='nutri-section-title' style='margin-top:1rem;'>3. Food-Group Variety</div>", unsafe_allow_html=True)
        rep_text = (
            " &middot; ".join(
                f"<strong>{g['group']}</strong> ({', '.join(g['items'])})"
                for g in variety["represented"]
            )
            if variety["represented"]
            else "None recorded"
        )
        unrep_text = (
            ", ".join(variety["unrepresented"])
            if variety["unrepresented"]
            else "All primary food groups are represented on this plate."
        )
        st.markdown(
            f"""
            <div class="nutri-card">
                <div class="nutri-meta-row"><strong>Represented on this plate:</strong> {rep_text}</div>
                <div class="nutri-meta-row" style="margin-top:0.5rem;">
                    <strong>Not represented in this meal:</strong> {unrep_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='nutri-section-title'>4. Contextual Suggestions</div>", unsafe_allow_html=True)
    for suggestion in suggestions:
        st.markdown(
            f"<div class='nutri-card-tinted' style='margin-bottom:0.6rem;'>{suggestion}</div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "Educational observations are generated strictly from your confirmed portions and reference database values. "
        "NutriScan AI does not label foods as good or bad and does not provide medical advice."
    )


def render_ai_detection_insights(items: list[dict[str, Any]]) -> None:
    st.subheader("AI Detection Insights")
    st.caption(
        "Transparent record of model detections, actual confidence scores where available, and human verifications."
    )
    if not items:
        st.info("No items analysed yet.")
        return

    rows: list[dict[str, Any]] = []
    for item in items:
        conf = item.get("confidence")
        conf_display = f"{conf * 100:.1f}%" if conf is not None else "Not available (manual entry)"
        rows.append(
            {
                "Confirmed Food": item["food_name"],
                "Food Group": item.get("food_group", "Other"),
                "Original AI Output": item.get("original_ai_label") or "Manual entry",
                "Model Confidence": conf_display,
                "Verification Status": item.get("verification_status", "Confirmed by user"),
                "Portion Source": item.get("portion_source", "User-confirmed"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 1: Home / Live Food Scanner
# ---------------------------------------------------------------------------
def render_live_scanner_page(detector: FoodDetector) -> None:
    st.markdown(
        f"""
        <div class="nutri-hero">
            <div class="nutri-hero-kicker">{APP_NAME} &middot; {APP_TAGLINE}</div>
            <h1>{APP_SUBTITLE}</h1>
            <p>
                Point your camera or upload a meal photo for deep-learning food detection,
                confirm familiar Indian or international portions, and uncover holistic Meal Intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analyzer = get_nutrition_analyzer()
    portion_mgr = get_portion_manager()
    if analyzer.load_error:
        st.error(analyzer.load_error)
    if portion_mgr.load_error:
        st.error(portion_mgr.load_error)

    status = detector.get_status_summary()
    if not status["ready"]:
        st.error(
            f"**YOLO Model Weights Unavailable:** {status['error']}\n\n"
            "Detection is paused until weights are available. You may still log foods manually below "
            "or run `python models/download_weights.py`."
        )
    elif status["mode"] == "custom":
        st.markdown(
            f"<div class='nutri-card-mint'><strong>Active Detection Engine:</strong> Custom 40-Class Indian &amp; International YOLO Model "
            f"<code>{status['weights_path']}</code> &middot; Recognises {len(status['supported_classes'])} trained classes.</div>",
            unsafe_allow_html=True,
        )
    else:
        supported = ", ".join(status["supported_classes"])
        st.markdown(
            f"<div class='nutri-card-tinted'><strong>Active Detection Engine:</strong> Base Pretrained YOLO (<code>yolo11n.pt</code>). "
            f"Directly trained to recognise: <strong>{supported}</strong>. Bowls, plates, and everyday Indian dishes are transparently flagged "
            f"as <em>Uncertain Food Item</em> for quick human verification rather than guessed.</div>",
            unsafe_allow_html=True,
        )

    top_a, top_b = st.columns([2, 1])
    with top_a:
        conf_threshold = st.slider(
            "Detection Confidence Threshold",
            min_value=0.15,
            max_value=0.85,
            value=float(st.session_state["conf_threshold"]),
            step=0.05,
            help="Detections below 45% confidence are automatically flagged for manual verification.",
        )
        st.session_state["conf_threshold"] = conf_threshold
    with top_b:
        if not st.session_state["scanner_active"]:
            st.markdown("<div style='height:0.65rem;'></div>", unsafe_allow_html=True)
            if st.button("Start Scanning", type="primary", use_container_width=True):
                st.session_state["scanner_active"] = True
                st.rerun()
        else:
            st.markdown(
                "<div class='nutri-card' style='padding:0.75rem 1rem;margin-bottom:0;'>"
                "<strong>Scanner Ready</strong><br/>"
                "<span class='nutri-meta-row'>Allow camera access below or switch to photo upload.</span></div>",
                unsafe_allow_html=True,
            )

    scanner_col, verify_col = st.columns([1.35, 1.0], gap="large")

    # Left Column: Camera Input & Image Upload
    with scanner_col:
        st.subheader("Food Input & Live Detection")
        tab_cam, tab_upload = st.tabs(["Live Camera Feed", "Upload Meal Photo"])

        with tab_cam:
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

            btn_1, btn_2 = st.columns(2)
            with btn_1:
                sync_clicked = st.button(
                    "Capture & Verify Detections",
                    type="primary",
                    use_container_width=True,
                    disabled=not webrtc_ctx.state.playing,
                )
            with btn_2:
                if st.button("Clear Plate", use_container_width=True):
                    st.session_state["confirmed_detections"] = []
                    st.rerun()

            if sync_clicked and video_proc is not None:
                live_dets = video_proc.get_latest_detections()
                if live_dets:
                    sync_detections_from_live_stream(live_dets)
                    st.success(f"Synced {len(live_dets)} detection(s) for verification.")
                else:
                    st.warning(
                        "No supported food items were detected in the current frame. "
                        "Improve lighting, adjust the confidence slider, or add items manually."
                    )

            if webrtc_ctx.state.playing and video_proc is not None:
                fps = video_proc.get_fps()
                live_now = video_proc.get_latest_detections()
                st.caption(f"Live stream active · {fps:.1f} FPS · {len(live_now)} object(s) detected")
            else:
                st.caption(
                    "Press START above to activate your camera (mobile browsers automatically prefer the rear camera). "
                    "If your browser blocks camera access over HTTP, use the Upload Meal Photo tab."
                )

        with tab_upload:
            uploaded_file = st.file_uploader(
                "Upload a meal photograph (JPG, PNG, WebP)",
                type=["jpg", "jpeg", "png", "webp"],
                key="meal_photo_uploader",
            )
            if uploaded_file is not None:
                try:
                    pil_img = Image.open(uploaded_file).convert("RGB")
                except (UnidentifiedImageError, OSError, ValueError):
                    st.error("Unable to read this file as a valid image. Please upload a JPG, PNG, or WebP photograph.")
                else:
                    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    if detector.is_ready:
                        dets = detector.detect(img_bgr, conf_threshold=conf_threshold)
                        annotated = detector.draw_detections(img_bgr, dets, model_mode=detector.model_mode)
                        st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
                        if dets:
                            st.caption(f"Detected {len(dets)} item(s) using {detector.model_mode} weights.")
                            if st.button("Send Photo Detections to Verification", type="primary", use_container_width=True):
                                sync_detections_from_live_stream([d.to_dict() for d in dets])
                                st.success(f"Loaded {len(dets)} detection(s) into the verification panel.")
                                st.rerun()
                        else:
                            st.info(
                                "No detections exceeded the current confidence threshold for this image. "
                                "You can lower the confidence threshold or add the foods manually on the right."
                            )
                    else:
                        st.image(pil_img, use_container_width=True)
                        st.warning("YOLO model weights are not loaded. Add the visible items manually on the right.")

    # Right Column: Food Verification & Portion Confirmation
    with verify_col:
        st.subheader("Verification & Portion Confirmation")
        st.markdown(
            "<div class='nutri-card-tinted' style='padding:0.85rem 1rem;font-size:0.86rem;'>"
            "<strong>Portion Transparency:</strong> An ordinary 2D RGB camera cannot reliably measure exact food mass, "
            "bowl depth, or cooking oil absorption. Confirm your actual quantities below (pieces, katoris, cups, or grams) "
            "before calculating nutrition.</div>",
            unsafe_allow_html=True,
        )

        detections_list: list[dict[str, Any]] = st.session_state["confirmed_detections"]
        select_options = ["-- Select food item --"] + CANONICAL_FOOD_CLASSES

        if not detections_list:
            st.markdown(
                "<div class='nutri-card'>"
                "<strong>Your Plate Is Empty</strong><br/>"
                "<span class='nutri-meta-row'>"
                "Scan with your camera, upload a meal photo, or add foods manually below to begin analysis."
                "</span></div>",
                unsafe_allow_html=True,
            )
        else:
            indices_to_remove: list[int] = []
            for idx, item in enumerate(detections_list):
                uid = item["uid"]
                is_uncertain = bool(item.get("is_uncertain", False))
                conf_val = item.get("confidence")
                conf_str = f"{conf_val * 100:.0f}% confidence" if conf_val is not None else "Manual entry"
                status_cls = "nutri-status-warn" if is_uncertain else "nutri-status-ok"
                status_text = "Needs verification" if is_uncertain else item.get("verification_status", "Verified")

                with st.container(border=True):
                    st.markdown(
                        f"<div class='nutri-meta-row'><strong>Item {idx + 1}</strong> &middot; "
                        f"<span class='{status_cls}'>{status_text}</span> &middot; {conf_str} &middot; "
                        f"{item['portion_source']}</div>",
                        unsafe_allow_html=True,
                    )
                    if item.get("original_ai_label") and item["original_ai_label"] != item["food_name"]:
                        st.caption(f"Raw model label: {item['original_ai_label']}")
                    if item.get("bbox") and any(item["bbox"]):
                        st.caption(f"Bounding box [x1, y1, x2, y2]: {item['bbox']}")

                    current_idx = (
                        select_options.index(item["food_name"])
                        if item["food_name"] in select_options
                        else 0
                    )
                    selected_food = st.selectbox(
                        "Food Label",
                        options=select_options,
                        index=current_idx,
                        key=f"food_select_{uid}",
                    )
                    if selected_food != "-- Select food item --" and selected_food != item["food_name"]:
                        item["food_name"] = selected_food
                        item["is_uncertain"] = False
                        item["confirmed"] = True
                        if item.get("confidence") is not None:
                            item["verification_status"] = (
                                "Corrected by user"
                                if selected_food != item.get("original_ai_label")
                                else "Confirmed AI prediction"
                            )
                        def_qty, def_unit = portion_mgr.get_default_portion(selected_food)
                        item["quantity"] = def_qty
                        item["unit"] = def_unit
                        item["portion_source"] = "Estimated default"

                    if item["food_name"]:
                        avail_units = portion_mgr.get_available_units(item["food_name"])
                        unit_idx = avail_units.index(item["unit"]) if item["unit"] in avail_units else 0

                        p1, p2 = st.columns(2)
                        with p1:
                            new_qty = st.number_input(
                                "Quantity",
                                min_value=0.1,
                                max_value=2000.0,
                                value=float(item["quantity"]),
                                step=0.5 if item["unit"] != "Grams (g)" else 10.0,
                                key=f"qty_{uid}",
                            )
                        with p2:
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
                        st.caption(f"Estimated weight: {est_grams:.1f} g ({conv_note})")

                    a1, a2 = st.columns(2)
                    with a1:
                        item["confirmed"] = st.checkbox(
                            "Include in meal",
                            value=bool(item.get("confirmed", False)) and bool(item["food_name"]),
                            disabled=not bool(item["food_name"]),
                            key=f"confirm_{uid}",
                        )
                    with a2:
                        if st.button("Remove", key=f"remove_{uid}", use_container_width=True):
                            indices_to_remove.append(idx)

            if indices_to_remove:
                for idx in sorted(indices_to_remove, reverse=True):
                    detections_list.pop(idx)
                st.rerun()

        with st.expander("Add Food Item Manually"):
            m_food = st.selectbox(
                "Select Food (Indian staples listed first)",
                options=CANONICAL_FOOD_CLASSES,
                key="manual_add_food",
            )
            m_units = portion_mgr.get_available_units(m_food)
            m_def_qty, m_def_unit = portion_mgr.get_default_portion(m_food)
            mc1, mc2 = st.columns(2)
            with mc1:
                m_qty = st.number_input(
                    "Quantity",
                    min_value=0.1,
                    max_value=2000.0,
                    value=float(m_def_qty),
                    key="manual_qty",
                )
            with mc2:
                m_unit = st.selectbox(
                    "Unit",
                    options=m_units,
                    index=m_units.index(m_def_unit) if m_def_unit in m_units else 0,
                    key="manual_unit",
                )
            if st.button("Add to Plate", key="manual_add_btn", use_container_width=True):
                entry = make_detection_entry(
                    food_name=m_food,
                    confidence=None,
                    bbox=None,
                    is_uncertain=False,
                    source_tag="User-confirmed",
                    verification_status="Manually added",
                )
                entry["quantity"] = m_qty
                entry["unit"] = m_unit
                entry["confirmed"] = True
                st.session_state["confirmed_detections"].append(entry)
                st.rerun()

        confirmed_only = [
            d for d in st.session_state["confirmed_detections"]
            if d.get("confirmed") and d.get("food_name")
        ]
        if confirmed_only:
            meal_title = st.text_input(
                "Meal Name",
                value="Everyday Meal",
                key="meal_label_input",
            )
            if st.button(
                f"Analyse Meal ({len(confirmed_only)} Confirmed Item(s))",
                type="primary",
                use_container_width=True,
            ):
                analysis = analyzer.analyze_meal(confirmed_only)
                st.session_state["latest_analysis"] = analysis
                history_mgr = get_history_manager()
                history_mgr.save_meal(analysis, meal_label=meal_title)
                st.session_state["nav_page"] = "Nutrition Dashboard"
                st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Nutrition Dashboard & Meal Intelligence
# ---------------------------------------------------------------------------
def render_dashboard_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <div class="nutri-hero-kicker">Nutrition Analysis &middot; Meal Intelligence</div>
            <h1>Nutritional Breakdown &amp; Plate Insights</h1>
            <p>
                Verified macronutrient contributions calculated strictly from your confirmed portions
                and ICMR-NIN / USDA reference tables.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analysis = st.session_state.get("latest_analysis")
    if not analysis or not analysis.get("items"):
        st.info("No meal analysed yet. Start in the Live Food Scanner to scan or verify your plate.")
        if st.button("Open Live Scanner", type="primary"):
            st.session_state["nav_page"] = "Home / Live Scanner"
            st.rerun()
        return

    if analysis.get("missing_foods"):
        st.warning(
            f"Missing reference entries (values omitted, not fabricated): "
            f"{', '.join(analysis['missing_foods'])}"
        )

    totals = analysis["totals"]
    macro_pct = analysis["macro_energy_pct"]
    items = analysis["items"]

    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "Estimated Calories", f"{totals['total_calories']:.0f} kcal", f"{totals['total_grams']:.0f} g total weight"),
        (k2, "Protein", f"{totals['total_protein_g']:.1f} g", f"{macro_pct['protein_pct']:.0f}% of macro energy"),
        (k3, "Carbohydrates", f"{totals['total_carbs_g']:.1f} g", f"{macro_pct['carbs_pct']:.0f}% of macro energy"),
        (k4, "Fat", f"{totals['total_fat_g']:.1f} g", f"{macro_pct['fat_pct']:.0f}% of macro energy"),
        (k5, "Dietary Fibre", f"{totals['total_fibre_g']:.1f} g", f"{totals['matched_item_count']} matched item(s)"),
    ]
    for col, label, val, sub in kpis:
        with col:
            st.markdown(
                f"<div class='nutri-kpi'><div class='nutri-kpi-label'>{label}</div>"
                f"<div class='nutri-kpi-value'>{val}</div>"
                f"<div class='nutri-kpi-sub'>{sub}</div></div>",
                unsafe_allow_html=True,
            )

    # Signature Feature: Meal Intelligence
    render_meal_intelligence_card(analysis)

    # Visualisations
    st.subheader("Nutritional Visualisations")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(create_macro_donut_chart(analysis), use_container_width=True)
    with c2:
        st.plotly_chart(create_food_contribution_chart(analysis), use_container_width=True)

    st.plotly_chart(create_macro_grams_bar_chart(analysis), use_container_width=True)

    # Individual Item Table
    st.subheader("Individual Food Contributions")
    for item in items:
        with st.container(border=True):
            left, right = st.columns([2, 1])
            with left:
                st.markdown(
                    f"**{item['food_name']}** · {item['category']} · {item.get('food_group', 'Other')} — "
                    f"`{item['quantity']} {item['unit']}` ({item['grams']:.1f} g)"
                )
                st.caption(f"Portion: {item['portion_source']} · Ref: {item['source']} · {item['notes']}")
            with right:
                if item.get("in_database", True):
                    st.markdown(
                        f"**{item['calories']:.0f} kcal** · "
                        f"P {item['protein_g']:.1f}g · C {item['carbs_g']:.1f}g · "
                        f"F {item['fat_g']:.1f}g · Fib {item['fibre_g']:.1f}g"
                    )
                else:
                    st.markdown("**Not in database** (values omitted)")

    # AI Transparency Section
    st.divider()
    render_ai_detection_insights(items)

    st.divider()
    export_df = pd.DataFrame(items)
    st.download_button(
        label="Export Meal Analysis (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="nutriscan_meal_analysis.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Page 3: Meal History & Meal Pattern Insights
# ---------------------------------------------------------------------------
def render_history_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <div class="nutri-hero-kicker">History &middot; Longitudinal Awareness</div>
            <h1>Meal History &amp; Pattern Insights</h1>
            <p>
                Inspect previously analysed meals, export your records, and explore nutritional patterns
                once sufficient meal history has been recorded.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history_mgr = get_history_manager()
    df = history_mgr.load_history()

    if df.empty:
        st.info("No meals recorded yet. Analyse a meal in the Live Food Scanner to begin building your history.")
        return

    avg_cal = float(pd.to_numeric(df["total_calories"], errors="coerce").fillna(0).mean())
    avg_prot = float(pd.to_numeric(df["total_protein_g"], errors="coerce").fillna(0).mean())
    avg_fib = float(pd.to_numeric(df["total_fibre_g"], errors="coerce").fillna(0).mean())

    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        (m1, "Recorded Meals", f"{len(df)}"),
        (m2, "Avg Calories / Meal", f"{avg_cal:.0f} kcal"),
        (m3, "Avg Protein / Meal", f"{avg_prot:.1f} g"),
        (m4, "Avg Fibre / Meal", f"{avg_fib:.1f} g"),
    ]
    for col, label, val in metrics:
        with col:
            st.markdown(
                f"<div class='nutri-kpi'><div class='nutri-kpi-label'>{label}</div>"
                f"<div class='nutri-kpi-value'>{val}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)
    display_cols = [c for c in df.columns if c != "items_json"]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    # Inspect a specific recorded meal
    st.subheader("Inspect a Recorded Meal")
    meal_labels = [
        f"{row['timestamp']} — {row['meal_label']} ({float(row['total_calories']):.0f} kcal)"
        for _, row in df.iterrows()
    ]
    selected_idx = st.selectbox(
        "Choose a meal to inspect",
        options=list(range(len(df))),
        format_func=lambda i: meal_labels[i],
    )
    selected_row = df.iloc[selected_idx]
    parsed_items = history_mgr.parse_meal_items(selected_row)
    with st.container(border=True):
        st.markdown(
            f"**{selected_row['meal_label']}** · {selected_row['timestamp']} · "
            f"{float(selected_row['total_calories']):.0f} kcal · "
            f"P {float(selected_row['total_protein_g']):.1f}g · "
            f"C {float(selected_row['total_carbs_g']):.1f}g · "
            f"F {float(selected_row['total_fat_g']):.1f}g · "
            f"Fibre {float(selected_row['total_fibre_g']):.1f}g"
        )
        st.caption(f"Recorded foods: {selected_row['foods_summary']}")
        if parsed_items:
            st.dataframe(
                pd.DataFrame(parsed_items)[
                    ["food_name", "quantity", "unit", "grams", "calories", "protein_g", "carbs_g", "fat_g", "fibre_g"]
                ],
                use_container_width=True,
                hide_index=True,
            )

    # Meal Pattern Insights (Strictly gated on real history)
    st.divider()
    st.subheader("Meal Pattern Insights")
    patterns = history_mgr.compute_meal_pattern_insights()
    if not patterns["sufficient_data"]:
        st.markdown(
            f"<div class='nutri-card-tinted'><strong>Building Your Baseline:</strong> {patterns['message']} "
            "NutriScan AI never fabricates historical records or extrapolates from insufficient logs.</div>",
            unsafe_allow_html=True,
        )
    else:
        shifts = patterns["recent_shifts"]
        st.markdown(
            f"<div class='nutri-card-mint'>Analysed <strong>{patterns['meal_count']}</strong> recorded meals. "
            f"Compared with your earlier entries, recent meals average "
            f"<strong>{shifts['protein_delta_g']:+.1f} g</strong> protein and "
            f"<strong>{shifts['fibre_delta_g']:+.1f} g</strong> fibre per meal.</div>",
            unsafe_allow_html=True,
        )
        pc1, pc2 = st.columns(2)
        with pc1:
            st.plotly_chart(create_history_trend_chart(patterns["timeline_df"]), use_container_width=True)
        with pc2:
            if patterns["top_foods"]:
                st.plotly_chart(create_top_foods_chart(patterns["top_foods"]), use_container_width=True)

    st.divider()
    h1, h2 = st.columns(2)
    with h1:
        st.download_button(
            "Download Full Meal History (CSV)",
            data=history_mgr.export_csv_bytes(),
            file_name="nutriscan_meal_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with h2:
        if st.button("Clear Meal History", use_container_width=True):
            history_mgr.clear_history()
            st.success("Meal history cleared.")
            st.rerun()


# ---------------------------------------------------------------------------
# Page 4: Food & Portion Reference Database
# ---------------------------------------------------------------------------
def render_database_page() -> None:
    st.markdown(
        """
        <div class="nutri-hero">
            <div class="nutri-hero-kicker">Reference Data &middot; ICMR-NIN &amp; USDA</div>
            <h1>Indian &amp; International Nutrition Database</h1>
            <p>
                Transparent per-100g nutritional composition paired with everyday Indian and international
                portion weights (katori, roti/piece, cup, serving, grams).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analyzer = get_nutrition_analyzer()
    portion_mgr = get_portion_manager()

    f1, f2 = st.columns([2, 1])
    with f1:
        search_q = st.text_input("Search food name", placeholder="e.g., Roti, Dal, Paneer, Idli, Poha...")
    with f2:
        category_filter = st.selectbox("Cuisine Filter", ["All", "Indian", "International"])

    df = analyzer.df.copy()
    if category_filter != "All":
        df = df[df["category"] == category_filter]
    if search_q.strip():
        df = df[df["food_name"].str.contains(search_q.strip(), case=False, na=False)]

    st.subheader(f"Nutritional Reference ({len(df)} foods)")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Portion Weight Reference (grams)")
    st.dataframe(portion_mgr.df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Page 5: About & AI Transparency
# ---------------------------------------------------------------------------
def render_about_page(detector: FoodDetector) -> None:
    status = detector.get_status_summary()
    st.markdown(
        f"""
        <div class="nutri-hero">
            <div class="nutri-hero-kicker">{APP_NAME} v{APP_VERSION}</div>
            <h1>Architecture, AI Boundaries &amp; Cloud Deployment</h1>
            <p>
                Built for clarity and honesty — combining Ultralytics YOLO computer vision with
                human-verified portions and grounded nutritional reference data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        ### Detection Model Transparency
        - **Current Mode:** `{status['mode']}`
        - **Directly Supported Classes by Loaded Weights:** {', '.join(status['supported_classes']) or 'None (weights not loaded)'}
        - **Custom 40-Class Indian + International Model:** Fine-tune using `training/prepare_dataset.py`,
          `training/dataset.yaml`, and `training/train.py`, then deploy `models/nutriscan_food_yolo.pt`.

        ### Why User Portion Confirmation Matters
        A standard 2D RGB camera cannot reliably determine dish depth, density, gravy thickness, or added cooking oil.
        NutriScan AI uses familiar units (katori, roti/piece, cup, ml, grams) confirmed by you before calculating nutrition.

        ### Mobile Camera Access & Streamlit Community Cloud
        Mobile browsers require **HTTPS** for live camera access (`getUserMedia`).
        Deploying directly to **Streamlit Community Cloud** provides HTTPS automatically and works seamlessly
        with the included `requirements.txt`, `packages.txt`, and `.streamlit/config.toml`.
        """
    )


# ---------------------------------------------------------------------------
# Application Shell
# ---------------------------------------------------------------------------
def main() -> None:
    init_session_state()
    apply_styling()

    detector = get_detector()

    with st.sidebar:
        st.markdown(
            f"<h2 class='nutri-editorial' style='margin-bottom:0.1rem;'>{APP_NAME}</h2>"
            f"<div class='nutri-meta-row' style='margin-bottom:1.1rem;'>{APP_TAGLINE}</div>",
            unsafe_allow_html=True,
        )

        pages = [
            "Home / Live Scanner",
            "Nutrition Dashboard",
            "Meal History",
            "Food Database",
            "About & AI Transparency",
        ]
        current_idx = (
            pages.index(st.session_state["nav_page"])
            if st.session_state["nav_page"] in pages
            else 0
        )
        selected_page = st.radio("Navigate", pages, index=current_idx, label_visibility="collapsed")
        st.session_state["nav_page"] = selected_page

        st.divider()
        status = detector.get_status_summary()
        engine_label = (
            "Custom 40-Class YOLO"
            if status["mode"] == "custom"
            else "Base Pretrained YOLO"
            if status["ready"]
            else "Weights Not Loaded"
        )
        st.caption(f"Detection Engine: {engine_label}")
        st.caption(f"Version {APP_VERSION}")

    if selected_page == "Home / Live Scanner":
        render_live_scanner_page(detector)
    elif selected_page == "Nutrition Dashboard":
        render_dashboard_page()
    elif selected_page == "Meal History":
        render_history_page()
    elif selected_page == "Food Database":
        render_database_page()
    elif selected_page == "About & AI Transparency":
        render_about_page(detector)


if __name__ == "__main__":
    main()
