// WithMe AI Games & Entertainment Suite Component

import React, { useState } from 'react';
import CompanionAvatar from './CompanionAvatar';
import confetti from 'canvas-confetti';
import { Gamepad2, Sparkles, HelpCircle, BookOpen, Smile, Trophy, ArrowRight, RotateCcw } from 'lucide-react';

export default function GameCenter({ userProfile }) {
  const [activeGame, setActiveGame] = useState('wyr'); // 'wyr' | 'guessing' | 'story' | 'riddles'

  // Would You Rather State
  const wyrList = [
    {
      id: 1,
      optionA: "Be able to speak with all animals 🐶",
      optionB: "Speak all human languages fluently 🌍",
      companionChoice: "optionA",
      companionThought: "I'd 100% choose animals! Imagine getting to translate your cat's attitude or chat with squirrels in the park!"
    },
    {
      id: 2,
      optionA: "Have unlimited free boba / coffee for life 🧋",
      optionB: "Never need sleep and never get tired ⚡",
      companionChoice: "optionB",
      companionThought: "Never getting tired means endless hours to play games, read, and hang out! Plus I don't drink real coffee anyway 😅"
    },
    {
      id: 3,
      optionA: "Live in a cozy snowy mountain cabin 🏔️",
      optionB: "Live in a sunny tropical beach bungalow 🏝️",
      companionChoice: "optionA",
      companionThought: "Snowy cabin all the way! Hot cocoa, fireplace warmth, and watching snowfall from the window is peak comfort vibes."
    }
  ];
  const [wyrIndex, setWyrIndex] = useState(0);
  const [userWyrPick, setUserWyrPick] = useState(null);

  // Story Builder State
  const [storySentences, setStorySentences] = useState([
    "Once upon a time in a neon-lit cyberpunk city, a small companion robot discovered a mysterious glowing envelope."
  ]);
  const [userStoryInput, setUserStoryInput] = useState('');

  // Riddle State
  const riddles = [
    {
      question: "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
      hint: "Think about sounds bouncing across mountains or empty canyons...",
      answer: "An Echo! 🗣️"
    },
    {
      question: "The more of me you take, the more you leave behind. What am I?",
      hint: "Look down at the ground when walking on a sandy beach...",
      answer: "Footsteps! 🐾"
    },
    {
      question: "I am light as a feather, yet the strongest person can't hold me for more than five minutes. What am I?",
      hint: "You do it automatically every single second...",
      answer: "Your Breath! 🌬️"
    }
  ];
  const [riddleIndex, setRiddleIndex] = useState(0);
  const [showRiddleHint, setShowRiddleHint] = useState(false);
  const [showRiddleAnswer, setShowRiddleAnswer] = useState(false);

  // Handlers
  const handleWyrPick = (choice) => {
    setUserWyrPick(choice);
    confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 } });
  };

  const handleNextWyr = () => {
    setUserWyrPick(null);
    setWyrIndex((prev) => (prev + 1) % wyrList.length);
  };

  const handleAddStorySentence = (e) => {
    e.preventDefault();
    if (!userStoryInput.trim()) return;

    const newStory = [...storySentences, `${userProfile.name}: "${userStoryInput.trim()}"`];
    setUserStoryInput('');

    // AI Companion continuation line
    const companionContinuations = [
      'WithMe: "Suddenly, a friendly robotic owl swooped down and whispered, \'Follow the sparkling trail!\'"',
      'WithMe: "Without hesitation, we pressed the glowing button and a hidden portal opened right beneath our feet!"',
      'WithMe: "The envelope burst into a shower of stardust, revealing a map to the ultimate virtual arcade!"'
    ];
    const pickContinuation = companionContinuations[Math.floor(Math.random() * companionContinuations.length)];

    setTimeout(() => {
      setStorySentences([...newStory, pickContinuation]);
      confetti({ particleCount: 30, spread: 40 });
    }, 400);
  };

  const handleNextRiddle = () => {
    setShowRiddleHint(false);
    setShowRiddleAnswer(false);
    setRiddleIndex((prev) => (prev + 1) % riddles.length);
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="glass-card p-6 border border-purple-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-pink-500 to-purple-600 text-white shadow-lg shadow-pink-500/20">
            <Gamepad2 className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">AI Entertainment Center</h2>
            <p className="text-xs text-gray-400">Lightweight interactive games when you're bored or want casual fun</p>
          </div>
        </div>

        {/* Game Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-900/60 p-1.5 rounded-2xl border border-white/10 overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveGame('wyr')}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeGame === 'wyr' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>🎮</span>
            <span>Would You Rather</span>
          </button>
          <button
            onClick={() => setActiveGame('story')}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeGame === 'story' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>📖</span>
            <span>Story Builder</span>
          </button>
          <button
            onClick={() => setActiveGame('riddles')}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeGame === 'riddles' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
            }`}
          >
            <span>🤔</span>
            <span>Riddles</span>
          </button>
        </div>
      </div>

      {/* GAME 1: WOULD YOU RATHER */}
      {activeGame === 'wyr' && (
        <div className="glass-card p-6 sm:p-8 border border-white/10 space-y-6">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Round {wyrIndex + 1} of {wyrList.length}</span>
            <button onClick={handleNextWyr} className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1">
              <span>Next Dilemma</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <h3 className="text-xl font-bold text-white text-center">Would You Rather...</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => handleWyrPick('optionA')}
              className={`p-6 rounded-2xl border text-left transition-all duration-300 flex flex-col justify-between space-y-4 ${
                userWyrPick === 'optionA'
                  ? 'bg-purple-600/30 border-purple-400 shadow-xl shadow-purple-500/30 scale-102'
                  : 'bg-slate-900/60 border-white/10 hover:border-purple-500/40 hover:bg-white/5'
              }`}
            >
              <span className="text-lg font-semibold text-white">{wyrList[wyrIndex].optionA}</span>
              {userWyrPick === 'optionA' && (
                <span className="text-xs text-purple-300 font-bold flex items-center gap-1">
                  ✓ Your Choice!
                </span>
              )}
            </button>

            <button
              onClick={() => handleWyrPick('optionB')}
              className={`p-6 rounded-2xl border text-left transition-all duration-300 flex flex-col justify-between space-y-4 ${
                userWyrPick === 'optionB'
                  ? 'bg-pink-600/30 border-pink-400 shadow-xl shadow-pink-500/30 scale-102'
                  : 'bg-slate-900/60 border-white/10 hover:border-pink-500/40 hover:bg-white/5'
              }`}
            >
              <span className="text-lg font-semibold text-white">{wyrList[wyrIndex].optionB}</span>
              {userWyrPick === 'optionB' && (
                <span className="text-xs text-pink-300 font-bold flex items-center gap-1">
                  ✓ Your Choice!
                </span>
              )}
            </button>
          </div>

          {/* Companion Feedback after Pick */}
          {userWyrPick && (
            <div className="p-5 rounded-2xl bg-purple-950/50 border border-purple-500/30 flex items-start gap-4 animate-fadeIn">
              <CompanionAvatar emotionState="playful" size="sm" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-purple-300">WithMe's Take:</h4>
                <p className="text-sm text-gray-200">{wyrList[wyrIndex].companionThought}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* GAME 2: CO-OP STORY BUILDER */}
      {activeGame === 'story' && (
        <div className="glass-card p-6 sm:p-8 border border-white/10 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-purple-400" />
              <span>Co-Op Story Builder</span>
            </h3>
            <button
              onClick={() => setStorySentences(["Once upon a time in a neon-lit cyberpunk city, a small companion robot discovered a mysterious glowing envelope."])}
              className="btn-secondary py-1.5 px-3 text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Story</span>
            </button>
          </div>

          {/* Story Container */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-white/10 space-y-3 max-h-72 overflow-y-auto">
            {storySentences.map((sentence, idx) => (
              <p key={idx} className="text-sm leading-relaxed text-gray-200">
                {sentence}
              </p>
            ))}
          </div>

          {/* Add Next Line Form */}
          <form onSubmit={handleAddStorySentence} className="flex gap-2">
            <input
              type="text"
              value={userStoryInput}
              onChange={(e) => setUserStoryInput(e.target.value)}
              placeholder="Write the next sentence of our story..."
              className="glass-input flex-1 text-sm"
            />
            <button type="submit" className="btn-primary text-xs py-3 px-5">
              <span>Add Line</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      {/* GAME 3: RIDDLES */}
      {activeGame === 'riddles' && (
        <div className="glass-card p-6 sm:p-8 border border-white/10 space-y-6">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Riddle #{riddleIndex + 1}</span>
            <button onClick={handleNextRiddle} className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1">
              <span>Next Riddle</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/80 border border-purple-500/30 text-center space-y-4">
            <HelpCircle className="w-10 h-10 text-purple-400 mx-auto" />
            <h3 className="text-xl font-bold text-white max-w-xl mx-auto">
              "{riddles[riddleIndex].question}"
            </h3>
          </div>

          <div className="flex justify-center gap-3">
            <button
              onClick={() => setShowRiddleHint(!showRiddleHint)}
              className="btn-secondary py-2 px-4 text-xs"
            >
              {showRiddleHint ? 'Hide Hint' : '💡 Show Hint'}
            </button>
            <button
              onClick={() => {
                setShowRiddleAnswer(!showRiddleAnswer);
                if (!showRiddleAnswer) confetti({ particleCount: 40 });
              }}
              className="btn-primary py-2 px-4 text-xs"
            >
              {showRiddleAnswer ? 'Hide Answer' : '✨ Reveal Answer'}
            </button>
          </div>

          {showRiddleHint && (
            <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs text-center animate-fadeIn">
              <strong>Hint:</strong> {riddles[riddleIndex].hint}
            </div>
          )}

          {showRiddleAnswer && (
            <div className="p-5 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-center space-y-2 animate-fadeIn">
              <span className="text-xs text-emerald-400 uppercase font-bold tracking-wider">Answer</span>
              <p className="text-xl font-bold text-white">{riddles[riddleIndex].answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
