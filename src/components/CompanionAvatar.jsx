// WithMe Expressive Ghost Companion Avatar Component (Ghosti & Tiny Companion)
// High-Fidelity Interactive Edition: Gestures, Audio Synthesis, Expressions & Petting Support

import React, { useState, useEffect, useRef } from 'react';

export default function CompanionAvatar({
  emotionState = 'happy',
  isSpeaking = false,
  size = 'md',
  showTinyCompanion = true,
  customEyeColor = null,
  isDancing = false,
  isWaving = false,
  isSleeping = false,
  onInteract = null, // Optional callback when user taps avatar
  enableControls = true, // Whether to show hover/tap action toolbar
  accessorySkin = 'headphones', // 'headphones' | 'wizard' | 'crown' | 'catears' | 'halo' | 'sunglasses' | 'flower'
  auraSkin = 'cyber' // 'none' | 'cyber' | 'stardust' | 'galaxy' | 'hearts'
}) {
  // Gaze & Animation States
  const [pupilPos, setPupilPos] = useState({ x: 0, y: 0 });
  const [isBlinking, setIsBlinking] = useState(false);
  const [isSquishing, setIsSquishing] = useState(false);
  const [isSpinning, setIsSpinning] = useState(false);
  const [isBlushing, setIsBlushing] = useState(false);
  const [activeEyeOverride, setActiveEyeOverride] = useState(null); // 'winking' | 'surprised' | 'heart'
  
  // Interactive Floating Elements & Speech Bubble
  const [floatingParticles, setFloatingParticles] = useState([]);
  const [speechBubble, setSpeechBubble] = useState(null);
  const [showQuickToolbar, setShowQuickToolbar] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  // Local Animation Triggers
  const [localDancing, setLocalDancing] = useState(false);
  const [localWaving, setLocalWaving] = useState(false);
  const [localSleeping, setLocalSleeping] = useState(false);

  // Petting Gesture Tracking
  const petCounterRef = useRef(0);
  const speechTimeoutRef = useRef(null);
  const audioCtxRef = useRef(null);

  // Combine Props with Local Overrides
  const currentDancing = isDancing || localDancing;
  const currentWaving = isWaving || localWaving;
  const currentSleeping = isSleeping || localSleeping;

  // Web Audio API Cute Sound Synthesizer
  const playAudioEffect = (type) => {
    if (isMuted) return;
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) audioCtxRef.current = new AudioCtx();
      }
      const ctx = audioCtxRef.current;
      if (!ctx) return;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'boop') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(520, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
        osc.start(now);
        osc.stop(now + 0.12);
      } else if (type === 'giggle') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(600, now);
        osc.frequency.setValueAtTime(800, now + 0.08);
        osc.frequency.setValueAtTime(1050, now + 0.16);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'highfive') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(784, now);
        osc.frequency.setValueAtTime(1046.5, now + 0.1);
        gain.gain.setValueAtTime(0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'dance') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.setValueAtTime(554, now + 0.07);
        osc.frequency.setValueAtTime(659, now + 0.14);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.28);
        osc.start(now);
        osc.stop(now + 0.28);
      }
    } catch {
      // Audio fallback silent
    }
  };

  // Mouse Gaze Tracking Across Window
  useEffect(() => {
    const handleMouseMove = (e) => {
      const cx = window.innerWidth / 2;
      const cy = window.innerHeight / 3;
      const dx = (e.clientX - cx) / cx;
      const dy = (e.clientY - cy) / cy;
      setPupilPos({ x: dx * 5, y: dy * 3 });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Eyelid Blink Interval
  useEffect(() => {
    if (currentSleeping || emotionState === 'sleepy') return;
    const interval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 220);
    }, 4200);
    return () => clearInterval(interval);
  }, [currentSleeping, emotionState]);

  // Dimension scaling
  const dimensions = {
    sm: { mainW: 75, mainH: 80, tinyW: 38, tinyH: 40 },
    md: { mainW: 135, mainH: 145, tinyW: 68, tinyH: 74 },
    lg: { mainW: 210, mainH: 225, tinyW: 100, tinyH: 108 }
  }[size] || { mainW: 135, mainH: 145, tinyW: 68, tinyH: 74 };

  // Helper: Show Temporary Speech Bubble
  const triggerSpeech = (text, duration = 3000) => {
    if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current);
    setSpeechBubble(text);
    speechTimeoutRef.current = setTimeout(() => {
      setSpeechBubble(null);
    }, duration);
  };

  // Helper: Spawn Floating Emoji Particle FX
  const spawnParticle = (emoji, posX = 50, posY = 20) => {
    const newId = Date.now() + Math.random();
    setFloatingParticles((prev) => [
      ...prev.slice(-6),
      { id: newId, emoji, x: posX + (Math.random() * 20 - 10), y: posY }
    ]);
    setTimeout(() => {
      setFloatingParticles((prev) => prev.filter((p) => p.id !== newId));
    }, 1000);
  };

  // Click / Poke Reaction Handler
  const handlePoke = (e) => {
    e.stopPropagation();
    setIsSquishing(true);
    setIsBlushing(true);
    playAudioEffect('boop');

    const reactions = [
      { text: "Boop! Hi friend! ✨", emoji: "✨", eye: "winking" },
      { text: "Hehe! That tickles! 🖐️", emoji: "🖐️", eye: "heart" },
      { text: "I'm right here with you! 💖", emoji: "💖", eye: "heart" },
      { text: "Ready for anything! 🚀", emoji: "🚀", eye: "star" },
      { text: "High five! 🖐️", emoji: "🖐️", eye: "winking" }
    ];
    const pick = reactions[Math.floor(Math.random() * reactions.length)];
    
    triggerSpeech(pick.text);
    spawnParticle(pick.emoji, 45, 10);
    setActiveEyeOverride(pick.eye);

    setTimeout(() => {
      setIsSquishing(false);
      setIsBlushing(false);
      setActiveEyeOverride(null);
    }, 800);

    if (onInteract) onInteract('poke');
  };

  // Double Click Spin Handler
  const handleDoubleClick = (e) => {
    e.stopPropagation();
    setIsSpinning(true);
    playAudioEffect('giggle');
    triggerSpeech("Wheee 360 spin! 🎉");
    spawnParticle("🎉", 50, 0);
    setActiveEyeOverride("star");

    setTimeout(() => {
      setIsSpinning(false);
      setActiveEyeOverride(null);
    }, 700);
  };

  // Petting Gesture
  const handleMouseMoveOver = () => {
    petCounterRef.current += 1;
    if (petCounterRef.current > 15) {
      petCounterRef.current = 0;
      setIsBlushing(true);
      playAudioEffect('giggle');
      spawnParticle("💖", 40 + Math.random() * 20, 20);
      triggerSpeech("Mmm... loving the pets! 🥰", 2500);
      setActiveEyeOverride('heart');
      setTimeout(() => {
        setIsBlushing(false);
        setActiveEyeOverride(null);
      }, 1500);
    }
  };

  // Quick Action Toolbar Trigger
  const handleQuickAction = (action) => {
    switch (action) {
      case 'highfive':
        setLocalWaving(true);
        playAudioEffect('highfive');
        triggerSpeech("High five! We make a great team! 🖐️");
        spawnParticle("🖐️", 50, 10);
        setTimeout(() => setLocalWaving(false), 2500);
        break;

      case 'dance':
        setLocalDancing(true);
        playAudioEffect('dance');
        triggerSpeech("Party time! Let's dance! 🎵");
        spawnParticle("🎵", 60, 10);
        spawnParticle("🎶", 30, 20);
        setTimeout(() => setLocalDancing(false), 3500);
        break;

      case 'pet':
        setIsBlushing(true);
        setActiveEyeOverride('heart');
        playAudioEffect('giggle');
        triggerSpeech("Warm hugs & pets! 🥰");
        spawnParticle("💖", 50, 10);
        setTimeout(() => {
          setIsBlushing(false);
          setActiveEyeOverride(null);
        }, 3000);
        break;

      case 'nap':
        setLocalSleeping(!localSleeping);
        if (!localSleeping) {
          triggerSpeech("Nap time... Zzz 💤");
          spawnParticle("💤", 55, 10);
        } else {
          triggerSpeech("Wide awake and refreshed! ☀️");
          spawnParticle("☀️", 55, 10);
        }
        break;

      default:
        break;
    }
  };

  // Determine Eye Render Details & Colors
  const getEyeDetails = (emotion) => {
    if (activeEyeOverride) {
      if (activeEyeOverride === 'winking') return { mode: 'winking', color: '#38bdf8' };
      if (activeEyeOverride === 'surprised') return { mode: 'surprised', color: '#fbbf24' };
      if (activeEyeOverride === 'heart') return { mode: 'heart', color: '#f472b6' };
      if (activeEyeOverride === 'star') return { mode: 'star', color: '#fbbf24' };
    }

    let mode = 'normal';
    let color = customEyeColor || '#38bdf8';

    switch (emotion) {
      case 'loving':
        mode = 'heart';
        color = '#f472b6';
        break;
      case 'excited':
      case 'playful':
        mode = 'star';
        color = '#fbbf24';
        break;
      case 'sad':
      case 'caring':
        mode = 'sad';
        color = '#38bdf8';
        break;
      case 'sleepy':
        mode = 'sleepy';
        color = '#38bdf8';
        break;
      case 'happy':
        mode = 'happy_arc';
        color = customEyeColor || '#38bdf8';
        break;
      default:
        mode = 'normal';
        color = customEyeColor || '#38bdf8';
    }
    return { mode, color };
  };

  const { mode: mainEyeMode, color: mainEyeColor } = getEyeDetails(emotionState);

  // Render Core Ghost SVG
  const renderGhostSVG = (w, h, isTiny = false) => {
    const eyeColor = mainEyeColor;

    return (
      <svg width={w} height={h} viewBox="0 0 130 140" className="overflow-visible drop-shadow-2xl">
        <defs>
          <linearGradient id={`ghostGrad-${isTiny ? 'tiny' : 'main'}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="70%" stopColor="#f1f5f9" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>

          <linearGradient id="headphoneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a855f7" />
            <stop offset="100%" stopColor="#7e22ce" />
          </linearGradient>

          <filter id={`eyeGlow-${isTiny ? 't' : 'm'}`} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="blushGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" />
          </filter>
        </defs>

        {/* ACCESSORY SKIN: HEADPHONES */}
        {(accessorySkin === 'headphones' || isTiny) && (
          <>
            <path
              d="M 22 55 A 44 44 0 0 1 108 55"
              fill="none"
              stroke="url(#headphoneGrad)"
              strokeWidth={isTiny ? "6" : "10"}
              strokeLinecap="round"
            />
            {!isTiny ? (
              <>
                <g transform="translate(14, 45)">
                  <rect x="0" y="0" width="14" height="28" rx="7" fill="url(#headphoneGrad)" />
                  <circle cx="7" cy="14" r="4" fill="none" stroke="#38bdf8" strokeWidth="2" />
                </g>
                <g transform="translate(102, 45)">
                  <rect x="0" y="0" width="14" height="28" rx="7" fill="url(#headphoneGrad)" />
                  <circle cx="7" cy="14" r="4" fill="none" stroke="#38bdf8" strokeWidth="2" />
                </g>
              </>
            ) : (
              <>
                <rect x="18" y="44" width="8" height="18" rx="4" fill="url(#headphoneGrad)" />
                <rect x="104" y="44" width="8" height="18" rx="4" fill="url(#headphoneGrad)" />
              </>
            )}
          </>
        )}

        {/* ACCESSORY SKIN: WIZARD HAT */}
        {!isTiny && accessorySkin === 'wizard' && (
          <g transform="translate(0, -5)">
            <polygon points="65,2 35,36 95,36" fill="#6d28d9" stroke="#a855f7" strokeWidth="1.5" />
            <ellipse cx="65" cy="36" rx="36" ry="6" fill="#581c87" stroke="#9333ea" strokeWidth="1" />
            <path d="M 65 14 L 67 19 L 72 19 L 68 22 L 70 27 L 65 24 L 60 27 L 62 22 L 58 19 L 63 19 Z" fill="#fbbf24" />
          </g>
        )}

        {/* ACCESSORY SKIN: ROYAL CROWN */}
        {!isTiny && accessorySkin === 'crown' && (
          <g transform="translate(0, 0)">
            <path d="M 38,30 L 35,8 L 50,20 L 65,4 L 80,20 L 95,8 L 92,30 Z" fill="#fbbf24" stroke="#f59e0b" strokeWidth="1.5" />
            <ellipse cx="65" cy="30" rx="27" ry="4" fill="#d97706" />
            <circle cx="35" cy="8" r="3" fill="#ef4444" />
            <circle cx="65" cy="4" r="3.5" fill="#3b82f6" />
            <circle cx="95" cy="8" r="3" fill="#ef4444" />
            <circle cx="50" cy="20" r="2" fill="#10b981" />
            <circle cx="80" cy="20" r="2" fill="#10b981" />
          </g>
        )}

        {/* ACCESSORY SKIN: CAT EARS */}
        {!isTiny && accessorySkin === 'catears' && (
          <g>
            <polygon points="32,32 18,6 46,24" fill="#ec4899" stroke="#f472b6" strokeWidth="1.5" />
            <polygon points="34,30 24,12 43,24" fill="#fbcfe8" />
            <polygon points="98,32 112,6 84,24" fill="#ec4899" stroke="#f472b6" strokeWidth="1.5" />
            <polygon points="96,30 106,12 87,24" fill="#fbcfe8" />
          </g>
        )}

        {/* ACCESSORY SKIN: HALO */}
        {!isTiny && accessorySkin === 'halo' && (
          <g transform="translate(0, -6)">
            <ellipse cx="65" cy="18" rx="32" ry="8" fill="none" stroke="#fbbf24" strokeWidth="4.5" filter="url(#eyeGlow-m)" />
            <ellipse cx="65" cy="18" rx="32" ry="8" fill="none" stroke="#fef08a" strokeWidth="1.5" />
          </g>
        )}

        {/* Outer Ghost Body */}
        <path
          d="M 32 45 C 32 20, 98 20, 98 45 L 108 100 C 108 115, 94 125, 84 120 C 76 116, 68 124, 65 124 C 62 124, 54 116, 46 120 C 36 125, 22 115, 22 100 Z"
          fill={`url(#ghostGrad-${isTiny ? 'tiny' : 'main'})`}
          stroke="#cbd5e1"
          strokeWidth="1.5"
        />

        {/* Left Arm Stub */}
        <path
          d={currentWaving && !isTiny ? "M 22 75 Q 8 50 14 42" : "M 22 80 C 12 80 12 92 22 92"}
          fill="url(#headphoneGrad)"
          stroke="#e2e8f0"
          strokeWidth="2"
          className={currentWaving ? "animate-bounce" : "transition-all duration-300"}
        />

        {/* Right Arm Stub */}
        <path
          d={currentDancing && !isTiny ? "M 108 75 Q 122 50 116 42" : "M 108 80 C 118 80 118 92 108 92"}
          fill="url(#headphoneGrad)"
          stroke="#e2e8f0"
          strokeWidth="2"
          className={currentDancing ? "animate-bounce" : "transition-all duration-300"}
        />

        {/* Glossy Dark Visor Screen */}
        <rect
          x="35"
          y="42"
          width="60"
          height="45"
          rx="18"
          fill="#090d16"
          stroke="#1e293b"
          strokeWidth="2"
        />

        {/* Visor Glass Flare Reflection */}
        <path
          d="M 40 46 C 45 44 65 44 75 46 C 70 48 45 48 40 46 Z"
          fill="rgba(255, 255, 255, 0.25)"
        />

        {/* Rosy Pink Blushing Cheeks */}
        {(isBlushing || emotionState === 'loving' || emotionState === 'excited') && (
          <>
            <ellipse cx="44" cy="72" rx="5" ry="3" fill="#ff77a9" opacity="0.85" filter="url(#blushGlow)" />
            <ellipse cx="86" cy="72" rx="5" ry="3" fill="#ff77a9" opacity="0.85" filter="url(#blushGlow)" />
          </>
        )}

        {/* ACCESSORY SKIN: FLOWER */}
        {!isTiny && accessorySkin === 'flower' && (
          <g transform="translate(94, 20)">
            <circle cx="-6" cy="0" r="5" fill="#f472b6" />
            <circle cx="6" cy="0" r="5" fill="#f472b6" />
            <circle cx="0" cy="-6" r="5" fill="#f472b6" />
            <circle cx="0" cy="6" r="5" fill="#f472b6" />
            <circle cx="0" cy="0" r="4.5" fill="#fbbf24" />
          </g>
        )}

        {/* Animated Chest Light Badge */}
        <circle cx="65" cy="100" r={isTiny ? 2.5 : 4} fill="#38bdf8" className="animate-pulse" />

        {/* EYES Group inside Visor */}
        <g transform={`translate(${pupilPos.x}, ${pupilPos.y})`}>
          {isBlinking || currentSleeping || mainEyeMode === 'sleepy' ? (
            <>
              <path d="M 46 62 Q 52 68 58 62" fill="none" stroke={eyeColor} strokeWidth="3.5" strokeLinecap="round" />
              <path d="M 72 62 Q 78 68 84 62" fill="none" stroke={eyeColor} strokeWidth="3.5" strokeLinecap="round" />
            </>
          ) : mainEyeMode === 'winking' ? (
            <>
              <path d="M 46 64 Q 52 58 58 64" fill="none" stroke={eyeColor} strokeWidth="4" strokeLinecap="round" />
              <rect x="72" y="54" width="12" height="14" rx="5" fill={eyeColor} filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
            </>
          ) : mainEyeMode === 'surprised' ? (
            <>
              <circle cx="52" cy="61" r="7" fill={eyeColor} filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
              <circle cx="78" cy="61" r="7" fill={eyeColor} filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
            </>
          ) : mainEyeMode === 'heart' ? (
            <>
              <path
                d="M 52 56 C 50 52, 44 54, 46 60 L 52 66 L 58 60 C 60 54, 54 52, 52 56 Z"
                fill={eyeColor}
                filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`}
              />
              <path
                d="M 78 56 C 76 52, 70 54, 72 60 L 78 66 L 84 60 C 86 54, 80 52, 78 56 Z"
                fill={eyeColor}
                filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`}
              />
            </>
          ) : mainEyeMode === 'star' ? (
            <>
              <path
                d="M 52 53 L 54 58 L 59 58 L 55 61 L 57 66 L 52 63 L 47 66 L 49 61 L 45 58 L 50 58 Z"
                fill={eyeColor}
                filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`}
              />
              <path
                d="M 78 53 L 80 58 L 85 58 L 81 61 L 83 66 L 78 63 L 73 66 L 75 61 L 71 58 L 76 58 Z"
                fill={eyeColor}
                filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`}
              />
            </>
          ) : mainEyeMode === 'happy_arc' ? (
            <>
              <path d="M 46 64 Q 52 56 58 64" fill="none" stroke={eyeColor} strokeWidth="4" strokeLinecap="round" filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
              <path d="M 72 64 Q 78 56 84 64" fill="none" stroke={eyeColor} strokeWidth="4" strokeLinecap="round" filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
            </>
          ) : (
            <>
              <rect x="46" y="54" width="12" height="14" rx="5" fill={eyeColor} filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
              <rect x="72" y="54" width="12" height="14" rx="5" fill={eyeColor} filter={`url(#eyeGlow-${isTiny ? 't' : 'm'})`} />
            </>
          )}

          {mainEyeMode === 'sad' && (
            <>
              <circle cx="52" cy="72" r="2.5" fill="#38bdf8" className="animate-ping" />
              <circle cx="78" cy="72" r="2.5" fill="#38bdf8" className="animate-ping" />
            </>
          )}

          {!currentSleeping && mainEyeMode !== 'sleepy' && (
            <path
              d="M 60 74 Q 65 78 70 74"
              fill="none"
              stroke={eyeColor}
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          )}
        </g>

        {/* ACCESSORY SKIN: SUNGLASSES */}
        {!isTiny && accessorySkin === 'sunglasses' && (
          <g transform="translate(0, 0)">
            <path d="M 38 50 Q 65 52 92 50 L 89 63 Q 65 72 41 63 Z" fill="#0f172a" stroke="#38bdf8" strokeWidth="1.5" />
            <line x1="38" y1="52" x2="25" y2="48" stroke="#38bdf8" strokeWidth="2" />
            <line x1="92" y1="52" x2="105" y2="48" stroke="#38bdf8" strokeWidth="2" />
            <path d="M 42 52 L 56 52 L 48 61 Z" fill="rgba(255, 255, 255, 0.35)" />
          </g>
        )}
      </svg>
    );
  };

  return (
    <div
      className="relative inline-flex flex-col items-center justify-center select-none group cursor-pointer"
      onMouseEnter={() => setShowQuickToolbar(true)}
      onMouseLeave={() => setShowQuickToolbar(false)}
      tabIndex={0}
      aria-label="Interactive AI Ghost Companion Avatar - Click or pet me!"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') handlePoke(e);
      }}
    >
      {/* Speech Bubble Notification */}
      {speechBubble && (
        <div className="absolute -top-12 z-30 bg-slate-900/90 text-white text-xs font-semibold px-3 py-1.5 rounded-2xl border border-purple-500/40 shadow-xl backdrop-blur-md animate-bounce flex items-center gap-1.5 whitespace-nowrap">
          <span>{speechBubble}</span>
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-slate-900 border-r border-b border-purple-500/40 rotate-45" />
        </div>
      )}

      {/* Floating Emoji Particles Layer */}
      {floatingParticles.map((pt) => (
        <span
          key={pt.id}
          className="absolute z-40 text-lg pointer-events-none animate-float-up"
          style={{ left: `${pt.x}%`, top: `${pt.y}%` }}
        >
          {pt.emoji}
        </span>
      ))}

      {/* AURA SKINS BACKGROUND FX */}
      {auraSkin === 'cyber' && (
        <div className="absolute inset-0 rounded-full bg-cyan-500/20 border border-cyan-400/40 animate-pulse pointer-events-none blur-sm" />
      )}
      {auraSkin === 'stardust' && (
        <div className="absolute -inset-4 rounded-full bg-amber-500/15 border border-amber-300/30 animate-pulse pointer-events-none blur-md" />
      )}
      {auraSkin === 'galaxy' && (
        <div className="absolute -inset-4 rounded-full bg-purple-600/25 border border-purple-400/40 animate-pulse pointer-events-none blur-md" />
      )}
      {auraSkin === 'hearts' && (
        <div className="absolute -inset-4 rounded-full bg-pink-500/20 border border-pink-300/30 animate-pulse pointer-events-none blur-md" />
      )}

      {/* Radiating Voice Ripple Waveform Ring when AI is Speaking */}
      {isSpeaking && (
        <div className="absolute inset-0 rounded-full bg-purple-500/20 border-2 border-purple-400/50 animate-ripple pointer-events-none" />
      )}

      {/* Main Container */}
      <div
        className="relative"
        onClick={handlePoke}
        onDoubleClick={handleDoubleClick}
        onMouseMove={handleMouseMoveOver}
      >
        <div
          className={`relative transition-transform duration-300 transform-gpu ${
            isSpinning
              ? 'animate-spin360'
              : isSquishing
              ? 'animate-squish'
              : currentDancing
              ? 'animate-bounce'
              : currentSleeping
              ? 'rotate-12 translate-y-3'
              : isSpeaking
              ? 'scale-105'
              : 'animate-float'
          } hover:scale-105 active:scale-95`}
        >
          {renderGhostSVG(dimensions.mainW, dimensions.mainH, false)}

          {(currentDancing || isSpeaking) && (
            <div className="absolute -top-4 right-0 flex gap-1 text-purple-400 font-bold text-lg animate-bounce pointer-events-none">
              <span>🎵</span>
              <span className="[animation-delay:0.2s]">🎶</span>
            </div>
          )}

          {(currentSleeping || emotionState === 'sleepy') && (
            <div className="absolute -top-6 right-2 flex flex-col text-cyan-300 font-bold text-xs animate-pulse pointer-events-none">
              <span className="text-base">Z</span>
              <span className="text-sm ml-2">z</span>
              <span className="text-xs ml-4">z</span>
            </div>
          )}

          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <span className="text-[10px] bg-purple-600/80 text-white font-medium px-2 py-0.5 rounded-full shadow-md backdrop-blur-sm whitespace-nowrap">
              Click or Pet Me! ✨
            </span>
          </div>
        </div>

        {showTinyCompanion && (
          <div
            className={`absolute -top-2 -right-10 sm:-right-14 transition-all duration-500 ${
              currentDancing ? 'animate-bounce [animation-delay:0.1s]' : 'animate-float [animation-delay:0.5s]'
            }`}
          >
            <div className="absolute inset-0 bg-purple-500/20 rounded-full blur-xl animate-pulse pointer-events-none" />
            {renderGhostSVG(dimensions.tinyW, dimensions.tinyH, true)}

            {emotionState === 'loving' && (
              <span className="absolute -top-3 left-0 text-pink-400 text-xs animate-bounce pointer-events-none">💖</span>
            )}
          </div>
        )}
      </div>

      {enableControls && showQuickToolbar && size !== 'sm' && (
        <div className="absolute -bottom-10 z-30 flex items-center gap-1.5 bg-slate-950/90 backdrop-blur-md p-1.5 rounded-2xl border border-white/10 shadow-2xl animate-fade-in">
          <button
            onClick={(e) => { e.stopPropagation(); handleQuickAction('highfive'); }}
            className="p-1.5 rounded-xl hover:bg-purple-600/30 text-xs text-purple-200 transition-colors"
            title="Give High Five 🖐️"
          >
            🖐️
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleQuickAction('pet'); }}
            className="p-1.5 rounded-xl hover:bg-pink-600/30 text-xs text-pink-200 transition-colors"
            title="Pet / Hug 💖"
          >
            💖
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleQuickAction('dance'); }}
            className="p-1.5 rounded-xl hover:bg-amber-600/30 text-xs text-amber-200 transition-colors"
            title="Dance 🎵"
          >
            💃
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleQuickAction('nap'); }}
            className="p-1.5 rounded-xl hover:bg-cyan-600/30 text-xs text-cyan-200 transition-colors"
            title="Nap / Sleep 💤"
          >
            💤
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setIsMuted(!isMuted); }}
            className={`p-1.5 rounded-xl text-xs transition-colors ${
              isMuted ? 'text-red-400 bg-red-950/50' : 'text-emerald-400 hover:bg-emerald-600/30'
            }`}
            title={isMuted ? "Unmute Sound Effects" : "Mute Sound Effects"}
          >
            {isMuted ? '🔇' : '🔔'}
          </button>
        </div>
      )}
    </div>
  );
}
