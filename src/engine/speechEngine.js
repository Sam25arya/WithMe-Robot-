// WithMe Advanced Web Speech Synthesis & Recognition Engine

class SpeechEngine {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.voices = [];
    this.currentUtterance = null;
    this.recognition = null;
    this.isListening = false;
    this.onVoiceListChanged = null;

    if (this.synth) {
      this.loadVoices();
      if (typeof this.synth.onvoiceschanged !== 'undefined') {
        this.synth.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  loadVoices() {
    if (!this.synth) return [];
    this.voices = this.synth.getVoices();
    if (this.onVoiceListChanged) {
      this.onVoiceListChanged(this.voices);
    }
    return this.voices;
  }

  getVoices() {
    if (!this.voices.length && this.synth) {
      this.voices = this.synth.getVoices();
    }
    return this.voices;
  }

  getDefaultVoice() {
    const voices = this.getVoices();
    if (!voices.length) return null;

    // Prefer English natural/google/apple friendly voices
    const preferredNames = ['Google US English', 'Samantha', 'Microsoft Zira', 'Karen', 'Victoria', 'Daniel'];
    for (const name of preferredNames) {
      const match = voices.find(v => v.name.includes(name) || v.voiceURI.includes(name));
      if (match) return match;
    }

    // Fallback to first English voice or first overall voice
    return voices.find(v => v.lang.startsWith('en')) || voices[0];
  }

  speak(text, options = {}) {
    if (!this.synth) return false;

    // Cancel ongoing speech
    this.synth.cancel();

    // Clean text (remove emojis & markdown formatting for cleaner speech output)
    const cleanText = text
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
      .replace(/[*_~`#]/g, '')
      .trim();

    if (!cleanText) return false;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const voices = this.getVoices();

    // Voice selection
    if (options.voiceURI) {
      const selectedVoice = voices.find(v => v.voiceURI === options.voiceURI);
      if (selectedVoice) utterance.voice = selectedVoice;
    }
    if (!utterance.voice) {
      utterance.voice = this.getDefaultVoice();
    }

    utterance.pitch = options.pitch ?? 1.1;
    utterance.rate = options.rate ?? 1.0;
    utterance.volume = options.volume ?? 1.0;

    // Event hooks
    if (options.onStart) utterance.onstart = options.onStart;
    if (options.onEnd) utterance.onend = options.onEnd;
    if (options.onError) utterance.onerror = options.onError;
    if (options.onBoundary) utterance.onboundary = options.onBoundary;

    this.currentUtterance = utterance;
    this.synth.speak(utterance);
    return true;
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
    }
  }

  // Check if Speech Recognition is supported
  isRecognitionSupported() {
    return typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);
  }

  // Speech Recognition Initializer
  startListening(callbacks = {}) {
    if (!this.isRecognitionSupported()) {
      if (callbacks.onError) callbacks.onError('Speech Recognition is not supported in this browser version.');
      return null;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    // Stop any existing instance
    if (this.recognition) {
      try { this.recognition.stop(); } catch {}
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = callbacks.continuous ?? false;
    recognition.interimResults = callbacks.interimResults ?? true;
    recognition.lang = callbacks.lang || 'en-US';

    recognition.onstart = () => {
      this.isListening = true;
      if (callbacks.onStart) callbacks.onStart();
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      if (callbacks.onResult) {
        callbacks.onResult({ finalTranscript, interimTranscript });
      }
    };

    recognition.onerror = (event) => {
      this.isListening = false;
      if (callbacks.onError) callbacks.onError(event.error);
    };

    recognition.onend = () => {
      this.isListening = false;
      if (callbacks.onEnd) callbacks.onEnd();
    };

    this.recognition = recognition;
    try {
      recognition.start();
    } catch (err) {
      if (callbacks.onError) callbacks.onError(err.message);
    }

    return recognition;
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch {}
      this.isListening = false;
    }
  }
}

export const speechEngine = new SpeechEngine();
