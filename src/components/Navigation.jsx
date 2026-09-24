// WithMe Header Navigation Component

import React from 'react';
import { MessageSquare, Brain, Gamepad2, Bell, Cpu, Settings, Heart, Smile } from 'lucide-react';
import { getMoodById } from '../engine/moodThemeEngine';

export default function Navigation({
  activeTab,
  setActiveTab,
  currentMoodId,
  onOpenMoodModal,
  onOpenSettings,
  userProfile
}) {
  const mood = getMoodById(currentMoodId);

  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'memory', label: 'Memory Vault', icon: Brain },
    { id: 'games', label: 'AI Games', icon: Gamepad2 },
    { id: 'reminders', label: 'Reminders', icon: Bell },
    { id: 'robotLab', label: 'Robot Lab (R&D)', icon: Cpu }
  ];

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-slate-950/70 border-b border-white/10 px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand Logo & Companion Heart */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('chat')}>
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-pink-500 shadow-lg shadow-purple-500/30">
            <Heart className="w-5 h-5 text-white animate-pulse" fill="white" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gradient flex items-center gap-1.5">
              WithMe
            </h1>
            <p className="text-[10px] text-gray-400 font-medium tracking-wide uppercase">AI Emotional Companion</p>
          </div>
        </div>

        {/* Center Desktop Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1.5 bg-slate-900/60 p-1.5 rounded-2xl border border-white/10">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600/90 to-indigo-600/90 text-white shadow-md shadow-purple-500/20'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Action Bar: Mood Pill & Settings */}
        <div className="flex items-center gap-2.5">
          {/* Active Mood Selector Button */}
          <button
            onClick={onOpenMoodModal}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-xs font-medium text-gray-200 shadow-sm"
            title="Update how you are feeling"
          >
            <span className="text-base">{mood.emoji}</span>
            <span className="hidden sm:inline font-semibold">{mood.label}</span>
            <Smile className="w-3.5 h-3.5 text-purple-400 opacity-70" />
          </button>

          {/* User Profile / Settings Button */}
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-gray-300 hover:text-white"
            title="Settings & Privacy"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Mobile Navigation Row */}
      <div className="md:hidden flex items-center justify-around mt-3 pt-2.5 border-t border-white/10">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg text-[11px] font-medium transition-all ${
                isActive ? 'text-purple-400 font-semibold' : 'text-gray-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label.split(' ')[0]}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
