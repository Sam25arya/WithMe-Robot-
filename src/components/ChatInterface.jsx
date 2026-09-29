// WithMe Main Friendship Chat Interface Component

import React, { useState, useRef, useEffect, useCallback } from 'react';
import CompanionAvatar from './CompanionAvatar';
import { Send, Mic, MicOff, Volume2, VolumeX, Sparkles, Radio, Settings2, SlidersHorizontal, AlertCircle } from 'lucide-react';
import { sendCompanionMessage } from '../engine/aiService';
import { getMoodById } from '../engine/moodThemeEngine';
import { speechEngine } from '../engine/speechEngine';
import { memoryStore } from '../engine/memoryStore';

export default function ChatInterface({
  messages,
  setMessages,
  currentMoodId,
  userProfile
}) {
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [companionEmotion, setCompanionEmotion] = useState(getMoodById(currentMoodId).avatarState);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [micError, setMicError] = useState(null);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);

  // Settings
  const [appSettings, setAppSettings] = useState(() => memoryStore.getSettings());
  const [autoSpeech, setAutoSpeech] = useState(appSettings.autoSpeechEnabled ?? false);
  const [handsFreeMode, setHandsFreeMode] = useState(appSettings.handsFreeMode ?? false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState(appSettings.voiceURI || '');
  const [voicePitch, setVoicePitch] = useState(appSettings.voicePitch ?? 1.1);
  const [voiceRate, setVoiceRate] = useState(appSettings.voiceRate ?? 1.0);

  const messagesEndRef = useRef(null);
  const handsFreeActiveRef = useRef(handsFreeMode);

  useEffect(() => {
    handsFreeActiveRef.current = handsFreeMode;
  }, [handsFreeMode]);

  const mood = getMoodById(currentMoodId);

  // Load voices on mount
  useEffect(() => {
    const updateVoices = () => {
      const v = speechEngine.getVoices();
      setAvailableVoices(v);
    };
    updateVoices();
    speechEngine.onVoiceListChanged = updateVoices;
  }, []);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, interimText]);

  // Quick contextual conversation starters
  const quickPrompts = [
    { text: "Today was really bad...", icon: "😔" },
    { text: "I have a big presentation tomorrow!", icon: "🚀" },
    { text: "I'm bored! Got any emergency ideas?", icon: "🚨" },
    { text: "Let's play Would You Rather!", icon: "🎮" },
    { text: "Tell me a fun riddle!", icon: "🤔" }
  ];

  // Speech Output helper
  const speakCompanionResponse = useCallback((text, onFinishCallback = null) => {
    setIsSpeaking(true);
    speechEngine.speak(text, {
      voiceURI: selectedVoiceURI,
      pitch: voicePitch,
      rate: voiceRate,
      onStart: () => setIsSpeaking(true),
      onEnd: () => {
        setIsSpeaking(false);
        if (onFinishCallback) onFinishCallback();
      },
      onError: () => {
        setIsSpeaking(false);
        if (onFinishCallback) onFinishCallback();
      }
    });
  }, [selectedVoiceURI, voicePitch, voiceRate]);

  // Stop current speech
  const handleStopSpeech = () => {
    speechEngine.stop();
    setIsSpeaking(false);
  };

  // Save Voice Settings
  const handleSaveVoiceSettings = (newURI, newPitch, newRate) => {
    setSelectedVoiceURI(newURI);
    setVoicePitch(newPitch);
    setVoiceRate(newRate);
    const updated = { ...appSettings, voiceURI: newURI, voicePitch: newPitch, voiceRate: newRate };
    memoryStore.setSettings(updated);
    setAppSettings(updated);
  };

  // Forward declaration of handleSendMessage
  const sendMessageRef = useRef(null);

  // Speech Recognition Control
  const startMicListening = useCallback(() => {
    setMicError(null);
    setInterimText('');

    speechEngine.startListening({
      continuous: false,
      interimResults: true,
      onStart: () => setIsListening(true),
      onResult: ({ finalTranscript, interimTranscript }) => {
        if (interimTranscript) {
          setInterimText(interimTranscript);
        }
        if (finalTranscript) {
          setInterimText('');
          setInputText(finalTranscript);
          setIsListening(false);

          // If in hands-free mode, auto send the spoken transcript!
          if (handsFreeActiveRef.current && sendMessageRef.current) {
            sendMessageRef.current(finalTranscript);
          }
        }
      },
      onError: (err) => {
        setIsListening(false);
        setInterimText('');
        if (err !== 'no-speech' && err !== 'aborted') {
          setMicError(`Microphone issue: ${err}`);
        }
      },
      onEnd: () => {
        setIsListening(false);
      }
    });
  }, []);

  const stopMicListening = useCallback(() => {
    speechEngine.stopListening();
    setIsListening(false);
    setInterimText('');
  }, []);

  const toggleMicListening = () => {
    if (isListening) {
      stopMicListening();
    } else {
      startMicListening();
    }
  };

  // Send Message Handler
  const handleSendMessage = async (textToSend = inputText) => {
    const text = textToSend.trim();
    if (!text || isTyping) return;

    // Stop active listening or speaking when sending
    stopMicListening();
    handleStopSpeech();

    const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Append User Message
    const userMsg = {
      id: 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4),
      sender: 'user',
      text: text,
      timestamp: timestampStr
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInputText('');
    setInterimText('');
    setIsTyping(true);

    // Call AI Companion Service
    try {
      const aiResult = await sendCompanionMessage({
        userMessage: text,
        moodId: currentMoodId,
        userName: userProfile.name
      });

      const companionMsg = {
        id: 'msg-' + (Date.now() + 1) + '-' + Math.random().toString(36).substr(2, 4),
        sender: 'companion',
        text: aiResult.text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: aiResult.source
      };

      setMessages([...newHistory, companionMsg]);
      setCompanionEmotion(aiResult.emotionState || mood.avatarState);

      // Auto Read Out Loud if AutoSpeech or HandsFree is enabled
      if (autoSpeech || handsFreeMode) {
        speakCompanionResponse(aiResult.text, () => {
          // If HandsFree mode is active, automatically reactivate mic for seamless user voice reply!
          if (handsFreeActiveRef.current) {
            setTimeout(() => {
              startMicListening();
            }, 600);
          }
        });
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsTyping(false);
    }
  };

  useEffect(() => {
    sendMessageRef.current = handleSendMessage;
  });

  return (
    <div className="flex flex-col h-[calc(100vh-130px)] max-w-5xl mx-auto w-full glass-card overflow-hidden border border-white/10 shadow-2xl my-2 relative">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-950/70 border-b border-white/10 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="relative">
            <CompanionAvatar
              emotionState={companionEmotion}
              isSpeaking={isSpeaking || isTyping}
              size="sm"
              accessorySkin={appSettings.accessorySkin || 'headphones'}
              auraSkin={appSettings.auraSkin || 'cyber'}
            />
            {isSpeaking && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white">WithMe Companion</h2>
              {isSpeaking ? (
                <span className="text-[10px] bg-purple-600/40 text-purple-200 border border-purple-400/40 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                  <Volume2 className="w-3 h-3" /> Speaking...
                </span>
              ) : isListening ? (
                <span className="text-[10px] bg-red-600/40 text-red-200 border border-red-400/40 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                  <Radio className="w-3 h-3" /> Listening...
                </span>
              ) : (
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              )}
            </div>
            <p className="text-xs text-purple-300 font-medium flex items-center gap-1.5">
              <span>Mood: {mood.emoji} {mood.label}</span>
              <span className="text-gray-500">•</span>
              <span className="text-gray-400">Context Aware</span>
            </p>
          </div>
        </div>

        {/* Header Voice & Hands-Free Controls */}
        <div className="flex items-center gap-2">
          {/* Hands-Free Mode Toggle */}
          <button
            onClick={() => {
              const nextVal = !handsFreeMode;
              setHandsFreeMode(nextVal);
              if (nextVal) {
                setAutoSpeech(true);
                startMicListening();
              } else {
                stopMicListening();
              }
              const updated = { ...appSettings, handsFreeMode: nextVal, autoSpeechEnabled: nextVal || autoSpeech };
              memoryStore.setSettings(updated);
            }}
            className={`p-2 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-all ${
              handsFreeMode
                ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white border-pink-400/50 shadow-lg shadow-pink-500/30'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-gray-200'
            }`}
            title="Hands-Free Walkie-Talkie Mode: Continuous voice conversation"
          >
            <Radio className={`w-4 h-4 ${handsFreeMode ? 'animate-pulse text-white' : ''}`} />
            <span className="hidden sm:inline">{handsFreeMode ? 'Hands-Free ON' : 'Hands-Free'}</span>
          </button>

          {/* Auto Read Out Loud Toggle */}
          <button
            onClick={() => {
              const nextVal = !autoSpeech;
              setAutoSpeech(nextVal);
              const updated = { ...appSettings, autoSpeechEnabled: nextVal };
              memoryStore.setSettings(updated);
            }}
            className={`p-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all ${
              autoSpeech
                ? 'bg-purple-600/30 border-purple-500/50 text-purple-200'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-gray-200'
            }`}
            title="Toggle automatic speech out loud"
          >
            {autoSpeech ? <Volume2 className="w-4 h-4 text-purple-400" /> : <VolumeX className="w-4 h-4 text-gray-500" />}
            <span className="hidden md:inline">{autoSpeech ? 'Voice On' : 'Voice Off'}</span>
          </button>

          {/* Voice Tuning Customization Drawer Button */}
          <button
            onClick={() => setShowVoiceSettings(!showVoiceSettings)}
            className="p-2 rounded-xl border bg-white/5 border-white/10 text-gray-400 hover:text-white transition-all"
            title="Voice & Speech Settings"
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Voice Tuning Settings Panel Modal Overlay */}
      {showVoiceSettings && (
        <div className="absolute top-16 right-4 z-40 w-80 p-4 rounded-2xl glass-card border border-purple-500/40 shadow-2xl space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Settings2 className="w-4 h-4 text-purple-400" />
              <span>Voice & Synth Customization</span>
            </h4>
            <button
              onClick={() => setShowVoiceSettings(false)}
              className="text-gray-400 hover:text-white text-xs font-bold px-2 py-0.5 rounded bg-white/5"
            >
              ✕
            </button>
          </div>

          {/* Voice Selection Dropdown */}
          <div>
            <label className="text-xs text-gray-300 block mb-1">Companion Voice</label>
            <select
              value={selectedVoiceURI}
              onChange={(e) => handleSaveVoiceSettings(e.target.value, voicePitch, voiceRate)}
              className="w-full glass-input text-xs py-2 px-2.5 rounded-xl bg-slate-900 text-white"
            >
              <option value="">Auto Selected (Default)</option>
              {availableVoices.map((v) => (
                <option key={v.voiceURI} value={v.voiceURI}>
                  {v.name} ({v.lang})
                </option>
              ))}
            </select>
          </div>

          {/* Pitch Slider */}
          <div>
            <div className="flex justify-between text-xs text-gray-300 mb-1">
              <span>Voice Pitch</span>
              <span className="text-purple-400 font-mono">{voicePitch.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.8"
              step="0.1"
              value={voicePitch}
              onChange={(e) => handleSaveVoiceSettings(selectedVoiceURI, parseFloat(e.target.value), voiceRate)}
              className="w-full accent-purple-500 cursor-pointer"
            />
          </div>

          {/* Speed / Rate Slider */}
          <div>
            <div className="flex justify-between text-xs text-gray-300 mb-1">
              <span>Speech Speed</span>
              <span className="text-purple-400 font-mono">{voiceRate.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.6"
              max="1.6"
              step="0.1"
              value={voiceRate}
              onChange={(e) => handleSaveVoiceSettings(selectedVoiceURI, voicePitch, parseFloat(e.target.value))}
              className="w-full accent-purple-500 cursor-pointer"
            />
          </div>

          <button
            onClick={() => speakCompanionResponse("Hello there! This is how my customized voice sounds like!")}
            className="w-full btn-secondary py-2 text-xs flex items-center justify-center gap-1.5"
          >
            <Volume2 className="w-3.5 h-3.5 text-purple-400" />
            <span>Test Voice Audio</span>
          </button>
        </div>
      )}

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
                    <CompanionAvatar emotionState={companionEmotion} isSpeaking={isSpeaking} size="sm" />
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
                        onClick={() => {
                          if (isSpeaking) {
                            handleStopSpeech();
                          } else {
                            speakCompanionResponse(msg.text);
                          }
                        }}
                        className="hover:text-purple-400 transition-colors flex items-center gap-1"
                        title={isSpeaking ? "Stop reading" : "Read out loud"}
                      >
                        <Volume2 className="w-3.5 h-3.5" />
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

      {/* Mic Warning Error Banner */}
      {micError && (
        <div className="px-4 py-2 bg-red-950/80 border-t border-red-500/30 text-red-300 text-xs flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-red-400" />
            {micError}
          </span>
          <button onClick={() => setMicError(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Live Interim Speech Recognition Bar */}
      {(isListening || interimText) && (
        <div className="px-4 py-2.5 bg-purple-950/60 border-t border-purple-500/30 flex items-center gap-3 animate-fadeIn">
          <div className="flex items-center gap-1 text-red-400 shrink-0">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
            <span className="text-xs font-semibold uppercase tracking-wider">Listening</span>
          </div>
          <p className="text-xs text-purple-200 italic truncate flex-1">
            "{interimText || 'Speak clearly into your microphone...'}"
          </p>
          <button
            onClick={stopMicListening}
            className="text-[11px] text-gray-400 hover:text-white px-2 py-0.5 rounded bg-white/10"
          >
            Cancel
          </button>
        </div>
      )}

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
            onClick={toggleMicListening}
            className={`p-3 rounded-xl border transition-all flex items-center justify-center ${
              isListening
                ? 'bg-red-500/30 border-red-500 text-red-300 animate-pulse shadow-lg shadow-red-500/20'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
            }`}
            title={isListening ? "Stop listening" : "Start speech voice input"}
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              handsFreeMode
                ? "Hands-free active! Speak anytime or type here..."
                : `Talk to WithMe (${mood.label} mode)...`
            }
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
