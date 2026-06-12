import React from 'react';
import { Camera, BarChart2, CloudSun, MessageSquare, BookOpen, HelpCircle } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, cropCatalogInfo }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: BookOpen },
    { id: 'detect', label: 'Scan Leaf', icon: Camera },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
    { id: 'weather', label: 'Weather & Tips', icon: CloudSun },
    { id: 'chat', label: 'Farmer Chat', icon: MessageSquare },
  ];

  return (
    <>
      {/* Top Header/Desktop Nav */}
      <header className="sticky top-0 z-40 w-full border-b border-primary-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand Logo */}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveTab('home')}>
            <span className="text-2xl" role="img" aria-label="wheat">🌾</span>
            <div>
              <h1 className="font-serif text-xl font-bold leading-none text-primary-800">AgriSense</h1>
              <p className="text-[10px] font-sans font-medium tracking-wide text-slate-500 uppercase">Smart Agriculture</p>
            </div>
          </div>

          {/* Desktop Nav Items */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-primary-600 text-white shadow-sm shadow-primary-200'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Crop Count Badge */}
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline-flex items-center rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 ring-1 ring-inset ring-primary-600/20">
              <span className="mr-1.5 flex h-1.5 w-1.5 items-center justify-center rounded-full bg-primary-500 animate-pulse"></span>
              {cropCatalogInfo ? `${cropCatalogInfo.model_crops?.length || 13} Crops` : 'Loading crops...'}
            </span>
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 pb-safe shadow-lg shadow-black/10">
        <div className="flex items-center justify-around h-16 px-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center justify-center w-16 h-12 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'text-primary-700 font-bold'
                    : 'text-slate-400 font-medium'
                }`}
                style={{ minHeight: '48px' }} // Standard 48px touch target
              >
                <Icon className={`w-5 h-5 mb-0.5 transition-transform duration-200 ${isActive ? 'scale-110 text-primary-600' : ''}`} />
                <span className="text-[10px] tracking-tight">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </>
  );
}
