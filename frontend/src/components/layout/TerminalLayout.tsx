import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { HealthResponse, MarketStatusItem, NavTabId } from '../../types/market';
import { WelcomeOnboardingModal } from '../common/WelcomeOnboardingModal';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { ShieldCheck, AlertCircle } from 'lucide-react';

interface TerminalLayoutProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  marketStatuses: MarketStatusItem[];
  onRefresh: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  pendingProposalsCount?: number;
  onOpenSearch?: () => void;
  unreadAlertsCount?: number;
  children: React.ReactNode;
}

export const TerminalLayout: React.FC<TerminalLayoutProps> = ({
  activeTab,
  onTabChange,
  health,
  healthLoading,
  marketStatuses,
  onRefresh,
  searchQuery,
  onSearchChange,
  pendingProposalsCount,
  onOpenSearch,
  unreadAlertsCount = 0,
  children,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [welcomeModalOpen, setWelcomeModalOpen] = useState<boolean>(() => {
    return !localStorage.getItem('vibe_onboarding_dismissed');
  });

  const handleStartPaperTradingFromModal = () => {
    setWelcomeModalOpen(false);
    onTabChange('paper_trading');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden terminal-mesh-bg text-slate-100 font-sans relative">
      {/* Ambient background micro-grid overlay */}
      <div className="absolute inset-0 terminal-grid-overlay opacity-25 pointer-events-none z-0" />

      {/* Mobile Drawer Overlay */}
      {mobileSidebarOpen && (
        <div
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar Navigation (Desktop + Mobile responsive drawer) */}
      <div
        className={`fixed md:static inset-y-0 left-0 z-50 transition-transform duration-300 md:translate-x-0 ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar
          activeTab={activeTab}
          onTabChange={(tab) => {
            onTabChange(tab);
            setMobileSidebarOpen(false);
          }}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          pendingProposalsCount={pendingProposalsCount}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        {/* Top Header */}
        <Header
          health={health}
          healthLoading={healthLoading}
          marketStatuses={marketStatuses}
          onRefresh={onRefresh}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
          onOpenHelp={() => setWelcomeModalOpen(true)}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          onOpenSearch={onOpenSearch}
          onNavigateTab={onTabChange}
          unreadAlertsCount={unreadAlertsCount}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-5 md:p-6 space-y-6">
          <ErrorBoundary fallbackTitle="View Display Error">
            {children}
          </ErrorBoundary>
        </main>

        {/* Persistent Bottom Simulation Ticker Banner */}
        <footer className="h-7 bg-[#070A12]/95 border-t border-white/[0.06] px-4 flex items-center justify-between text-[10px] font-mono text-slate-400 select-none shrink-0 z-20 overflow-x-auto whitespace-nowrap">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-amber-400 font-bold">
              <ShieldCheck className="w-3 h-3" />
              PAPER TRADING — NO REAL MONEY
            </span>
            <span className="text-slate-600">•</span>
            <span>DATA SOURCE: <span className="text-slate-300">DEMO / HISTORICAL</span></span>
            <span className="text-slate-600">•</span>
            <span>BROKER: <span className="text-slate-300">NOT CONNECTED (READ-ONLY)</span></span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-rose-400 font-bold">LIVE BROKER ORDERS: DISABLED</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-500">v0.1.0-release</span>
          </div>
        </footer>
      </div>

      {/* Welcome / Onboarding Modal */}
      <WelcomeOnboardingModal
        isOpen={welcomeModalOpen}
        onClose={() => setWelcomeModalOpen(false)}
        onStartPaperTrading={handleStartPaperTradingFromModal}
      />
    </div>
  );
};
