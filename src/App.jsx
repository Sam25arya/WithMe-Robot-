// WithMe Application Main Component

import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import MoodCheckIn from './components/MoodCheckIn';
import ChatInterface from './components/ChatInterface';
import MemoryVault from './components/MemoryVault';
import GameCenter from './components/GameCenter';
import RemindersSystem from './components/RemindersSystem';
import RobotLab from './components/RobotLab';
import TrainingStudio from './components/training-studio/TrainingStudio';
import SettingsModal from './components/SettingsModal';
import { memoryStore } from './engine/memoryStore';
import { applyMoodTheme, getMoodById } from './engine/moodThemeEngine';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'memory' | 'games' | 'reminders' | 'robotLab'
  const [currentMoodId, setCurrentMoodId] = useState('good');
  const [userProfile, setUserProfile] = useState(memoryStore.getUserProfile());
  const [messages, setMessages] = useState(memoryStore.getChatLogs());
  const [showMoodModal, setShowMoodModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Apply visual theme glow when mood changes
  useEffect(() => {
    applyMoodTheme(currentMoodId);
  }, [currentMoodId]);

  // Persist chat logs when updated
  useEffect(() => {
    if (messages.length > 0) {
      memoryStore.saveChatLogs(messages);
    }
  }, [messages]);

  // Handle Mood Selection
  const handleSelectMood = (moodId) => {
    setCurrentMoodId(moodId);
    const mood = getMoodById(moodId);

    // Auto append companion greeting message for the newly selected mood
    const greetingMsg = {
      id: 'msg-' + Date.now(),
      sender: 'companion',
      text: mood.greeting,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      source: 'local'
    };

    setMessages((prev) => [...prev, greetingMsg]);
  };

  return (
    <div className="min-h-screen relative flex flex-col text-gray-100 overflow-x-hidden selection:bg-purple-500 selection:text-white">
      {/* Dynamic Ambient Background Glow Layer */}
      <div className="ambient-background" />

      {/* Main Navigation Header */}
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentMoodId={currentMoodId}
        onOpenMoodModal={() => setShowMoodModal(true)}
        onOpenSettings={() => setShowSettingsModal(true)}
        userProfile={userProfile}
      />

      {/* Main Tab Content Viewport */}
      <main className="flex-1 z-10 p-2 sm:p-4 md:p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'chat' && (
          <ChatInterface
            messages={messages}
            setMessages={setMessages}
            currentMoodId={currentMoodId}
            userProfile={userProfile}
          />
        )}

        {activeTab === 'memory' && (
          <MemoryVault userProfile={userProfile} />
        )}

        {activeTab === 'trainingStudio' && (
          <TrainingStudio userProfile={userProfile} />
        )}

        {activeTab === 'games' && (
          <GameCenter userProfile={userProfile} />
        )}

        {activeTab === 'reminders' && (
          <RemindersSystem />
        )}

        {activeTab === 'robotLab' && (
          <RobotLab currentMoodId={currentMoodId} />
        )}
      </main>

      {/* Mood Check-In Modal */}
      {showMoodModal && (
        <MoodCheckIn
          currentMoodId={currentMoodId}
          onSelectMood={handleSelectMood}
          onClose={() => setShowMoodModal(false)}
        />
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <SettingsModal
          userProfile={userProfile}
          setUserProfile={setUserProfile}
          onClose={() => setShowSettingsModal(false)}
        />
      )}
    </div>
  );
}
