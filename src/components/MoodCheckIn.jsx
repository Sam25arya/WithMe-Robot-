// WithMe Mood Check-In Component

import React from 'react';
import { MOODS } from '../engine/moodThemeEngine';
import { X, Sparkles, HeartHandshake } from 'lucide-react';

export default function MoodCheckIn({ currentMoodId, onSelectMood, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="glass-card w-full max-w-lg p-6 lg:p-8 relative overflow-hidden border border-purple-500/30">
        {/* Ambient Top Glow */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
        
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300">
              <HeartHandshake className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                How are you feeling right now?
              </h2>
              <p className="text-xs text-gray-400">WithMe will adapt its conversation & mood lighting for you</p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* 7 Emotional Mood Options */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
          {MOODS.map((m) => {
            const isSelected = currentMoodId === m.id;
            return (
              <button
                key={m.id}
                onClick={() => {
                  onSelectMood(m.id);
                  if (onClose) onClose();
                }}
                className={`flex flex-col items-center justify-center p-4 rounded-2xl border transition-all duration-200 group ${
                  isSelected
                    ? 'bg-purple-600/30 border-purple-400 shadow-lg shadow-purple-500/20 scale-105'
                    : 'bg-slate-900/50 border-white/10 hover:bg-white/10 hover:border-white/20'
                }`}
              >
                <span className="text-3xl mb-2 transition-transform duration-200 group-hover:scale-125">
                  {m.emoji}
                </span>
                <span className={`text-sm font-semibold ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                  {m.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Footnote Encouragement */}
        <div className="p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/20 flex items-center gap-3 text-xs text-purple-200">
          <Sparkles className="w-4 h-4 text-purple-400 shrink-0" />
          <span>No pressure, no judgement. You can change your mood setting whenever you like.</span>
        </div>
      </div>
    </div>
  );
}
