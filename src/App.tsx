import { useEffect, useRef, useState } from 'react';
import { Header, NavSection } from './components/Header';
import { ScannerWorkspace } from './components/ScannerWorkspace';
import { DashboardView } from './components/DashboardView';
import { HistoryView } from './components/HistoryView';
import { DatabaseView } from './components/DatabaseView';
import {
  MealAnalysisResult,
  PlateItemDraft,
  analyzeMeal,
} from './engine/nutritionEngine';

const STORAGE_KEY = 'nutriscan_ai_meal_history_v2';

function loadSavedHistory(): MealAnalysisResult[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [activeSection, setActiveSection] = useState<NavSection>('scanner');
  const [plateItems, setPlateItems] = useState<PlateItemDraft[]>([]);
  const [mealLabel, setMealLabel] = useState<string>('Everyday Meal');
  const [history, setHistory] = useState<MealAnalysisResult[]>(() => loadSavedHistory());
  const [latestAnalysis, setLatestAnalysis] = useState<MealAnalysisResult | null>(
    () => loadSavedHistory()[0] ?? null
  );

  const scannerSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {
      // Ignore storage quota errors in restricted preview contexts
    }
  }, [history]);

  const handleStartScanning = () => {
    setActiveSection('scanner');
    requestAnimationFrame(() => {
      scannerSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  const handleAnalyzeMeal = () => {
    const confirmed = plateItems.filter((item) => item.confirmed && item.foodName.trim());
    if (confirmed.length === 0) return;

    const result = analyzeMeal(confirmed, mealLabel);
    setLatestAnalysis(result);
    setHistory((prev) => [result, ...prev]);
    setActiveSection('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleClearHistory = () => {
    setHistory([]);
    setLatestAnalysis(null);
  };

  const handleOpenInDashboard = (meal: MealAnalysisResult) => {
    setLatestAnalysis(meal);
    setActiveSection('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F3F7F0] text-[#25352B]">
      <Header
        activeSection={activeSection}
        onNavigate={(section) => {
          setActiveSection(section);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        onStartScanning={handleStartScanning}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {activeSection === 'scanner' && (
          <ScannerWorkspace
            plateItems={plateItems}
            onChangePlateItems={setPlateItems}
            mealLabel={mealLabel}
            onChangeMealLabel={setMealLabel}
            onAnalyzeMeal={handleAnalyzeMeal}
            onExploreDatabase={() => {
              setActiveSection('database');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            scannerSectionRef={scannerSectionRef}
          />
        )}

        {activeSection === 'dashboard' && (
          <DashboardView
            analysis={latestAnalysis}
            recentHistory={history}
            onSelectHistoricalMeal={(meal) => setLatestAnalysis(meal)}
            onBackToScanner={handleStartScanning}
          />
        )}

        {activeSection === 'history' && (
          <HistoryView
            history={history}
            onClearHistory={handleClearHistory}
            onOpenInDashboard={handleOpenInDashboard}
            onGoToScanner={handleStartScanning}
          />
        )}

        {activeSection === 'database' && <DatabaseView />}
      </main>

      <footer className="border-t border-[#DCE4D9] bg-[#E8F0E5]/60 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs text-[#758276]">
          <div>
            <span className="font-editorial text-sm font-semibold text-[#294C38]">
              NutriScan AI
            </span>
            <span className="mx-2">·</span>
            <span>Scan. Understand. Nourish.</span>
          </div>
          <p>
            Nutritional estimates use ICMR-NIN IFCT 2017 &amp; USDA FoodData Central references for
            general awareness and education. Not a medical or clinical tool.
          </p>
        </div>
      </footer>
    </div>
  );
}
