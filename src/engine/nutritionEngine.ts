import {
  CORE_VARIETY_GROUPS,
  FOOD_GROUP_CATALOG,
  FOOD_NUTRITION_DATABASE,
  FoodGroup,
  FoodNutritionRecord,
  PORTION_REFERENCE_DATABASE,
  PortionReferenceRecord,
  PortionUnit,
} from '../data/nutritionData';

export type VerificationStatus =
  | 'Confirmed AI prediction'
  | 'Confirmed by user'
  | 'Corrected by user'
  | 'Manually added'
  | 'Uncertain — requires verification';

export type DetectionCertainty = 'high' | 'medium' | 'low';

export interface PlateItemDraft {
  uid: string;
  foodName: string;
  originalAiLabel: string | null;
  confidence: number | null;
  detectionCertainty?: DetectionCertainty | null;
  visualNote?: string;
  box2d?: [number, number, number, number] | null; // [ymin, xmin, ymax, xmax] 0..1000
  isUncertain: boolean;
  quantity: number;
  unit: PortionUnit;
  portionSource: 'User-confirmed' | 'Estimated default';
  verificationStatus: VerificationStatus;
  confirmed: boolean;
  markerCoords?: { xPct: number; yPct: number } | null;
}

export interface AnalyzedFoodItem {
  foodName: string;
  category: string;
  foodGroup: FoodGroup | 'Unclassified';
  inDatabase: boolean;
  quantity: number;
  unit: PortionUnit;
  grams: number;
  portionSource: string;
  conversionNote: string;
  calories: number | null;
  proteinG: number | null;
  carbsG: number | null;
  fatG: number | null;
  fibreG: number | null;
  source: string;
  notes: string;
  confidence: number | null;
  detectionCertainty?: DetectionCertainty | null;
  visualNote?: string;
  verificationStatus: VerificationStatus;
  originalAiLabel: string | null;
}

export interface MealAnalysisResult {
  mealId: string;
  timestamp: string;
  mealLabel: string;
  items: AnalyzedFoodItem[];
  totals: {
    totalGrams: number;
    totalCalories: number;
    totalProteinG: number;
    totalCarbsG: number;
    totalFatG: number;
    totalFibreG: number;
    itemCount: number;
    matchedItemCount: number;
  };
  macroEnergyPct: {
    proteinPct: number;
    carbsPct: number;
    fatPct: number;
  };
  missingFoods: string[];
}

export interface MealIntelligenceReport {
  composition: {
    foodName: string;
    foodGroup: string;
    portionLabel: string;
    grams: number;
    calories: number;
    calorieSharePct: number;
    proteinG: number;
    carbsG: number;
    fatG: number;
    fibreG: number;
  }[];
  nutritionalBalance: {
    summary: string;
    calories: number;
    proteinG: number;
    carbsG: number;
    fatG: number;
    fibreG: number;
    proteinPct: number;
    carbsPct: number;
    fatPct: number;
  };
  foodGroupVariety: {
    represented: { group: FoodGroup; items: string[] }[];
    unrepresented: FoodGroup[];
    representedCount: number;
  };
  contextualSuggestions: string[];
  missingFoods: string[];
}

export interface MealPatternInsights {
  sufficientData: boolean;
  mealCount: number;
  requiredMeals: number;
  message?: string;
  averages?: {
    calories: number;
    proteinG: number;
    carbsG: number;
    fatG: number;
    fibreG: number;
  };
  recentShifts?: {
    proteinDeltaG: number;
    fibreDeltaG: number;
  };
  topFoods: { foodName: string; count: number }[];
  timeline: {
    label: string;
    calories: number;
    proteinG: number;
    carbsG: number;
    fatG: number;
    fibreG: number;
  }[];
}

const nutritionByLower = new Map<string, FoodNutritionRecord>(
  FOOD_NUTRITION_DATABASE.map((r) => [r.foodName.toLowerCase(), r])
);

const portionByLower = new Map<string, PortionReferenceRecord>(
  PORTION_REFERENCE_DATABASE.map((r) => [r.foodName.toLowerCase(), r])
);

const round1 = (n: number): number => Math.round(n * 10) / 10;

export function getFoodRecord(foodName: string): FoodNutritionRecord | null {
  return nutritionByLower.get(foodName.trim().toLowerCase()) ?? null;
}

