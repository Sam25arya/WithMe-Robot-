// WithMe Main Friendship Chat Interface Component

import React, { useState, useRef, useEffect } from 'react';
import CompanionAvatar from './CompanionAvatar';
import { Send, Mic, MicOff, Volume2, Sparkles, RefreshCw, Zap, Heart, MessageCircle } from 'lucide-react';
import { sendCompanionMessage } from '../engine/aiService';
import { getMoodById } from '../engine/moodThemeEngine';

export default function ChatInterface({
  messages,
  setMessages,
  currentMoodId,
  userProfile,
  onMemoryExtracted
}) {
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [companionEmotion, setCompanionEmotion] = useState(getMoodById(currentMoodId).avatarState);
  const [isListening, setIsListening] = useState(false);
  const [autoSpeech, setAutoSpeech] = useState(false);
  const messagesEndRef = useRef(null);

  const mood = getMoodById(currentMoodId);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Quick contextual conversation starters
  const quickPrompts = [
    { text: "Today was really bad...", icon: "😔" },
    { text: "I have a big presentation tomorrow!", icon: "🚀" },
    { text: "I'm bored! Got any emergency ideas?", icon: "🚨" },
    { text: "Let's play Would You Rather!", icon: "🎮" },
    { text: "Tell me a fun riddle!", icon: "🤔" }
  ];

  // Text-to-Speech playback helper
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop ongoing
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.pitch = 1.1;
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Voice Input (Web Speech Recognition API fallback)
  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser version. You can type your message!');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInputText(transcript);
    };

    recognition.start();
  };

  // Send Message Handler
  const handleSendMessage = async (textToSend = inputText) => {
    const text = textToSend.trim();
    if (!text || isTyping) return;

    // Append User Message
    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInputText('');
    setIsTyping(true);

    // Call AI Companion Service
    try {
      const aiResult = await sendCompanionMessage({
        userMessage: text,
        moodId: currentMoodId,
        userName: userProfile.name
      });

      const companionMsg = {
        id: 'msg-' + (Date.now() + 1),
        sender: 'companion',
        text: aiResult.text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: aiResult.source
      };

      setMessages([...newHistory, companionMsg]);
      setCompanionEmotion(aiResult.emotionState || mood.avatarState);

      if (autoSpeech) {
        speakText(aiResult.text);
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-130px)] max-w-5xl mx-auto w-full glass-card overflow-hidden border border-white/10 shadow-2xl my-2">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-950/60 border-b border-white/10">
        <div className="flex items-center gap-4">
          <CompanionAvatar emotionState={companionEmotion} isSpeaking={isTyping} size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white">WithMe Companion</h2>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <p className="text-xs text-purple-300 font-medium flex items-center gap-1.5">
              <span>Mood: {mood.emoji} {mood.label}</span>
              <span className="text-gray-500">•</span>
              <span className="text-gray-400">Context Aware</span>
            </p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoSpeech(!autoSpeech)}
            className={`p-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all ${
              autoSpeech
                ? 'bg-purple-600/30 border-purple-500/50 text-purple-200'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-gray-200'
            }`}
            title="Toggle automatic speech out loud"
          >
            <Volume2 className="w-4 h-4" />
            <span className="hidden sm:inline">{autoSpeech ? 'Voice On' : 'Voice Off'}</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll View */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4">
            <CompanionAvatar emotionState={mood.avatarState} size="lg" />
            <div className="max-w-md">
              <h3 className="text-xl font-bold text-white mb-2">"I'm right here with you."</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Whether you had a tough day, feel bored, have an upcoming exam, or just want casual conversation without judgment.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-[85%] sm:max-w-[75%] ${
                  isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                }`}
              >
                {!isUser && (
                  <div className="shrink-0 mt-1">
                    <CompanionAvatar emotionState={companionEmotion} size="sm" />
                  </div>
                )}
                <div>
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-br-none shadow-lg shadow-purple-500/20'
                        : 'bg-slate-900/80 border border-white/10 text-gray-100 rounded-bl-none shadow-md'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                  </div>
                  <div className={`flex items-center gap-2 mt-1 px-1 text-[11px] text-gray-500 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <span>{msg.timestamp}</span>
                    {!isUser && msg.source === 'local' && (
                      <span className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded text-gray-400 border border-white/5">Local Smart Engine</span>
                    )}
                    {!isUser && (
                      <button
                        onClick={() => speakText(msg.text)}
                        className="hover:text-purple-400 transition-colors"
                        title="Read out loud"
                      >
                        <Volume2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex gap-3 mr-auto max-w-[75%] items-center">
            <CompanionAvatar emotionState="attentive" isSpeaking={true} size="sm" />
            <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-white/10 text-gray-400 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-pulse [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse [animation-delay:0.4s]"></span>
              <span className="ml-1 text-gray-400">WithMe is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div className="px-4 py-2 border-t border-white/5 bg-slate-950/40 overflow-x-auto flex items-center gap-2 no-scrollbar">
        <Sparkles className="w-4 h-4 text-purple-400 shrink-0 ml-1" />
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(qp.text)}
            className="shrink-0 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 hover:text-white transition-all flex items-center gap-1.5"
          >
            <span>{qp.icon}</span>
            <span>{qp.text}</span>
          </button>
        ))}
      </div>

      {/* Input Form Bar */}
      <div className="p-4 bg-slate-950/80 border-t border-white/10">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={handleVoiceInput}
            className={`p-3 rounded-xl border transition-all ${
              isListening
                ? 'bg-red-500/20 border-red-500 text-red-400 animate-pulse'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
            }`}
            title="Speech input"
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={`Talk to WithMe (${mood.label} mode)...`}
            className="flex-1 glass-input py-3 px-4 text-sm"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isTyping}
            className="btn-primary py-3 px-5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
