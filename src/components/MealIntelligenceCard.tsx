import React from 'react';
import { MealAnalysisResult, computeMealIntelligence } from '../engine/nutritionEngine';

interface MealIntelligenceCardProps {
  analysis: MealAnalysisResult;
}

export const MealIntelligenceCard: React.FC<MealIntelligenceCardProps> = ({ analysis }) => {
  const report = computeMealIntelligence(analysis);
  const { composition, nutritionalBalance, foodGroupVariety, contextualSuggestions } = report;

  return (
    <section
      aria-labelledby="meal-intelligence-heading"
      className="bg-[#FFFFFF] border border-[#A8BCA6] rounded-2xl p-6 sm:p-8 shadow-[0_10px_30px_-22px_rgba(41,76,56,0.22)]"
    >
      {/* Header */}
      <div className="pb-6 border-b border-[#DCE4D9] flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <p className="text-xs font-medium text-[#527B60] mb-1.5">
            Signature Feature · Holistic Plate Analysis
          </p>
          <h2
            id="meal-intelligence-heading"
            className="font-editorial text-2xl sm:text-3xl font-semibold text-[#294C38] tracking-tight"
          >
            NutriScan Meal Intelligence
          </h2>
          <p className="text-sm text-[#758276] mt-1.5 max-w-2xl">
            Synthesising confirmed food items, portion weights, and food-group diversity into clear
            nutritional awareness.
          </p>
        </div>
        <div className="text-xs text-[#758276] tabular-nums shrink-0">
          {foodGroupVariety.representedCount} food group
          {foodGroupVariety.representedCount === 1 ? '' : 's'} represented ·{' '}
          {Math.round(nutritionalBalance.calories)} kcal total
        </div>
      </div>

      {/* Main 2-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
        {/* 1. Meal Composition */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-baseline justify-between">
            <h3 className="text-sm font-semibold text-[#294C38]">01. Meal Composition</h3>
            <span className="text-xs text-[#758276]">Share of estimated energy</span>
          </div>

          {composition.length === 0 ? (
            <p className="text-sm text-[#758276] py-4">
              No database-matched items available for composition analysis.
            </p>
          ) : (
            <div className="divide-y divide-[#E8F0E5]">
              {composition.map((item, idx) => (
                <div key={`${item.foodName}-${idx}`} className="py-3.5 first:pt-0 last:pb-0">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-sm font-semibold text-[#25352B]">{item.foodName}</span>
                    <span className="text-sm font-semibold text-[#294C38] tabular-nums shrink-0">
                      {Math.round(item.calories)} kcal · {Math.round(item.calorieSharePct)}%
                    </span>
                  </div>
                  <div className="text-xs text-[#758276] mt-1 tabular-nums">
                    {item.foodGroup} · {item.portionLabel} ({item.grams} g) · P{' '}
                    {item.proteinG.toFixed(1)}g · C {item.carbsG.toFixed(1)}g · F{' '}
                    {item.fatG.toFixed(1)}g
                  </div>
                  <div className="mt-2 h-1.5 w-full bg-[#E8F0E5] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#527B60] rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(Math.max(item.calorieSharePct, 3), 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 2. Nutritional Balance & 3. Food-Group Variety */}
        <div className="lg:col-span-6 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-[#294C38] mb-3">02. Nutritional Balance</h3>
            <div className="bg-[#DCEBDD]/55 rounded-xl p-4 sm:p-5 border border-[#C6DBC8]">
              <p className="text-sm text-[#25352B] leading-relaxed">
                {nutritionalBalance.summary}
              </p>

              {/* Stacked energy proportion bar */}
              {nutritionalBalance.calories > 0 && (
                <div className="mt-4">
                  <div className="h-2.5 w-full rounded-full overflow-hidden flex bg-[#E8F0E5]">
                    <div
                      style={{ width: `${nutritionalBalance.proteinPct}%` }}
                      className="bg-[#294C38] h-full"
                      title={`Protein ${nutritionalBalance.proteinPct}%`}
                    />
                    <div
                      style={{ width: `${nutritionalBalance.carbsPct}%` }}
                      className="bg-[#527B60] h-full"
                      title={`Carbohydrates ${nutritionalBalance.carbsPct}%`}
                    />
                    <div
                      style={{ width: `${nutritionalBalance.fatPct}%` }}
                      className="bg-[#C4955A] h-full"
                      title={`Fat ${nutritionalBalance.fatPct}%`}
                    />
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1 text-xs text-[#294C38] tabular-nums">
                    <span>
                      Protein: <strong>{nutritionalBalance.proteinG.toFixed(1)} g</strong> (
                      {Math.round(nutritionalBalance.proteinPct)}%)
                    </span>
                    <span>
                      Carbs: <strong>{nutritionalBalance.carbsG.toFixed(1)} g</strong> (
                      {Math.round(nutritionalBalance.carbsPct)}%)
                    </span>
                    <span>
                      Fat: <strong>{nutritionalBalance.fatG.toFixed(1)} g</strong> (
                      {Math.round(nutritionalBalance.fatPct)}%)
                    </span>
                    <span>
                      Fibre: <strong>{nutritionalBalance.fibreG.toFixed(1)} g</strong>
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 3. Food-Group Variety */}
          <div>
            <h3 className="text-sm font-semibold text-[#294C38] mb-3">03. Food-Group Variety</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="border-t border-[#DCE4D9] pt-3">
                <p className="text-xs font-semibold text-[#294C38] mb-2">
                  Represented on this plate
                </p>
                {foodGroupVariety.represented.length === 0 ? (
                  <p className="text-xs text-[#758276]">None recorded yet</p>
                ) : (
                  <ul className="space-y-1.5 text-sm text-[#25352B]">
                    {foodGroupVariety.represented.map((entry) => (
                      <li key={entry.group} className="leading-snug">
                        <span className="font-medium text-[#294C38]">{entry.group}</span>
                        <span className="text-xs text-[#758276] block">
                          {entry.items.join(', ')}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="border-t border-[#DCE4D9] pt-3">
                <p className="text-xs font-semibold text-[#758276] mb-2">
                  Not represented in this meal
                </p>
                {foodGroupVariety.unrepresented.length === 0 ? (
                  <p className="text-sm text-[#294C38]">
                    All primary food groups are represented on this plate.
                  </p>
                ) : (
                  <ul className="space-y-1.5 text-sm text-[#758276]">
                    {foodGroupVariety.unrepresented.map((group) => (
                      <li key={group}>{group}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Contextual Suggestions */}
      <div className="mt-8 pt-6 border-t border-[#DCE4D9]">
        <h3 className="text-sm font-semibold text-[#294C38] mb-3">04. Contextual Suggestions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {contextualSuggestions.map((text, idx) => (
            <div
              key={idx}
              className="bg-[#F6F0E4] border border-[#E7DEC9] rounded-xl px-4 py-3.5 text-sm text-[#25352B] leading-relaxed"
            >
              {text}
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-[#758276]">
          Educational awareness based strictly on your confirmed portions and ICMR-NIN / USDA
          reference data. NutriScan AI does not label foods as good or bad and does not make medical
          claims.
        </p>
      </div>
    </section>
  );
};