export function getPortionReference(foodName: string): PortionReferenceRecord | null {
  return portionByLower.get(foodName.trim().toLowerCase()) ?? null;
}

export function getDefaultPortion(foodName: string): { quantity: number; unit: PortionUnit } {
  const ref = getPortionReference(foodName);
  if (!ref) {
    return { quantity: 100, unit: 'Grams (g)' };
  }
  return { quantity: ref.defaultQuantity, unit: ref.defaultUnit };
}

export function getAvailableUnits(foodName: string): PortionUnit[] {
  const ref = getPortionReference(foodName);
  const units: PortionUnit[] = ['Grams (g)'];
  if (!ref) {
    return ['Grams (g)', 'Servings', 'Cups', 'Katoris', 'Pieces', 'Millilitres (ml)'];
  }
  if (ref.gramsPerPiece > 0) units.push('Pieces');
  if (ref.gramsPerCup > 0) units.push('Cups');
  if (ref.gramsPerKatori > 0) units.push('Katoris');
  if (ref.gramsPerMl > 0) units.push('Millilitres (ml)');
  if (ref.gramsPerServing > 0) units.push('Servings');
  return units;
}

export function convertToGrams(
  foodName: string,
  quantity: number,
  unit: PortionUnit
): { grams: number; conversionNote: string } {
  const qty = Math.max(Number(quantity) || 0, 0);
  if (unit === 'Grams (g)') {
    return { grams: round1(qty), conversionNote: 'Direct gram entry' };
  }

  const ref = getPortionReference(foodName);
  if (!ref) {
    return { grams: round1(qty * 100), conversionNote: 'Fallback 100g/unit reference' };
  }

  const map: Record<Exclude<PortionUnit, 'Grams (g)'>, number> = {
    Pieces: ref.gramsPerPiece,
    Cups: ref.gramsPerCup,
    Katoris: ref.gramsPerKatori,
    'Millilitres (ml)': ref.gramsPerMl,
    Servings: ref.gramsPerServing,
  };

  let factor = map[unit] ?? 0;
  if (factor <= 0) {
    factor = ref.gramsPerServing > 0 ? ref.gramsPerServing : 150;
    return {
      grams: round1(qty * factor),
      conversionNote: `Unit '${unit}' approximated via standard serving (${factor}g)`,
    };
  }

  const singular = unit.split('(')[0].trim().replace(/s$/, '') || unit;
  return {
    grams: round1(qty * factor),
    conversionNote: `1 ${singular} ≈ ${factor}g`,
  };
}

export function analyzeMeal(drafts: PlateItemDraft[], mealLabel: string): MealAnalysisResult {
  const missingFoods: string[] = [];
  const analyzedItems: AnalyzedFoodItem[] = drafts.map((draft) => {
    const record = getFoodRecord(draft.foodName);
    const { grams, conversionNote } = convertToGrams(draft.foodName, draft.quantity, draft.unit);
    const scale = grams / 100;

    if (!record) {
      missingFoods.push(draft.foodName);
      return {
        foodName: draft.foodName,
        category: 'Unlisted',
        foodGroup: 'Unclassified',
        inDatabase: false,
        quantity: round1(draft.quantity),
        unit: draft.unit,
        grams,
        portionSource: draft.portionSource,
        conversionNote,
        calories: null,
        proteinG: null,
        carbsG: null,
        fatG: null,
        fibreG: null,
        source: 'Not found in database',
        notes: 'This food is not in food_nutrition.csv; no nutritional values were fabricated.',
        confidence: draft.confidence,
        detectionCertainty: draft.detectionCertainty ?? null,
        visualNote: draft.visualNote,
        verificationStatus: draft.verificationStatus,
        originalAiLabel: draft.originalAiLabel,
      };
    }

    return {
      foodName: record.foodName,
      category: record.category,
      foodGroup: record.foodGroup,
      inDatabase: true,
      quantity: round1(draft.quantity),
      unit: draft.unit,
      grams,
      portionSource: draft.portionSource,
      conversionNote,
      calories: round1(record.caloriesPer100g * scale),
      proteinG: round1(record.proteinPer100g * scale),
      carbsG: round1(record.carbsPer100g * scale),
      fatG: round1(record.fatPer100g * scale),
      fibreG: round1(record.fibrePer100g * scale),
      source: record.source,
      notes: record.notes,
      confidence: draft.confidence,
      detectionCertainty: draft.detectionCertainty ?? null,
      visualNote: draft.visualNote,
      verificationStatus: draft.verificationStatus,
      originalAiLabel: draft.originalAiLabel,
    };
  });

  const matched = analyzedItems.filter((i) => i.inDatabase);
  const totals = {
    totalGrams: round1(analyzedItems.reduce((s, i) => s + i.grams, 0)),
    totalCalories: round1(matched.reduce((s, i) => s + (i.calories ?? 0), 0)),
    totalProteinG: round1(matched.reduce((s, i) => s + (i.proteinG ?? 0), 0)),
    totalCarbsG: round1(matched.reduce((s, i) => s + (i.carbsG ?? 0), 0)),
    totalFatG: round1(matched.reduce((s, i) => s + (i.fatG ?? 0), 0)),
    totalFibreG: round1(matched.reduce((s, i) => s + (i.fibreG ?? 0), 0)),
    itemCount: analyzedItems.length,
    matchedItemCount: matched.length,
  };

  const pKcal = totals.totalProteinG * 4;
  const cKcal = totals.totalCarbsG * 4;
  const fKcal = totals.totalFatG * 9;
  const macroKcal = pKcal + cKcal + fKcal;

  const macroEnergyPct =
    macroKcal > 0
      ? {
          proteinPct: round1((pKcal / macroKcal) * 100),
          carbsPct: round1((cKcal / macroKcal) * 100),
          fatPct: round1((fKcal / macroKcal) * 100),
        }
      : { proteinPct: 0, carbsPct: 0, fatPct: 0 };

  const now = new Date();
  const timestamp = now.toISOString().replace('T', ' ').slice(0, 19);

  return {
    mealId: `meal_${now.getTime()}`,
    timestamp,
    mealLabel: mealLabel.trim() || 'Everyday Meal',
    items: analyzedItems,
    totals,
    macroEnergyPct,
    missingFoods,
  };
}

