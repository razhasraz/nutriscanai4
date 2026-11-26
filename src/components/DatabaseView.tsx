import React, { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import {
  FOOD_GROUP_CATALOG,
  FOOD_NUTRITION_DATABASE,
  FoodCategory,
  FoodGroup,
  PORTION_REFERENCE_DATABASE,
} from '../data/nutritionData';

const BANNER_IMG = '/src/assets/images/editorial_botanical_plate_1795712772778.jpg';

export const DatabaseView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<'All' | FoodCategory>('All');
  const [groupFilter, setGroupFilter] = useState<'All' | FoodGroup>('All');
  const [imgFailed, setImgFailed] = useState(false);

  const portionMap = useMemo(
    () => new Map(PORTION_REFERENCE_DATABASE.map((p) => [p.foodName, p])),
    []
  );

  const filteredFoods = useMemo(() => {
    const q = query.trim().toLowerCase();
    return FOOD_NUTRITION_DATABASE.filter((item) => {
      if (categoryFilter !== 'All' && item.category !== categoryFilter) return false;
      if (groupFilter !== 'All' && item.foodGroup !== groupFilter) return false;
      if (
        q &&
        !item.foodName.toLowerCase().includes(q) &&
        !item.foodGroup.toLowerCase().includes(q) &&
        !item.source.toLowerCase().includes(q)
      ) {
        return false;
      }
      return true;
    });
  }, [query, categoryFilter, groupFilter]);

  return (
    <div className="space-y-8">
      {/* Editorial Banner */}
      <section className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
        <div className="lg:col-span-7 p-7 sm:p-9 flex flex-col justify-center">
          <p className="text-xs font-medium text-[#527B60] mb-2">
            Indian Food Intelligence · Reference Data
          </p>
          <h1 className="font-editorial text-3xl sm:text-4xl font-semibold text-[#294C38] tracking-tight">
            Nutrition &amp; Portion Reference Database
          </h1>
          <p className="text-sm text-[#758276] mt-3 leading-relaxed max-w-xl">
            Every calculation in NutriScan AI is traced back to these 40 curated entries from
            ICMR-NIN IFCT 2017 and USDA FoodData Central, paired with everyday Indian serving units
            including katoris, rotis, pieces, cups, and grams.
          </p>
          <p className="text-xs text-[#294C38] mt-4">
            <strong>On-Device Recognition Transparency:</strong> The browser-local COCO-SSD model
            directly detects Apple, Banana, Orange, Pizza, Sandwich, and Cake, and flags bowls/cups
            for quick selection across all 40 Indian and international foods—with zero external API
            keys required.
          </p>
        </div>
        <div className="lg:col-span-5 min-h-[210px] bg-[#E8F0E5]">
          {!imgFailed ? (
            <img
              src={BANNER_IMG}
              alt="Steamed idli, paneer cubes, yellow dal, green apple slices, and fresh herbs on sage ceramic dishes"
              referrerPolicy="no-referrer"
              onError={() => setImgFailed(true)}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center p-6 text-center">
              <span className="font-editorial text-lg text-[#294C38]">
                40 Verified Foods · ICMR-NIN &amp; USDA
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Filter Controls */}
      <section className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-5 flex flex-col md:flex-row md:items-center gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-[#758276] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Roti, Dal, Paneer, Idli, Poha, Rajma..."
            className="w-full pl-10 pr-4 py-2 text-sm bg-[#F3F7F0] border border-[#DCE4D9] rounded-lg focus:outline-none focus:border-[#527B60]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex p-1 bg-[#E8F0E5] rounded-lg">
            {(['All', 'Indian', 'International'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
                  categoryFilter === cat
                    ? 'bg-[#FFFFFF] text-[#294C38] shadow-xs'
                    : 'text-[#758276] hover:text-[#25352B]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <select
            aria-label="Filter by food group"
            value={groupFilter}
            onChange={(e) => setGroupFilter(e.target.value as 'All' | FoodGroup)}
            className="px-3 py-2 text-xs font-medium bg-[#F3F7F0] border border-[#DCE4D9] rounded-lg text-[#25352B] focus:outline-none focus:border-[#527B60]"
          >
            <option value="All">All Food Groups</option>
            {FOOD_GROUP_CATALOG.map((grp) => (
              <option key={grp} value={grp}>
                {grp}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Reference Table */}
      <section className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#E8F0E5] flex items-center justify-between">
          <h2 className="text-sm font-bold text-[#294C38]">
            Nutritional Values per 100 g &amp; Portion Standards
          </h2>
          <span className="text-xs text-[#758276] tabular-nums">
            Showing {filteredFoods.length} of {FOOD_NUTRITION_DATABASE.length} foods
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-[#F3F7F0] text-xs text-[#758276] border-b border-[#DCE4D9]">
                <th className="py-3 px-5 font-semibold">Food Item</th>
                <th className="py-3 px-3 font-semibold text-right">kcal</th>
                <th className="py-3 px-3 font-semibold text-right">Protein</th>
                <th className="py-3 px-3 font-semibold text-right">Carbs</th>
                <th className="py-3 px-3 font-semibold text-right">Fat</th>
                <th className="py-3 px-3 font-semibold text-right">Fibre</th>
                <th className="py-3 px-4 font-semibold">Default Portion</th>
                <th className="py-3 px-4 font-semibold">Recipe Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8F0E5]">
              {filteredFoods.map((food) => {
                const portion = portionMap.get(food.foodName);
                const portionSummary = portion
                  ? `${portion.defaultQuantity} ${portion.defaultUnit}${
                      portion.gramsPerKatori > 0
                        ? ` · 1 katori ≈ ${portion.gramsPerKatori}g`
                        : portion.gramsPerPiece > 0
                        ? ` · 1 piece ≈ ${portion.gramsPerPiece}g`
                        : ` · 1 serving ≈ ${portion.gramsPerServing}g`
                    }`
                  : '100 g';

                return (
                  <tr key={food.foodName} className="hover:bg-[#F3F7F0]/50">
                    <td className="py-3.5 px-5">
                      <div className="font-semibold text-[#25352B]">{food.foodName}</div>
                      <div className="text-xs text-[#758276] mt-0.5">
                        {food.category} · {food.foodGroup} · {food.source}
                      </div>
                    </td>
                    <td className="py-3.5 px-3 text-right font-semibold text-[#294C38] tabular-nums">
                      {food.caloriesPer100g}
                    </td>
                    <td className="py-3.5 px-3 text-right tabular-nums text-[#25352B]">
                      {food.proteinPer100g.toFixed(1)}g
                    </td>
                    <td className="py-3.5 px-3 text-right tabular-nums text-[#25352B]">
                      {food.carbsPer100g.toFixed(1)}g
                    </td>
                    <td className="py-3.5 px-3 text-right tabular-nums text-[#25352B]">
                      {food.fatPer100g.toFixed(1)}g
                    </td>
                    <td className="py-3.5 px-3 text-right tabular-nums text-[#25352B]">
                      {food.fibrePer100g.toFixed(1)}g
                    </td>
                    <td className="py-3.5 px-4 text-xs text-[#25352B] tabular-nums">
                      {portionSummary}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-[#758276] max-w-xs">
                      {food.notes}
                    </td>
                  </tr>
                );
              })}
              {filteredFoods.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-sm text-[#758276]">
                    No foods matched "{query}". Try searching for Dal, Roti, Paneer, Idli, or Apple.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
