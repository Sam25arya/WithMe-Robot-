// WithMe Settings & Privacy Modal Component

import React, { useState } from 'react';
import { memoryStore } from '../engine/memoryStore';
import { X, Key, User, Shield, Volume2, Cpu, Check, Trash2 } from 'lucide-react';

export default function SettingsModal({ userProfile, setUserProfile, onClose }) {
  const [settings, setSettings] = useState(memoryStore.getSettings());
  const [nameInput, setNameInput] = useState(userProfile.name);
  const [apiKeyInput, setApiKeyInput] = useState(settings.geminiApiKey);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();

    // Update Profile
    const updatedProfile = { ...userProfile, name: nameInput, preferredCallName: nameInput };
    memoryStore.setUserProfile(updatedProfile);
    setUserProfile(updatedProfile);

    // Update Settings
    const updatedSettings = { ...settings, geminiApiKey: apiKeyInput };
    memoryStore.setSettings(updatedSettings);
    setSettings(updatedSettings);

    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card w-full max-w-lg p-6 lg:p-8 relative border border-purple-500/30 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-purple-400" />
            <span>Settings & Privacy</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-6">
          {/* User Profile Section */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-purple-300 flex items-center gap-2">
              <User className="w-4 h-4" /> User Persona
            </h3>
            <div>
              <label className="text-xs text-gray-400 block mb-1">What should WithMe call you?</label>
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                className="glass-input w-full text-sm"
                placeholder="Your name"
                required
              />
            </div>
          </div>

          {/* AI Engine & API Key Configuration */}
          <div className="space-y-3 pt-4 border-t border-white/10">
            <h3 className="text-sm font-semibold text-purple-300 flex items-center gap-2">
              <Key className="w-4 h-4" /> Low-Cost Hybrid AI Engine
            </h3>

            <div>
              <label className="text-xs text-gray-400 block mb-1">Google Gemini 1.5 Flash API Key (Optional)</label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="AIzaSy..."
                className="glass-input w-full text-sm font-mono"
              />
              <p className="text-[11px] text-gray-500 mt-1">
                Leave blank to use the built-in smart local friendship engine (100% free, zero API cost).
              </p>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
              <span className="text-xs text-gray-300">Force Smart Local Engine (Zero API Cost)</span>
              <input
                type="checkbox"
                checked={settings.useLocalFallbackOnly}
                onChange={(e) => setSettings({ ...settings, useLocalFallbackOnly: e.target.checked })}
                className="w-4 h-4 accent-purple-500 rounded cursor-pointer"
              />
            </div>
          </div>

          {/* Save Action */}
          <div className="flex items-center justify-between pt-4 border-t border-white/10">
            {savedSuccess ? (
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <Check className="w-4 h-4" /> Settings Saved!
              </span>
            ) : <div />}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary py-2 px-4 text-xs"
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary py-2 px-5 text-xs">
                Save Preferences
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