export function computeMealIntelligence(analysis: MealAnalysisResult): MealIntelligenceReport {
  const matched = analysis.items.filter((i) => i.inDatabase);
  const totalCal = analysis.totals.totalCalories;

  const composition = matched.map((item) => {
    const calories = item.calories ?? 0;
    const calorieSharePct = totalCal > 0 ? round1((calories / totalCal) * 100) : 0;
    return {
      foodName: item.foodName,
      foodGroup: item.foodGroup,
      portionLabel: `${item.quantity} ${item.unit}`,
      grams: item.grams,
      calories,
      calorieSharePct,
      proteinG: item.proteinG ?? 0,
      carbsG: item.carbsG ?? 0,
      fatG: item.fatG ?? 0,
      fibreG: item.fibreG ?? 0,
    };
  });

  const { totalProteinG, totalCarbsG, totalFatG, totalFibreG } = analysis.totals;
  const { proteinPct, carbsPct, fatPct } = analysis.macroEnergyPct;

  let summary =
    'Confirm at least one database-matched food item to view meal nutritional balance.';
  if (totalCal > 0) {
    const dominant = [
      { name: 'carbohydrates', val: carbsPct },
      { name: 'protein', val: proteinPct },
      { name: 'fat', val: fatPct },
    ].sort((a, b) => b.val - a.val)[0].name;

    summary = `Across ${matched.length} analysed item${matched.length === 1 ? '' : 's'}, this meal provides an estimated ${Math.round(totalCal)} kcal with ${dominant} supplying the largest share of energy (Carbs ${Math.round(carbsPct)}% · Protein ${Math.round(proteinPct)}% · Fat ${Math.round(fatPct)}%) and ${totalFibreG.toFixed(1)} g of dietary fibre.`;
  }

  const groupMap = new Map<FoodGroup, string[]>();
  for (const item of matched) {
    if (item.foodGroup !== 'Unclassified') {
      const list = groupMap.get(item.foodGroup) ?? [];
      list.push(item.foodName);
      groupMap.set(item.foodGroup, list);
    }
  }

  const represented = FOOD_GROUP_CATALOG.filter((g) => groupMap.has(g)).map((group) => ({
    group,
    items: groupMap.get(group)!,
  }));
  const unrepresented = CORE_VARIETY_GROUPS.filter((g) => !groupMap.has(g));

  const suggestions: string[] = [];
  if (matched.length === 0) {
    suggestions.push(
      'Add and confirm items from the nutritional reference database to generate contextual meal insights.'
    );
  } else {
    const carbItems = composition
      .filter((c) => c.foodGroup === 'Grains & Staples' || c.carbsG >= 20)
      .map((c) => c.foodName);
    const legumeItems = groupMap.get('Lentils & Legumes') ?? [];
    const vegItems = groupMap.get('Vegetables & Greens') ?? [];
    const fruitItems = groupMap.get('Fruits') ?? [];
    const hasProteinSource =
      legumeItems.length > 0 ||
      (groupMap.get('Dairy & Paneer')?.length ?? 0) > 0 ||
      (groupMap.get('Eggs & Lean Proteins')?.length ?? 0) > 0;

    if (carbItems.length >= 2 && legumeItems.length > 0 && vegItems.length === 0) {
      suggestions.push(
        `Your meal contains multiple carbohydrate sources (${carbItems.slice(0, 3).join(', ')}) and includes a legume-based protein source (${legumeItems.join(', ')}). Consider exploring additional vegetable variety such as sabzi or fresh salad in your meals.`
      );
    } else if (carbItems.length >= 2 && !hasProteinSource) {
      suggestions.push(
        `This plate centres on grain and carbohydrate staples (${carbItems.slice(0, 3).join(', ')}). Exploring complementary protein sources like dal, rajma, chole, paneer, curd, or eggs can broaden macronutrient variety.`
      );
    } else if (legumeItems.length > 0 && vegItems.length > 0) {
      suggestions.push(
        `Your plate brings together legumes (${legumeItems.join(', ')}) and vegetables (${vegItems.join(', ')}), combining plant protein with dietary fibre.`
      );
    }

    if (vegItems.length === 0 && !(carbItems.length >= 2 && legumeItems.length > 0)) {
      suggestions.push(
        'No vegetable dishes are represented in this meal. Pairing staples with a katori of seasonal sabzi, aloo gobi, soup, or fresh salad expands plant variety.'
      );
    }

    if (fruitItems.length === 0 && totalFibreG < 6) {
      suggestions.push(
        `Estimated dietary fibre for this meal is ${totalFibreG.toFixed(1)} g. Whole-wheat rotis, lentils, vegetables, oats, or whole fruit naturally contribute additional fibre across the day.`
      );
    } else if (totalFibreG >= 6) {
      const fibreSources = composition
        .filter((c) => c.fibreG >= 1.5)
        .map((c) => c.foodName)
        .join(', ');
      suggestions.push(
        `This meal contributes an estimated ${totalFibreG.toFixed(1)} g of dietary fibre${fibreSources ? `, led by ${fibreSources}` : ''}.`
      );
    }

    if (proteinPct < 14 && totalProteinG < 12) {
      suggestions.push(
        `Protein supplies about ${Math.round(proteinPct)}% (${totalProteinG.toFixed(1)} g) of estimated meal energy. Pairing everyday staples with dal, paneer, yogurt, eggs, fish, or grilled chicken adds protein diversity.`
      );
    } else if (totalProteinG >= 18) {
      const topProtein = [...composition]
        .sort((a, b) => b.proteinG - a.proteinG)
        .slice(0, 2)
        .map((c) => c.foodName)
        .join(' and ');
      suggestions.push(
        `Protein represents ~${Math.round(proteinPct)}% (${totalProteinG.toFixed(1)} g) of estimated energy, primarily contributed by ${topProtein}.`
      );
    }

    if (fatPct > 36 || (groupMap.get('Fried & Indulgent Snacks')?.length ?? 0) > 0) {
      suggestions.push(
        'Preparation details such as tadka, ghee brushing, or deep-frying can noticeably shift actual fat and calorie totals compared with database averages.'
      );
    }
  }

  return {
    composition,
    nutritionalBalance: {
      summary,
      calories: totalCal,
      proteinG: totalProteinG,
      carbsG: totalCarbsG,
      fatG: totalFatG,
      fibreG: totalFibreG,
      proteinPct,
      carbsPct,
      fatPct,
    },
    foodGroupVariety: {
      represented,
      unrepresented,
      representedCount: represented.length,
    },
    contextualSuggestions: suggestions.slice(0, 4),
    missingFoods: analysis.missingFoods,
  };
}

