import appPy from '../../nutriscan_streamlit/app.py?raw';
import configPy from '../../nutriscan_streamlit/config.py?raw';
import stylesCss from '../../nutriscan_streamlit/assets/styles.css?raw';
import mealIntelligencePy from '../../nutriscan_streamlit/modules/meal_intelligence.py?raw';
import nutritionPy from '../../nutriscan_streamlit/modules/nutrition.py?raw';
import portionPy from '../../nutriscan_streamlit/modules/portion.py?raw';
import historyPy from '../../nutriscan_streamlit/modules/history.py?raw';
import visualizationPy from '../../nutriscan_streamlit/modules/visualization.py?raw';
import detectorPy from '../../nutriscan_streamlit/modules/detector.py?raw';
import recommendationsPy from '../../nutriscan_streamlit/modules/recommendations.py?raw';
import packagesTxt from '../../nutriscan_streamlit/packages.txt?raw';
import requirementsTxt from '../../nutriscan_streamlit/requirements.txt?raw';
import streamlitConfigToml from '../../nutriscan_streamlit/.streamlit/config.toml?raw';
import datasetYaml from '../../nutriscan_streamlit/training/dataset.yaml?raw';
import testNutritionPy from '../../nutriscan_streamlit/tests/test_nutrition.py?raw';

export interface UpgradedRepoFile {
  path: string;
  status: 'Modified' | 'Added' | 'Bug Fixed';
  summary: string;
  content: string;
}

export const UPGRADED_STREAMLIT_FILES: UpgradedRepoFile[] = [
  {
    path: 'app.py',
    status: 'Modified',
    summary:
      'Redesigned soft-green editorial UI, full Scanner → Verification → Portion → Nutrition → Meal Intelligence → AI Detection Insights → History flow, safe image upload handling, and uncertain-detection pre-confirmation bug fix.',
    content: appPy,
  },
  {
    path: 'config.py',
    status: 'Modified',
    summary:
      'Preserved all original constants and paths while adding FOOD_GROUP_CATALOG, FOOD_GROUP_MAP, BRAND_PALETTE, and the "Scan. Understand. Nourish." product identity.',
    content: configPy,
  },
  {
    path: 'assets/styles.css',
    status: 'Modified',
    summary:
      'Replaced bright gradients with the soft botanical palette (#F3F7F0, #E8F0E5, #FFFFFF, #527B60, #294C38), DM Sans / Manrope / Playfair Display typography, and mobile-first responsive rules.',
    content: stylesCss,
  },
  {
    path: 'modules/meal_intelligence.py',
    status: 'Added',
    summary:
      'Signature NutriScan Meal Intelligence engine computing Meal Composition, Nutritional Balance, Food-Group Variety (represented & unrepresented), and non-medical Contextual Suggestions.',
    content: mealIntelligencePy,
  },
  {
    path: 'modules/nutrition.py',
    status: 'Modified',
    summary:
      'Preserved exact CSV calculations while adding graceful CSV error handling, food-group tagging, and transparent omission (never fabrication) when a food is missing from food_nutrition.csv.',
    content: nutritionPy,
  },
  {
    path: 'modules/portion.py',
    status: 'Modified',
    summary:
      'Preserved PortionManager API and Indian serving units (Katoris, Pieces, Cups, ml, Grams) while preventing uncaught crashes if portion_reference.csv is missing.',
    content: portionPy,
  },
  {
    path: 'modules/history.py',
    status: 'Modified',
    summary:
      'Preserved HISTORY_COLUMNS and CSV export while adding structured items_json inspection and real Meal Pattern Insights gated on >= 3 logged meals.',
    content: historyPy,
  },
  {
    path: 'modules/visualization.py',
    status: 'Modified',
    summary:
      'Updated Plotly charts to the soft-green botanical palette and added historical nutrient trend and frequently analysed foods charts.',
    content: visualizationPy,
  },
  {
    path: 'modules/detector.py',
    status: 'Modified',
    summary:
      'Preserved Ultralytics YOLO loading and honest COCO mapping, updated OpenCV bounding-box colours to botanical green/ochre, and added get_supported_classes() for weight transparency.',
    content: detectorPy,
  },
  {
    path: 'modules/recommendations.py',
    status: 'Modified',
    summary:
      'Preserved generate_meal_insights() API with refined educational, non-restrictive, non-medical language integrated with Meal Intelligence.',
    content: recommendationsPy,
  },
  {
    path: 'training/dataset.yaml',
    status: 'Bug Fixed',
    summary:
      'Removed the stray ```yaml markdown fence on line 1 that broke PyYAML and Ultralytics YOLO training.',
    content: datasetYaml,
  },
  {
    path: 'requirements.txt',
    status: 'Bug Fixed',
    summary:
      'Added CPU-only PyTorch wheel index (--extra-index-url https://download.pytorch.org/whl/cpu) and relaxed restrictive upper version pins so Streamlit Community Cloud installs opencv-python-headless without timing out or aborting.',
    content: requirementsTxt,
  },
  {
    path: 'packages.txt',
    status: 'Added',
    summary:
      'Added Linux system libraries (libgl1, libglib2.0-0, libsm6, libxext6, libxrender1, libav/opus/vpx) required for OpenCV and streamlit-webrtc on Streamlit Community Cloud.',
    content: packagesTxt,
  },
  {
    path: '.streamlit/config.toml',
    status: 'Added',
    summary:
      'Configured native Streamlit soft-green theme tokens (#F3F7F0 canvas, #E8F0E5 sidebar, #527B60 primary) for seamless Streamlit Community Cloud rendering.',
    content: streamlitConfigToml,
  },
  {
    path: 'tests/test_nutrition.py',
    status: 'Modified',
    summary:
      'Preserved existing tests and added tests for Meal Intelligence, non-fabrication of missing foods, and Meal Pattern Insights gating.',
    content: testNutritionPy,
  },
];
