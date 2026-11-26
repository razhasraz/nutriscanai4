import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';

export type NavSection = 'scanner' | 'dashboard' | 'history' | 'database';

interface HeaderProps {
  activeSection: NavSection;
  onNavigate: (section: NavSection) => void;
  onStartScanning: () => void;
}

const NAV_ITEMS: { id: NavSection; label: string }[] = [
  { id: 'scanner', label: 'Scanner' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'history', label: 'History' },
  { id: 'database', label: 'Database' },
];

export const Header: React.FC<HeaderProps> = ({
  activeSection,
  onNavigate,
  onStartScanning,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (section: NavSection) => {
    onNavigate(section);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-[#F3F7F0]/95 backdrop-blur-sm border-b border-[#DCE4D9]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-8">
        {/* Zone 1: Single-line Brand Wordmark */}
        <button
          type="button"
          onClick={() => handleNavClick('scanner')}
          className="flex items-center gap-2.5 text-left whitespace-nowrap shrink-0 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#527B60] rounded"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
            className="shrink-0"
          >
            <path
              d="M5 19C5 11.5 10.2 5.5 19.5 4.5C18.5 13.8 12.5 19 5 19Z"
              fill="#DCEBDD"
              stroke="#294C38"
              strokeWidth="1.75"
              strokeLinejoin="round"
            />
            <path
              d="M5 19L13.5 10.5"
              stroke="#527B60"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
          <span className="font-editorial text-xl font-semibold tracking-tight text-[#294C38]">
            NutriScan AI
          </span>
        </button>

        {/* Zone 2: 5 Clean Single-Line Navigation Links */}
        <nav
          aria-label="Primary navigation"
          className="hidden md:flex items-center gap-7 text-sm font-medium"
        >
          {NAV_ITEMS.map((item) => {
            const active = activeSection === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                className={`relative py-1 whitespace-nowrap shrink-0 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#527B60] ${
                  active
                    ? 'text-[#294C38] font-semibold'
                    : 'text-[#758276] hover:text-[#25352B]'
                }`}
              >
                {item.label}
                {active && (
                  <span
                    aria-hidden="true"
                    className="absolute inset-x-0 -bottom-[19px] h-[2px] bg-[#527B60]"
                  />
                )}
              </button>
            );
          })}
        </nav>

        {/* Zone 3: 1 Primary Action Button (+ mobile menu toggle) */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={onStartScanning}
            className="hidden sm:inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors duration-150 whitespace-nowrap shrink-0 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#527B60]"
          >
            Start Scanning
          </button>

          <button
            type="button"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="md:hidden inline-flex items-center justify-center w-10 h-10 rounded-lg text-[#294C38] hover:bg-[#E8F0E5] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile navigation drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#DCE4D9] bg-[#FFFFFF] px-4 py-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = activeSection === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-[#DCEBDD] text-[#294C38] font-semibold'
                    : 'text-[#25352B] hover:bg-[#F3F7F0]'
                }`}
              >
                {item.label}
              </button>
            );
          })}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                onStartScanning();
              }}
              className="w-full px-4 py-2.5 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors"
            >
              Start Scanning
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