export const MIN_MEALS_FOR_PATTERNS = 3;

export function computeMealPatternInsights(history: MealAnalysisResult[]): MealPatternInsights {
  if (history.length < MIN_MEALS_FOR_PATTERNS) {
    return {
      sufficientData: false,
      mealCount: history.length,
      requiredMeals: MIN_MEALS_FOR_PATTERNS,
      message: `Meal Pattern Insights require at least ${MIN_MEALS_FOR_PATTERNS} recorded meals. You currently have ${history.length} saved meal${history.length === 1 ? '' : 's'}.`,
      topFoods: [],
      timeline: [],
    };
  }

  const chronological = [...history].reverse();
  const countMap = new Map<string, number>();
  for (const meal of chronological) {
    for (const item of meal.items) {
      countMap.set(item.foodName, (countMap.get(item.foodName) ?? 0) + 1);
    }
  }

  const topFoods = Array.from(countMap.entries())
    .map(([foodName, count]) => ({ foodName, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  const avg = (fn: (m: MealAnalysisResult) => number) =>
    round1(chronological.reduce((s, m) => s + fn(m), 0) / chronological.length);

  const mid = Math.max(1, Math.floor(chronological.length / 2));
  const early = chronological.slice(0, mid);
  const recent = chronological.slice(mid);
  const meanOf = (arr: MealAnalysisResult[], fn: (m: MealAnalysisResult) => number) =>
    arr.reduce((s, m) => s + fn(m), 0) / arr.length;

  return {
    sufficientData: true,
    mealCount: history.length,
    requiredMeals: MIN_MEALS_FOR_PATTERNS,
    averages: {
      calories: avg((m) => m.totals.totalCalories),
      proteinG: avg((m) => m.totals.totalProteinG),
      carbsG: avg((m) => m.totals.totalCarbsG),
      fatG: avg((m) => m.totals.totalFatG),
      fibreG: avg((m) => m.totals.totalFibreG),
    },
    recentShifts: {
      proteinDeltaG: round1(
        meanOf(recent, (m) => m.totals.totalProteinG) -
          meanOf(early, (m) => m.totals.totalProteinG)
      ),
      fibreDeltaG: round1(
        meanOf(recent, (m) => m.totals.totalFibreG) -
          meanOf(early, (m) => m.totals.totalFibreG)
      ),
    },
    topFoods,
    timeline: chronological.map((m, idx) => ({
      label: `#${idx + 1} ${m.mealLabel.slice(0, 12)}`,
      calories: m.totals.totalCalories,
      proteinG: m.totals.totalProteinG,
      carbsG: m.totals.totalCarbsG,
      fatG: m.totals.totalFatG,
      fibreG: m.totals.totalFibreG,
    })),
  };
}

export function exportMealToCsv(analysis: MealAnalysisResult): string {
  const headers = [
    'food_name',
    'category',
    'food_group',
    'quantity',
    'unit',
    'grams',
    'calories',
    'protein_g',
    'carbs_g',
    'fat_g',
    'fibre_g',
    'portion_source',
    'verification_status',
    'source',
  ];
  const escape = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const rows = analysis.items.map((i) =>
    [
      i.foodName,
      i.category,
      i.foodGroup,
      i.quantity,
      i.unit,
      i.grams,
      i.calories ?? '',
      i.proteinG ?? '',
      i.carbsG ?? '',
      i.fatG ?? '',
      i.fibreG ?? '',
      i.portionSource,
      i.verificationStatus,
      i.source,
    ]
      .map(escape)
      .join(',')
  );
  return [headers.join(','), ...rows].join('\n');
}

export function exportHistoryToCsv(history: MealAnalysisResult[]): string {
  const headers = [
    'meal_id',
    'timestamp',
    'meal_label',
    'foods_summary',
    'item_count',
    'total_grams',
    'total_calories',
    'total_protein_g',
    'total_carbs_g',
    'total_fat_g',
    'total_fibre_g',
  ];
  const escape = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const rows = history.map((m) => {
    const summary = m.items.map((i) => `${i.foodName} (${i.quantity} ${i.unit})`).join(', ');
    return [
      m.mealId,
      m.timestamp,
      m.mealLabel,
      summary,
      m.totals.itemCount,
      m.totals.totalGrams,
      m.totals.totalCalories,
      m.totals.totalProteinG,
      m.totals.totalCarbsG,
      m.totals.totalFatG,
      m.totals.totalFibreG,
    ]
      .map(escape)
      .join(',');
  });
  return [headers.join(','), ...rows].join('\n');
}

export function triggerCsvDownload(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
