// WithMe Settings & Privacy Modal Component

import React, { useState, useEffect } from 'react';
import { memoryStore } from '../engine/memoryStore';
import { speechEngine } from '../engine/speechEngine';
import { X, Key, User, Shield, Volume2, Check, Radio } from 'lucide-react';

export default function SettingsModal({ userProfile, setUserProfile, onClose }) {
  const [settings, setSettings] = useState(memoryStore.getSettings());
  const [nameInput, setNameInput] = useState(userProfile.name);
  const [apiKeyInput, setApiKeyInput] = useState(settings.geminiApiKey);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);

  useEffect(() => {
    const voices = speechEngine.getVoices();
    setAvailableVoices(voices);
  }, []);

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
      <div className="glass-card w-full max-w-lg p-6 lg:p-8 relative border border-purple-500/30 overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-purple-400" />
            <span>Settings & Preferences</span>
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

          {/* Voice & Speech Synthesis Configuration */}
          <div className="space-y-3 pt-4 border-t border-white/10">
            <h3 className="text-sm font-semibold text-purple-300 flex items-center gap-2">
              <Volume2 className="w-4 h-4" /> Voice & Speech Preferences
            </h3>

            {/* Voice URI selection */}
            <div>
              <label className="text-xs text-gray-400 block mb-1">Companion Voice</label>
              <select
                value={settings.voiceURI || ''}
                onChange={(e) => setSettings({ ...settings, voiceURI: e.target.value })}
                className="w-full glass-input text-xs py-2 px-3 rounded-xl bg-slate-900 text-white"
              >
                <option value="">Auto Selected (Default)</option>
                {availableVoices.map((v) => (
                  <option key={v.voiceURI} value={v.voiceURI}>
                    {v.name} ({v.lang})
                  </option>
                ))}
              </select>
            </div>

            {/* Voice Pitch */}
            <div>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>Voice Pitch</span>
                <span className="text-purple-300 font-mono">{(settings.voicePitch ?? 1.1).toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="1.8"
                step="0.1"
                value={settings.voicePitch ?? 1.1}
                onChange={(e) => setSettings({ ...settings, voicePitch: parseFloat(e.target.value) })}
                className="w-full accent-purple-500 cursor-pointer"
              />
            </div>

            {/* Voice Speed */}
            <div>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>Speech Speed</span>
                <span className="text-purple-300 font-mono">{(settings.voiceRate ?? 1.0).toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.6"
                step="0.1"
                value={settings.voiceRate ?? 1.0}
                onChange={(e) => setSettings({ ...settings, voiceRate: parseFloat(e.target.value) })}
                className="w-full accent-purple-500 cursor-pointer"
              />
            </div>

            {/* Auto Read Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
              <span className="text-xs text-gray-300">Auto Read Out Loud Responses</span>
              <input
                type="checkbox"
                checked={settings.autoSpeechEnabled ?? false}
                onChange={(e) => setSettings({ ...settings, autoSpeechEnabled: e.target.checked })}
                className="w-4 h-4 accent-purple-500 rounded cursor-pointer"
              />
            </div>

            {/* Hands Free Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-pink-400" />
                <span className="text-xs text-gray-300">Default Hands-Free Walkie-Talkie Mode</span>
              </div>
              <input
                type="checkbox"
                checked={settings.handsFreeMode ?? false}
                onChange={(e) => setSettings({ ...settings, handsFreeMode: e.target.checked })}
                className="w-4 h-4 accent-pink-500 rounded cursor-pointer"
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
