// WithMe R&D Ghost Robot Hardware & Interactive Lab (Ghosti & Tiny Companion)

import React, { useState } from 'react';
import CompanionAvatar from './CompanionAvatar';
import confetti from 'canvas-confetti';
import { memoryStore } from '../engine/memoryStore';
import { Cpu, Eye, Activity, Sparkles, Heart, Music, Waves, Moon, Palette, Move, Shirt, Zap, Check } from 'lucide-react';

export default function RobotLab() {
  const [appSettings, setAppSettings] = useState(() => memoryStore.getSettings());
  const [ghostEmotion, setGhostEmotion] = useState('happy');
  const [customEyeColor, setCustomEyeColor] = useState('#38bdf8');
  const [accessorySkin, setAccessorySkin] = useState(appSettings.accessorySkin || 'headphones');
  const [auraSkin, setAuraSkin] = useState(appSettings.auraSkin || 'cyber');
  const [savedSkinSuccess, setSavedSkinSuccess] = useState(false);

  const [isDancing, setIsDancing] = useState(false);
  const [isWaving, setIsWaving] = useState(false);
  const [isSleeping, setIsSleeping] = useState(false);
  const [isFollowing, setIsFollowing] = useState(false);

  const [activeLog, setActiveLog] = useState([
    "10:08:12 [Ghosti Core] Main ghost & Tiny companion synced.",
    "10:08:14 [Vision] Person detected. Pupil gaze tracking aligned.",
    "10:08:15 [Companion Sync] Tiny companion mirroring emotional state: Happy."
  ]);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setActiveLog((prev) => [`${time} ${msg}`, ...prev.slice(0, 15)]);
  };

  // Preset Emotions
  const emotionsList = [
    { id: 'happy', label: 'Happy', emoji: '😊', desc: 'Curved eyes & smile' },
    { id: 'curious', label: 'Curious', emoji: '❓', desc: 'Attentive gaze' },
    { id: 'loving', label: 'Loving', emoji: '💖', desc: 'Pink heart eyes' },
    { id: 'sad', label: 'Sad', emoji: '😢', desc: 'Teary eyes & soft glow' },
    { id: 'excited', label: 'Excited', emoji: '⭐', desc: 'Golden star eyes' },
    { id: 'sleepy', label: 'Sleepy', emoji: '😴', desc: 'Closed eyes & Zzz' }
  ];

  // Eye Colors
  const eyeColors = [
    { name: 'Cyan Glow', hex: '#38bdf8' },
    { name: 'Neon Pink', hex: '#f472b6' },
    { name: 'Golden Star', hex: '#fbbf24' },
    { name: 'Emerald', hex: '#34d399' },
    { name: 'Violet Glow', hex: '#c084fc' }
  ];

  // Accessories List
  const accessoryList = [
    { id: 'headphones', label: 'Headphones', icon: '🎧' },
    { id: 'wizard', label: 'Wizard Hat', icon: '🧙‍♂️' },
    { id: 'crown', label: 'Royal Crown', icon: '👑' },
    { id: 'catears', label: 'Cat Ears', icon: '🐱' },
    { id: 'halo', label: 'Angel Halo', icon: '😇' },
    { id: 'sunglasses', label: 'Cool Shades', icon: '🕶️' },
    { id: 'flower', label: 'Blossom', icon: '🌸' }
  ];

  // Aura List
  const auraList = [
    { id: 'cyber', label: 'Cyber Cyan', icon: '⚡' },
    { id: 'stardust', label: 'Stardust', icon: '✨' },
    { id: 'galaxy', label: 'Galaxy', icon: '🌌' },
    { id: 'hearts', label: 'Pink Hearts', icon: '💖' },
    { id: 'none', label: 'Minimal', icon: '🚫' }
  ];

  // Save Skin Preferences Globally
  const handleSaveSkin = () => {
    const updated = { ...appSettings, accessorySkin, auraSkin };
    memoryStore.setSettings(updated);
    setAppSettings(updated);
    setSavedSkinSuccess(true);
    confetti({ particleCount: 50, spread: 60 });
    addLog(`[Customizer] Saved global companion skin: ${accessorySkin.toUpperCase()} + ${auraSkin.toUpperCase()} aura!`);
    setTimeout(() => setSavedSkinSuccess(false), 2000);
  };

  // Action Triggers
  const handleDance = () => {
    setIsDancing(true);
    setIsWaving(false);
    setIsSleeping(false);
    setGhostEmotion('happy');
    addLog("[Action] Ghosti & Tiny companion dancing to music 🎵");
    confetti({ particleCount: 40, spread: 50 });
    setTimeout(() => setIsDancing(false), 4000);
  };

  const handleWave = () => {
    setIsWaving(true);
    setIsDancing(false);
    setIsSleeping(false);
    setGhostEmotion('happy');
    addLog("[Action] Ghosti waving arm stub 👋");
    setTimeout(() => setIsWaving(false), 3000);
  };

  const handleExcited = () => {
    setGhostEmotion('excited');
    setIsDancing(false);
    setIsWaving(false);
    setIsSleeping(false);
    addLog("[Action] Star eyes activated! Ghosti & Tiny companion excited ⭐");
    confetti({ particleCount: 60, spread: 70 });
  };

  const handleSleep = () => {
    setIsSleeping(true);
    setGhostEmotion('sleepy');
    setIsDancing(false);
    setIsWaving(false);
    addLog("[Action] Ghosti & Tiny companion sleeping together 💤");
  };

  const handleFollow = () => {
    setIsFollowing(true);
    addLog("[Tracking] Floating follow trajectory active. Tracking user distance.");
    setTimeout(() => setIsFollowing(false), 3500);
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="glass-card p-6 border border-purple-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-500/30">
            <Cpu className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                Ghosti ♡ <span className="text-xs text-purple-300 font-normal">Physical Companion R&D</span>
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30">
                Dual Companion System
              </span>
            </div>
            <p className="text-xs text-gray-400">Smart ghost robot with a tiny companion that always follows you and mirrors your emotions</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-purple-300 bg-purple-950/50 px-3.5 py-1.5 rounded-xl border border-purple-500/30">
          <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>Same Emotions, Always Together</span>
        </div>
      </div>

      {/* Main Interactive Stage & Customizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Ghosti Interactive Viewport Stage */}
        <div className="lg:col-span-7 glass-card p-6 sm:p-8 border border-white/10 flex flex-col items-center justify-between space-y-6 relative overflow-hidden">
          <div className="w-full flex items-center justify-between text-xs text-gray-400 border-b border-white/10 pb-3">
            <span className="flex items-center gap-1.5 font-semibold text-purple-300">
              <Eye className="w-4 h-4" /> Dual Companion Stage Preview
            </span>
            <span className="text-pink-400 font-medium">State: {ghostEmotion.toUpperCase()}</span>
          </div>

          {/* Interactive Ghost Avatar Stage */}
          <div className={`py-8 transition-transform duration-500 ${isFollowing ? 'translate-x-6' : ''}`}>
            <CompanionAvatar
              emotionState={ghostEmotion}
              size="lg"
              showTinyCompanion={true}
              customEyeColor={customEyeColor}
              accessorySkin={accessorySkin}
              auraSkin={auraSkin}
              isDancing={isDancing}
              isWaving={isWaving}
              isSleeping={isSleeping}
            />
          </div>

          {/* Eye Color Customizer */}
          <div className="w-full p-4 rounded-2xl bg-slate-950/70 border border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                <Palette className="w-4 h-4 text-purple-400" /> Customizable Eye Colors & Glow
              </span>
            </div>
            <div className="flex items-center gap-2 pt-1">
              {eyeColors.map((c) => (
                <button
                  key={c.hex}
                  onClick={() => {
                    setCustomEyeColor(c.hex);
                    addLog(`[Customizer] Eye color changed to ${c.name}`);
                  }}
                  className={`w-7 h-7 rounded-full transition-transform hover:scale-110 ${
                    customEyeColor === c.hex ? 'ring-2 ring-white ring-offset-2 ring-offset-slate-950 scale-110' : ''
                  }`}
                  style={{ backgroundColor: c.hex, boxShadow: `0 0 10px ${c.hex}` }}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right: Customization & Emotion Controls */}
        <div className="lg:col-span-5 space-y-5">
          {/* ACCESSORY HATS & SKINS SELECTOR */}
          <div className="glass-card p-5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Shirt className="w-4 h-4 text-purple-400" /> Head Accessories & Hats
              </h3>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {accessoryList.map((acc) => (
                <button
                  key={acc.id}
                  onClick={() => {
                    setAccessorySkin(acc.id);
                    addLog(`[Outfit] Equipped accessory: ${acc.label}`);
                  }}
                  className={`p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-1 ${
                    accessorySkin === acc.id
                      ? 'bg-purple-600/30 border-purple-400 text-white shadow-md shadow-purple-500/20'
                      : 'bg-slate-900/50 border-white/5 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <span className="text-lg">{acc.icon}</span>
                  <span className="text-[10px] font-semibold">{acc.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* AURA GLOW SKINS */}
          <div className="glass-card p-5 border border-white/10 space-y-3">
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-cyan-400" /> Body Aura & FX Glow
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {auraList.map((aura) => (
                <button
                  key={aura.id}
                  onClick={() => {
                    setAuraSkin(aura.id);
                    addLog(`[Aura] Changed body aura effect: ${aura.label}`);
                  }}
                  className={`p-2 rounded-xl border text-center transition-all flex items-center justify-center gap-1.5 ${
                    auraSkin === aura.id
                      ? 'bg-cyan-600/30 border-cyan-400 text-white shadow-md shadow-cyan-500/20'
                      : 'bg-slate-900/50 border-white/5 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <span className="text-sm">{aura.icon}</span>
                  <span className="text-xs font-semibold">{aura.label}</span>
                </button>
              ))}
            </div>

            {/* Save Active Companion Look Button */}
            <button
              onClick={handleSaveSkin}
              className="w-full btn-primary py-2.5 text-xs flex items-center justify-center gap-1.5 mt-2"
            >
              {savedSkinSuccess ? (
                <>
                  <Check className="w-4 h-4 text-emerald-400" />
                  <span>Companion Look Saved Across App!</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-yellow-300" />
                  <span>Set as Active Companion Outfit</span>
                </>
              )}
            </button>
          </div>

          {/* Emotion Matrix Selector */}
          <div className="glass-card p-5 border border-white/10 space-y-3">
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Heart className="w-4 h-4 text-pink-400" /> Expressive Emotions
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {emotionsList.map((e) => (
                <button
                  key={e.id}
                  onClick={() => {
                    setGhostEmotion(e.id);
                    setIsSleeping(e.id === 'sleepy');
                    setIsDancing(false);
                    setIsWaving(false);
                    addLog(`[Emotion] Ghosti & Tiny companion set to ${e.label}`);
                  }}
                  className={`p-2.5 rounded-xl border text-center transition-all ${
                    ghostEmotion === e.id
                      ? 'bg-purple-600/30 border-purple-400 text-white shadow-md shadow-purple-500/20'
                      : 'bg-slate-900/50 border-white/5 text-gray-300 hover:bg-white/5'
                  }`}
                >
                  <span className="text-xl block mb-0.5">{e.emoji}</span>
                  <span className="text-xs font-semibold">{e.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="glass-card p-5 border border-white/10 space-y-3">
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-purple-400" /> Interactive Actions
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button onClick={handleFollow} className="btn-secondary p-3 flex flex-col items-center gap-1 text-center">
                <Move className="w-4 h-4 text-cyan-400" />
                <span>Follows You</span>
              </button>

              <button onClick={handleDance} className="btn-secondary p-3 flex flex-col items-center gap-1 text-center">
                <Music className="w-4 h-4 text-pink-400" />
                <span>Dances to Music</span>
              </button>

              <button onClick={handleWave} className="btn-secondary p-3 flex flex-col items-center gap-1 text-center">
                <Waves className="w-4 h-4 text-emerald-400" />
                <span>Waves Hello</span>
              </button>

              <button onClick={handleExcited} className="btn-secondary p-3 flex flex-col items-center gap-1 text-center">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Gets Excited</span>
              </button>
            </div>

            <button
              onClick={handleSleep}
              className="w-full btn-secondary p-2.5 flex items-center justify-center gap-2 text-xs mt-1 text-indigo-300 border-indigo-500/30"
            >
              <Moon className="w-4 h-4 text-indigo-400" />
              <span>Sleeps Together (Main & Tiny Ghost)</span>
            </button>
          </div>

          {/* Realtime Telemetry Log */}
          <div className="glass-card p-4 border border-white/10 space-y-2">
            <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">HRI Telemetry & Companion Log</h3>
            <div className="p-3 rounded-xl bg-slate-950 font-mono text-[11px] text-gray-300 space-y-1 h-28 overflow-y-auto border border-white/5">
              {activeLog.map((log, i) => (
                <div key={i} className="leading-snug">{log}</div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
