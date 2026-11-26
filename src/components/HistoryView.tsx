import React, { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ArrowRight, Download, Trash2 } from 'lucide-react';
import {
  MealAnalysisResult,
  computeMealPatternInsights,
  exportHistoryToCsv,
  triggerCsvDownload,
} from '../engine/nutritionEngine';
import { MealIntelligenceCard } from './MealIntelligenceCard';

interface HistoryViewProps {
  history: MealAnalysisResult[];
  onClearHistory: () => void;
  onOpenInDashboard: (meal: MealAnalysisResult) => void;
  onGoToScanner: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  history,
  onClearHistory,
  onOpenInDashboard,
  onGoToScanner,
}) => {
  const [selectedMealId, setSelectedMealId] = useState<string | null>(
    history[0]?.mealId ?? null
  );
  const [confirmClear, setConfirmClear] = useState(false);

  const selectedMeal =
    history.find((m) => m.mealId === selectedMealId) ?? history[0] ?? null;

  const patterns = computeMealPatternInsights(history);

  if (history.length === 0) {
    return (
      <div className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-10 text-center max-w-2xl mx-auto">
        <p className="text-xs font-medium text-[#527B60] mb-2">Meal History &amp; Pattern Insights</p>
        <h2 className="font-editorial text-2xl font-semibold text-[#294C38]">
          No recorded meals yet
        </h2>
        <p className="text-sm text-[#758276] mt-2 leading-relaxed">
          Analyse your first meal in the Live Food Scanner to record confirmed portions,
          nutritional summaries, and build your real historical baseline.
        </p>
        <button
          type="button"
          onClick={onGoToScanner}
          className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors"
        >
          Scan Your First Meal
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  const avgCalories =
    history.reduce((s, m) => s + m.totals.totalCalories, 0) / history.length;
  const avgProtein =
    history.reduce((s, m) => s + m.totals.totalProteinG, 0) / history.length;
  const avgFibre =
    history.reduce((s, m) => s + m.totals.totalFibreG, 0) / history.length;

  const handleExportHistory = () => {
    const csv = exportHistoryToCsv(history);
    triggerCsvDownload(csv, 'nutriscan_meal_history.csv');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-[#527B60] mb-1">
            Meal History · Longitudinal Awareness
          </p>
          <h1 className="font-editorial text-3xl sm:text-4xl font-semibold text-[#294C38] tracking-tight">
            Meal History &amp; Pattern Insights
          </h1>
          <p className="text-sm text-[#758276] mt-1">
            Inspect previous meal analyses, export your CSV log, and observe patterns across
            recorded meals.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleExportHistory}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors whitespace-nowrap"
          >
            <Download className="w-4 h-4" />
            Export History CSV
          </button>

          {!confirmClear ? (
            <button
              type="button"
              onClick={() => setConfirmClear(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium text-[#758276] hover:text-[#9A3412] bg-[#FFFFFF] border border-[#DCE4D9] rounded-lg transition-colors whitespace-nowrap"
            >
              <Trash2 className="w-4 h-4" />
              Clear Log
            </button>
          ) : (
            <div className="inline-flex items-center gap-2 bg-[#F6F0E4] border border-[#E2D3B5] px-3 py-1.5 rounded-lg text-xs">
              <span className="text-[#6B4A1E] font-medium">Clear all history?</span>
              <button
                type="button"
                onClick={() => {
                  onClearHistory();
                  setConfirmClear(false);
                }}
                className="font-semibold text-[#9A3412] hover:underline"
              >
                Confirm
              </button>
              <button
                type="button"
                onClick={() => setConfirmClear(false)}
                className="text-[#758276] hover:text-[#25352B]"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Summary KPI Strip */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Recorded Meals', value: `${history.length}` },
          { label: 'Average Calories / Meal', value: `${Math.round(avgCalories)} kcal` },
          { label: 'Average Protein / Meal', value: `${avgProtein.toFixed(1)} g` },
          { label: 'Average Fibre / Meal', value: `${avgFibre.toFixed(1)} g` },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-5"
          >
            <span className="text-xs font-medium text-[#758276]">{stat.label}</span>
            <p className="font-heading text-2xl font-bold text-[#294C38] tabular-nums mt-2">
              {stat.value}
            </p>
          </div>
        ))}
      </section>

      {/* Recorded Meals Table + Inspector */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-[#E8F0E5]">
            <h2 className="text-base font-bold text-[#294C38]">Saved Meal Records</h2>
            <p className="text-xs text-[#758276] mt-0.5">Select any entry to inspect its full breakdown</p>
          </div>
          <div className="divide-y divide-[#E8F0E5] max-h-[520px] overflow-y-auto">
            {history.map((meal) => {
              const isSelected = selectedMeal?.mealId === meal.mealId;
              return (
                <button
                  key={meal.mealId}
                  type="button"
                  onClick={() => setSelectedMealId(meal.mealId)}
                  className={`w-full text-left p-4 transition-colors ${
                    isSelected ? 'bg-[#DCEBDD]/45' : 'hover:bg-[#F3F7F0]'
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-sm font-semibold text-[#294C38]">
                      {meal.mealLabel}
                    </span>
                    <span className="text-xs font-semibold text-[#527B60] tabular-nums shrink-0">
                      {Math.round(meal.totals.totalCalories)} kcal
                    </span>
                  </div>
                  <p className="text-xs text-[#758276] mt-0.5 tabular-nums">{meal.timestamp}</p>
                  <p className="text-xs text-[#25352B] mt-1.5 line-clamp-2">
                    {meal.items.map((i) => `${i.foodName} (${i.quantity} ${i.unit})`).join(', ')}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Meal Inspector */}
        <div className="lg:col-span-7 space-y-5">
          {selectedMeal && (
            <>
              <div className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6 space-y-4">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <div>
                    <p className="text-xs text-[#758276] tabular-nums">{selectedMeal.timestamp}</p>
                    <h3 className="text-lg font-bold text-[#294C38] mt-0.5">
                      {selectedMeal.mealLabel}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => onOpenInDashboard(selectedMeal)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#527B60] hover:text-[#294C38]"
                  >
                    Open Full Dashboard
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-[#25352B] tabular-nums border-y border-[#E8F0E5] py-3">
                  <span>
                    Calories: <strong>{Math.round(selectedMeal.totals.totalCalories)} kcal</strong>
                  </span>
                  <span>
                    Protein: <strong>{selectedMeal.totals.totalProteinG.toFixed(1)} g</strong>
                  </span>
                  <span>
                    Carbs: <strong>{selectedMeal.totals.totalCarbsG.toFixed(1)} g</strong>
                  </span>
                  <span>
                    Fat: <strong>{selectedMeal.totals.totalFatG.toFixed(1)} g</strong>
                  </span>
                  <span>
                    Fibre: <strong>{selectedMeal.totals.totalFibreG.toFixed(1)} g</strong>
                  </span>
                </div>

                <div className="divide-y divide-[#E8F0E5] text-sm">
                  {selectedMeal.items.map((item, idx) => (
                    <div
                      key={`${item.foodName}-${idx}`}
                      className="py-2.5 flex items-baseline justify-between gap-4"
                    >
                      <div>
                        <span className="font-medium text-[#25352B]">{item.foodName}</span>
                        <span className="text-xs text-[#758276] ml-2 tabular-nums">
                          {item.quantity} {item.unit} ({item.grams} g)
                        </span>
                      </div>
                      <span className="text-xs font-semibold text-[#294C38] tabular-nums shrink-0">
                        {item.inDatabase ? `${Math.round(item.calories ?? 0)} kcal` : 'Not in DB'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <MealIntelligenceCard analysis={selectedMeal} />
            </>
          )}
        </div>
      </section>

      {/* Future / Longitudinal Section: Meal Pattern Insights */}
      <section className="space-y-4 pt-4 border-t border-[#DCE4D9]">
        <div>
          <p className="text-xs font-medium text-[#527B60] mb-1">Historical Analysis</p>
          <h2 className="font-editorial text-2xl font-semibold text-[#294C38]">
            Meal Pattern Insights
          </h2>
          <p className="text-sm text-[#758276] mt-0.5">
            Trends and composition patterns calculated strictly from your real saved meal records.
          </p>
        </div>

        {!patterns.sufficientData ? (
          <div className="bg-[#F6F0E4] border border-[#E7DEC9] rounded-2xl p-6 text-sm text-[#25352B]">
            <p className="font-semibold text-[#294C38]">Building Your Baseline</p>
            <p className="mt-1.5 leading-relaxed text-[#25352B]">
              {patterns.message} Log {patterns.requiredMeals - patterns.mealCount} more meal
              {patterns.requiredMeals - patterns.mealCount === 1 ? '' : 's'} to unlock nutrient
              trend lines and frequently analysed food summaries. NutriScan AI never fabricates
              historical records.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-[#DCEBDD]/55 border border-[#C6DBC8] rounded-xl p-4 text-sm text-[#25352B]">
              Across <strong>{patterns.mealCount}</strong> recorded meals, recent entries average{' '}
              <strong className="tabular-nums">
                {(patterns.recentShifts?.proteinDeltaG ?? 0) >= 0 ? '+' : ''}
                {patterns.recentShifts?.proteinDeltaG.toFixed(1)} g
              </strong>{' '}
              protein and{' '}
              <strong className="tabular-nums">
                {(patterns.recentShifts?.fibreDeltaG ?? 0) >= 0 ? '+' : ''}
                {patterns.recentShifts?.fibreDeltaG.toFixed(1)} g
              </strong>{' '}
              fibre per meal compared with your earlier recorded entries.
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6">
                <h3 className="text-base font-bold text-[#294C38] mb-4">
                  Recorded Nutrient Trends Over Time (g)
                </h3>
                <div className="h-[260px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={patterns.timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E8F0E5" vertical={false} />
                      <XAxis dataKey="label" tick={{ fill: '#758276', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#758276', fontSize: 11 }} unit="g" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#FFFFFF',
                          borderColor: '#DCE4D9',
                          borderRadius: '10px',
                          fontSize: '12px',
                        }}
                      />
                      <Legend iconType="circle" />
                      <Line
                        type="monotone"
                        dataKey="proteinG"
                        name="Protein (g)"
                        stroke="#294C38"
                        strokeWidth={2.2}
                        dot={{ r: 4 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="carbsG"
                        name="Carbs (g)"
                        stroke="#527B60"
                        strokeWidth={2.2}
                        dot={{ r: 4 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="fatG"
                        name="Fat (g)"
                        stroke="#C4955A"
                        strokeWidth={2}
                        dot={{ r: 3.5 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="fibreG"
                        name="Fibre (g)"
                        stroke="#A8BCA6"
                        strokeWidth={2}
                        strokeDasharray="4 4"
                        dot={{ r: 3.5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6">
                <h3 className="text-base font-bold text-[#294C38] mb-4">
                  Frequently Analysed Foods
                </h3>
                <div className="h-[260px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={patterns.topFoods}
                      layout="vertical"
                      margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#E8F0E5" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} tick={{ fill: '#758276', fontSize: 11 }} />
                      <YAxis
                        dataKey="foodName"
                        type="category"
                        width={105}
                        tick={{ fill: '#25352B', fontSize: 11 }}
                      />
                      <Tooltip
                        formatter={(v) => [`${v ?? 0} meal(s)`, 'Recorded']}
                        contentStyle={{
                          backgroundColor: '#FFFFFF',
                          borderColor: '#DCE4D9',
                          borderRadius: '10px',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="count" fill="#527B60" radius={[0, 6, 6, 0]} maxBarSize={24} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
