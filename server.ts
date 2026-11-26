import 'dotenv/config';
import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { GoogleGenAI, ThinkingLevel, Type } from '@google/genai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT || 3000);
const IS_PROD = process.env.NODE_ENV === 'production';

const CANONICAL_FOODS = [
  'Roti / Chapati',
  'Rice',
  'Dal',
  'Paneer',
  'Sabzi',
  'Idli',
  'Dosa',
  'Poha',
  'Chole',
  'Samosa',
  'Biryani',
  'Paratha',
  'Puri',
  'Rajma',
  'Khichdi',
  'Upma',
  'Dhokla',
  'Uttapam',
  'Pakora',
  'Aloo Gobi',
  'Apple',
  'Banana',
  'Orange',
  'Egg',
  'Grilled chicken',
  'Fish',
  'Burger',
  'Pizza',
  'French fries',
  'Sandwich',
  'Salad',
  'Oatmeal',
  'Yogurt',
  'Pasta',
  'Pancakes',
  'Bread',
  'Rice bowl',
  'Soup',
  'Cake',
  'Cookies',
];

const ALLOWED_MIME_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function getGenAIClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY is not configured on the server.');
  }
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });
}

async function startServer() {
  const app = express();

  app.use(express.json({ limit: '12mb' }));

  app.get('/api/health', (_req, res) => {
    res.json({ ok: true });
  });

  app.post('/api/detect-food', async (req, res) => {
    try {
      const { imageBase64, mimeType } = req.body ?? {};

      if (typeof imageBase64 !== 'string' || imageBase64.length < 100) {
        return res.status(400).json({ error: 'A valid meal image is required.' });
      }
      if (typeof mimeType !== 'string' || !ALLOWED_MIME_TYPES.has(mimeType)) {
        return res.status(400).json({ error: 'Unsupported image format. Please use JPG, PNG, or WebP.' });
      }

      const ai = getGenAIClient();

      const prompt = [
        'You are the computer vision food-recognition engine for NutriScan AI.',
        'Inspect the meal photograph carefully and detect every distinct visible food item.',
        'Match each detected food to the closest canonical label from this exact list whenever visually accurate:',
        CANONICAL_FOODS.join(', '),
        'Rules:',
        '- Only report foods genuinely visible in the image. Never invent hidden dishes.',
        '- If a visible dish clearly does not belong to the canonical list (or is visually ambiguous), set matchedCanonicalFood to "" (empty string), set rawLabel to the plain name of what you see, and set needsVerification to true.',
        '- Provide tight 2D bounding boxes as [ymin, xmin, ymax, xmax] normalized on a 0 to 1000 integer scale.',
        '- Estimate a rough visual count or standard serving count (e.g. 2 rotis, 1 katori dal) while remembering that exact mass requires user confirmation.',
        '- Set certainty to "high" when visually unmistakable, "medium" when likely but partially occluded or ambiguous, and "low" when uncertain.',
        '- If no food is visible in the photo, return an empty detections array and explain why in plateSummary.',
      ].join('\n');

      const response = await ai.models.generateContent({
        model: 'gemini-4-hydrogen',
        contents: {
          parts: [
            {
              inlineData: {
                mimeType,
                data: imageBase64,
              },
            },
            { text: prompt },
          ],
        },
        config: {
          thinkingConfig: { thinkingLevel: ThinkingLevel.LOW },
          responseMimeType: 'application/json',
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              suggestedMealLabel: {
                type: Type.STRING,
                description: 'Short natural title for the meal, e.g., Home Dal-Roti Thali or Fresh Fruit Bowl.',
              },
              plateSummary: {
                type: Type.STRING,
                description: 'One concise factual sentence describing what is visible in the image.',
              },
              detections: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    matchedCanonicalFood: {
                      type: Type.STRING,
                      description: 'Exact name from the canonical list, or empty string if unlisted/ambiguous.',
                    },
                    rawLabel: {
                      type: Type.STRING,
                      description: 'Plain descriptive label of what is visible.',
                    },
                    certainty: {
                      type: Type.STRING,
                      description: 'One of: high, medium, low.',
                    },
                    needsVerification: {
                      type: Type.BOOLEAN,
                      description: 'True if the dish is ambiguous, occluded, or outside the canonical list.',
                    },
                    suggestedQuantity: {
                      type: Type.NUMBER,
                      description: 'Approximate visible count (e.g., 2 for two rotis, 1 for one bowl/katori).',
                    },
                    visualNote: {
                      type: Type.STRING,
                      description: 'Brief visual cue observed (e.g., two flatbreads on plate, yellow lentil bowl).',
                    },
                    box2d: {
                      type: Type.ARRAY,
                      items: { type: Type.INTEGER },
                      description: 'Bounding box [ymin, xmin, ymax, xmax] scaled 0..1000.',
                    },
                  },
                  required: [
                    'matchedCanonicalFood',
                    'rawLabel',
                    'certainty',
                    'needsVerification',
                    'suggestedQuantity',
                    'visualNote',
                    'box2d',
                  ],
                },
              },
            },
            required: ['suggestedMealLabel', 'plateSummary', 'detections'],
          },
        },
      });

      const text = (response.text ?? '{}').trim();
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(text);
      } catch {
        return res.status(502).json({
          error: 'Could not parse detection response. Please try scanning again with clearer lighting.',
        });
      }

      const rawDetections = Array.isArray(parsed.detections) ? parsed.detections : [];
      const canonicalLower = new Map(CANONICAL_FOODS.map((f) => [f.toLowerCase(), f]));

      const normalizedDetections = rawDetections.map((det: Record<string, unknown>) => {
        const rawCanonical = String(det.matchedCanonicalFood ?? '').trim();
        const exactCanonical = canonicalLower.get(rawCanonical.toLowerCase()) ?? '';
        const rawLabel = String(det.rawLabel ?? exactCanonical ?? 'Food item').trim();
        const certaintyRaw = String(det.certainty ?? 'medium').toLowerCase();
        const certainty =
          certaintyRaw === 'high' || certaintyRaw === 'medium' || certaintyRaw === 'low'
            ? certaintyRaw
            : 'medium';
        const needsVerification = Boolean(det.needsVerification) || !exactCanonical || certainty === 'low';
        const qty = Number(det.suggestedQuantity);
        const safeQty = Number.isFinite(qty) && qty > 0 && qty <= 50 ? Math.round(qty * 10) / 10 : 1;

        let box2d: [number, number, number, number] | null = null;
        if (Array.isArray(det.box2d) && det.box2d.length === 4) {
          const coords = det.box2d.map((n) => Math.max(0, Math.min(1000, Math.round(Number(n) || 0))));
          if (coords[2] > coords[0] && coords[3] > coords[1]) {
            box2d = [coords[0], coords[1], coords[2], coords[3]];
          }
        }

        return {
          matchedCanonicalFood: exactCanonical,
          rawLabel,
          certainty,
          needsVerification,
          suggestedQuantity: safeQty,
          visualNote: String(det.visualNote ?? '').trim(),
          box2d,
        };
      });

      return res.json({
        suggestedMealLabel: String(parsed.suggestedMealLabel ?? 'Scanned Meal').trim() || 'Scanned Meal',
        plateSummary: String(parsed.plateSummary ?? '').trim(),
        detections: normalizedDetections,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unexpected vision detection error.';
      const status =
        message.includes('API_KEY_INVALID') || message.includes('PERMISSION_DENIED')
          ? 403
          : message.includes('RESOURCE_EXHAUSTED') || message.includes('429')
          ? 429
          : 500;
      return res.status(status).json({ error: message });
    }
  });

  if (!IS_PROD) {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.resolve(__dirname, 'dist');
    app.use(express.static(distDir));
    app.get('/{*splat}', (_req, res) => {
      const indexFile = path.join(distDir, 'index.html');
      if (fs.existsSync(indexFile)) {
        res.sendFile(indexFile);
      } else {
        res.status(404).send('Application build not found.');
      }
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`NutriScan AI server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
