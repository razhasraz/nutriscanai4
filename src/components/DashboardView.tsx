import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ArrowLeft, Download, AlertTriangle } from 'lucide-react';
import {
  MealAnalysisResult,
  exportMealToCsv,
  triggerCsvDownload,
} from '../engine/nutritionEngine';
import { MealIntelligenceCard } from './MealIntelligenceCard';

interface DashboardViewProps {
  analysis: MealAnalysisResult | null;
  recentHistory: MealAnalysisResult[];
  onSelectHistoricalMeal: (meal: MealAnalysisResult) => void;
  onBackToScanner: () => void;
}

const MACRO_COLORS = ['#294C38', '#527B60', '#C4955A'];

export const DashboardView: React.FC<DashboardViewProps> = ({
  analysis,
  recentHistory,
  onSelectHistoricalMeal,
  onBackToScanner,
}) => {
  if (!analysis || analysis.items.length === 0) {
    return (
      <div className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-10 text-center max-w-2xl mx-auto">
        <p className="text-xs font-medium text-[#527B60] mb-2">Nutrition Dashboard</p>
        <h2 className="font-editorial text-2xl font-semibold text-[#294C38]">
          No meal analysed yet
        </h2>
        <p className="text-sm text-[#758276] mt-2 leading-relaxed">
          Scan a meal or confirm your portions in the Live Food Scanner to view your macronutrient
          breakdown, Meal Intelligence insights, and AI Detection transparency report.
        </p>
        <button
          type="button"
          onClick={onBackToScanner}
          className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Go to Live Scanner
        </button>
      </div>
    );
  }

  const { totals, macroEnergyPct, items, missingFoods } = analysis;
  const matchedItems = items.filter((i) => i.inDatabase);

  const donutData = [
    { name: 'Protein', value: macroEnergyPct.proteinPct, grams: totals.totalProteinG },
    { name: 'Carbohydrates', value: macroEnergyPct.carbsPct, grams: totals.totalCarbsG },
    { name: 'Fat', value: macroEnergyPct.fatPct, grams: totals.totalFatG },
  ].filter((d) => d.value > 0);

  const calorieBarData = [...matchedItems]
    .sort((a, b) => (b.calories ?? 0) - (a.calories ?? 0))
    .map((item) => ({
      name: item.foodName,
      calories: item.calories ?? 0,
      category: item.category,
    }));

  const nutrientGroupedData = matchedItems.map((item) => ({
    name: item.foodName.length > 14 ? `${item.foodName.slice(0, 12)}…` : item.foodName,
    fullName: item.foodName,
    Protein: item.proteinG ?? 0,
    Carbs: item.carbsG ?? 0,
    Fat: item.fatG ?? 0,
    Fibre: item.fibreG ?? 0,
  }));

  const handleExport = () => {
    const csv = exportMealToCsv(analysis);
    triggerCsvDownload(csv, `nutriscan_${analysis.mealId}.csv`);
  };

  return (
    <div className="space-y-8">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-[#527B60] mb-1">
            Nutrition Analysis · {analysis.timestamp}
          </p>
          <h1 className="font-editorial text-3xl sm:text-4xl font-semibold text-[#294C38] tracking-tight">
            {analysis.mealLabel}
          </h1>
          <p className="text-sm text-[#758276] mt-1">
            Calculated strictly from confirmed portions and ICMR-NIN / USDA reference tables.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={onBackToScanner}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] rounded-lg transition-colors whitespace-nowrap"
          >
            <ArrowLeft className="w-4 h-4" />
            New Scan
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors whitespace-nowrap"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Missing Foods Warning (Honesty Check) */}
      {missingFoods.length > 0 && (
        <div
          role="status"
          className="bg-[#F6F0E4] border border-[#E2D3B5] rounded-xl p-4 flex items-start gap-3 text-sm text-[#6B4A1E]"
        >
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Not in Reference Database:</span>{' '}
            {missingFoods.join(', ')}. Nutritional values for unlisted items are omitted rather than
            fabricated.
          </div>
        </div>
      )}

      {/* 5 Primary Nutrient KPI Cards */}
      <section aria-label="Meal nutritional totals" className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          {
            label: 'Estimated Calories',
            value: `${Math.round(totals.totalCalories)} kcal`,
            sub: `${totals.totalGrams} g total weight`,
          },
          {
            label: 'Protein',
            value: `${totals.totalProteinG.toFixed(1)} g`,
            sub: `${Math.round(macroEnergyPct.proteinPct)}% of macro energy`,
          },
          {
            label: 'Carbohydrates',
            value: `${totals.totalCarbsG.toFixed(1)} g`,
            sub: `${Math.round(macroEnergyPct.carbsPct)}% of macro energy`,
          },
          {
            label: 'Fat',
            value: `${totals.totalFatG.toFixed(1)} g`,
            sub: `${Math.round(macroEnergyPct.fatPct)}% of macro energy`,
          },
          {
            label: 'Dietary Fibre',
            value: `${totals.totalFibreG.toFixed(1)} g`,
            sub: `${totals.matchedItemCount} of ${totals.itemCount} matched`,
          },
        ].map((kpi) => (
          <div
            key={kpi.label}
            className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-5 flex flex-col justify-between"
          >
            <span className="text-xs font-medium text-[#758276]">{kpi.label}</span>
            <span className="font-heading text-2xl font-bold text-[#294C38] tabular-nums mt-2">
              {kpi.value}
            </span>
            <span className="text-xs text-[#758276] mt-1.5 tabular-nums">{kpi.sub}</span>
          </div>
        ))}
      </section>

      {/* Signature Feature: NutriScan Meal Intelligence */}
      <MealIntelligenceCard analysis={analysis} />

      {/* Interactive Nutrition Charts */}
      {matchedItems.length > 0 && (
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Macro Donut Chart */}
          <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6">
            <h3 className="text-base font-bold text-[#294C38]">Macronutrient Energy Split</h3>
            <p className="text-xs text-[#758276] mt-0.5 mb-4">
              Percentage of estimated caloric energy (4 kcal/g protein &amp; carbs, 9 kcal/g fat)
            </p>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="48%"
                    innerRadius={62}
                    outerRadius={96}
                    paddingAngle={2}
                    stroke="#FFFFFF"
                    strokeWidth={2}
                  >
                    {donutData.map((entry, idx) => (
                      <Cell key={entry.name} fill={MACRO_COLORS[idx % MACRO_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name, item) => [
                      `${value ?? 0}% (${(item?.payload as { grams?: number } | undefined)?.grams?.toFixed?.(1) ?? 0} g)`,
                      String(name ?? ''),
                    ]}
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#DCE4D9',
                      borderRadius: '10px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend verticalAlign="bottom" height={32} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Calorie Contribution Horizontal Bar Chart */}
          <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6">
            <h3 className="text-base font-bold text-[#294C38]">
              Calorie Contribution by Food Item
            </h3>
            <p className="text-xs text-[#758276] mt-0.5 mb-4">
              Individual estimated kcal based on confirmed portions
            </p>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={calorieBarData}
                  layout="vertical"
                  margin={{ top: 8, right: 28, left: 16, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8F0E5" horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fill: '#758276', fontSize: 12 }}
                    axisLine={{ stroke: '#DCE4D9' }}
                    tickLine={false}
                  />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={110}
                    tick={{ fill: '#25352B', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(val) => [`${Math.round(Number(val ?? 0))} kcal`, 'Calories']}
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#DCE4D9',
                      borderRadius: '10px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="calories" radius={[0, 6, 6, 0]} maxBarSize={28}>
                    {calorieBarData.map((entry, idx) => (
                      <Cell
                        key={`${entry.name}-${idx}`}
                        fill={entry.category === 'Indian' ? '#527B60' : '#A8BCA6'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Grouped Macronutrient Breakdown (g) */}
          <div className="lg:col-span-12 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6">
            <h3 className="text-base font-bold text-[#294C38]">
              Nutrient Breakdown per Food (grams)
            </h3>
            <p className="text-xs text-[#758276] mt-0.5 mb-4">
              Comparing protein, carbohydrates, fat, and dietary fibre across items on this plate
            </p>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={nutrientGroupedData}
                  margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8F0E5" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#25352B', fontSize: 12 }}
                    axisLine={{ stroke: '#DCE4D9' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#758276', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                    unit="g"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#DCE4D9',
                      borderRadius: '10px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend iconType="circle" />
                  <Bar dataKey="Protein" fill="#294C38" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Carbs" fill="#527B60" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Fat" fill="#C4955A" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Fibre" fill="#A8BCA6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      )}

      {/* Individual Food Contributions Table */}
      <section className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[#E8F0E5]">
          <h3 className="text-base font-bold text-[#294C38]">Individual Food Contributions</h3>
          <p className="text-xs text-[#758276] mt-0.5">
            Reference sources and recipe caveats for every confirmed item
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-[#F3F7F0] text-xs text-[#758276] border-b border-[#DCE4D9]">
                <th className="py-3 px-5 font-semibold">Food Item</th>
                <th className="py-3 px-4 font-semibold">Confirmed Portion</th>
                <th className="py-3 px-4 font-semibold text-right">Calories</th>
                <th className="py-3 px-4 font-semibold text-right">Protein</th>
                <th className="py-3 px-4 font-semibold text-right">Carbs</th>
                <th className="py-3 px-4 font-semibold text-right">Fat</th>
                <th className="py-3 px-4 font-semibold text-right">Fibre</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8F0E5]">
              {items.map((item, idx) => (
                <tr key={`${item.foodName}-${idx}`} className="hover:bg-[#F3F7F0]/50">
                  <td className="py-3.5 px-5">
                    <div className="font-semibold text-[#25352B]">{item.foodName}</div>
                    <div className="text-xs text-[#758276] mt-0.5">
                      {item.category} · {item.foodGroup} · {item.source}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 tabular-nums">
                    <div className="text-[#25352B]">
                      {item.quantity} {item.unit}
                    </div>
                    <div className="text-xs text-[#758276]">
                      {item.grams} g · {item.portionSource}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right font-semibold text-[#294C38] tabular-nums">
                    {item.inDatabase ? `${Math.round(item.calories ?? 0)} kcal` : 'Not in DB'}
                  </td>
                  <td className="py-3.5 px-4 text-right tabular-nums text-[#25352B]">
                    {item.inDatabase ? `${(item.proteinG ?? 0).toFixed(1)} g` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right tabular-nums text-[#25352B]">
                    {item.inDatabase ? `${(item.carbsG ?? 0).toFixed(1)} g` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right tabular-nums text-[#25352B]">
                    {item.inDatabase ? `${(item.fatG ?? 0).toFixed(1)} g` : '—'}
                  </td>
                  <td className="py-3.5 px-4 text-right tabular-nums text-[#25352B]">
                    {item.inDatabase ? `${(item.fibreG ?? 0).toFixed(1)} g` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* AI Transparency: AI Detection Insights */}
      <section className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[#E8F0E5]">
          <p className="text-xs font-medium text-[#527B60] mb-1">AI Transparency</p>
          <h3 className="text-base font-bold text-[#294C38]">AI Detection Insights</h3>
          <p className="text-xs text-[#758276] mt-0.5 max-w-2xl">
            Every AI prediction, visual certainty tier, and human verification edit is recorded
            openly. AI visual recognition can misread gravies or hidden ingredients, so human
            verification remains part of every analysis.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-[#F3F7F0] text-xs text-[#758276] border-b border-[#DCE4D9]">
                <th className="py-3 px-5 font-semibold">Confirmed Food</th>
                <th className="py-3 px-4 font-semibold">Original AI Label</th>
                <th className="py-3 px-4 font-semibold">Visual Certainty</th>
                <th className="py-3 px-4 font-semibold">Verification Status</th>
                <th className="py-3 px-4 font-semibold">Portion Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8F0E5]">
              {items.map((item, idx) => {
                const certaintyText =
                  item.detectionCertainty === 'high'
                    ? 'High certainty'
                    : item.detectionCertainty === 'medium'
                    ? 'Medium certainty'
                    : item.detectionCertainty === 'low'
                    ? 'Low — verified by user'
                    : 'Manual entry';

                return (
                  <tr key={`ai-${item.foodName}-${idx}`} className="hover:bg-[#F3F7F0]/50">
                    <td className="py-3 px-5">
                      <div className="font-medium text-[#25352B]">{item.foodName}</div>
                      {item.visualNote && (
                        <div className="text-xs text-[#758276] mt-0.5">{item.visualNote}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[#758276]">
                      {item.originalAiLabel ?? 'Added manually'}
                    </td>
                    <td className="py-3 px-4 text-[#25352B]">{certaintyText}</td>
                    <td className="py-3 px-4 text-[#294C38] font-medium">
                      {item.verificationStatus}
                    </td>
                    <td className="py-3 px-4 text-[#758276]">{item.portionSource}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Previous Analysis Quick Switcher */}
      {recentHistory.length > 1 && (
        <section className="bg-[#E8F0E5]/65 border border-[#DCE4D9] rounded-2xl p-6">
          <h3 className="text-sm font-bold text-[#294C38] mb-3">Previous Analysis Summaries</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {recentHistory.slice(0, 6).map((meal) => {
              const active = meal.mealId === analysis.mealId;
              return (
                <button
                  key={meal.mealId}
                  type="button"
                  onClick={() => onSelectHistoricalMeal(meal)}
                  className={`text-left p-4 rounded-xl border transition-colors ${
                    active
                      ? 'bg-[#FFFFFF] border-[#527B60]'
                      : 'bg-[#FFFFFF]/80 border-[#DCE4D9] hover:border-[#A8BCA6]'
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-sm font-semibold text-[#294C38] truncate">
                      {meal.mealLabel}
                    </span>
                    <span className="text-xs font-semibold text-[#527B60] tabular-nums shrink-0">
                      {Math.round(meal.totals.totalCalories)} kcal
                    </span>
                  </div>
                  <p className="text-xs text-[#758276] mt-1 tabular-nums">{meal.timestamp}</p>
                  <p className="text-xs text-[#25352B] mt-1.5 truncate">
                    {meal.items.map((i) => i.foodName).join(', ')}
                  </p>
                </button>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
};
