import type * as cocoSsdTypes from '@tensorflow-models/coco-ssd';

export interface LocalFoodDetection {
  matchedCanonicalFood: string;
  rawLabel: string;
  confidence: number; // Real model score 0..1 from COCO-SSD
  needsVerification: boolean;
  box2d: [number, number, number, number]; // [ymin, xmin, ymax, xmax] scaled 0..1000
  visualNote: string;
}

// Exact honest mapping matching config.py from NutriScan AI
const COCO_DIRECT_FOOD_MAP: Record<string, string> = {
  apple: 'Apple',
  banana: 'Banana',
  orange: 'Orange',
  pizza: 'Pizza',
  sandwich: 'Sandwich',
  cake: 'Cake',
};

const COCO_UNCERTAIN_HINTS = new Set<string>([
  'bowl',
  'cup',
  'broccoli',
  'carrot',
  'hot dog',
  'donut',
]);

let cachedModelPromise: Promise<cocoSsdTypes.ObjectDetection> | null = null;

export async function loadLocalDetector(): Promise<cocoSsdTypes.ObjectDetection> {
  if (!cachedModelPromise) {
    cachedModelPromise = (async () => {
      const tf = await import('@tensorflow/tfjs');
      await tf.ready();
      const cocoSsd = await import('@tensorflow-models/coco-ssd');
      return cocoSsd.load({ base: 'lite_mobilenet_v2' });
    })().catch((err) => {
      cachedModelPromise = null;
      throw err;
    });
  }
  return cachedModelPromise;
}

export async function detectFoodInBrowser(
  imageElement: HTMLImageElement,
  confThreshold: number = 0.35
): Promise<LocalFoodDetection[]> {
  const model = await loadLocalDetector();
  const predictions = await model.detect(imageElement, 20, confThreshold);

  const imgWidth = Math.max(imageElement.naturalWidth || imageElement.width, 1);
  const imgHeight = Math.max(imageElement.naturalHeight || imageElement.height, 1);

  const detections: LocalFoodDetection[] = [];

  for (const pred of predictions) {
    const raw = pred.class.trim().toLowerCase();
    const isDirect = raw in COCO_DIRECT_FOOD_MAP;
    const isHint = COCO_UNCERTAIN_HINTS.has(raw);

    if (!isDirect && !isHint) {
      continue;
    }

    const [x, y, w, h] = pred.bbox;
    const xmin = Math.max(0, Math.min(1000, Math.round((x / imgWidth) * 1000)));
    const ymin = Math.max(0, Math.min(1000, Math.round((y / imgHeight) * 1000)));
    const xmax = Math.max(xmin + 1, Math.min(1000, Math.round(((x + w) / imgWidth) * 1000)));
    const ymax = Math.max(ymin + 1, Math.min(1000, Math.round(((y + h) / imgHeight) * 1000)));

    const confidence = Math.round(pred.score * 1000) / 1000;
    const matchedCanonicalFood = isDirect ? COCO_DIRECT_FOOD_MAP[raw] : '';
    const needsVerification = !isDirect || confidence < 0.45;

    detections.push({
      matchedCanonicalFood,
      rawLabel: isDirect ? COCO_DIRECT_FOOD_MAP[raw] : `Uncertain Food Item (${pred.class})`,
      confidence,
      needsVerification,
      box2d: [ymin, xmin, ymax, xmax],
      visualNote: isDirect
        ? `Detected directly on-device (${Math.round(confidence * 100)}% COCO-SSD score)`
        : `Detected "${pred.class}" container/hint (${Math.round(confidence * 100)}%) — select the exact dish`,
    });
  }

  return detections;
}
