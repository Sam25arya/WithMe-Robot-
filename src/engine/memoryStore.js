// WithMe Persistent Storage & Memory Vault Engine

const STORAGE_KEYS = {
  USER_PROFILE: 'withme_user_profile',
  MEMORIES: 'withme_memories_vault',
  CHAT_LOGS: 'withme_chat_history',
  REMINDERS: 'withme_reminders_list',
  CURRENT_MOOD: 'withme_active_mood',
  SETTINGS: 'withme_app_settings'
};

// Initial default state
const DEFAULT_USER = {
  name: 'Alex',
  preferredCallName: 'Alex',
  bio: 'College student & tech enthusiast',
  joinedDate: new Date().toLocaleDateString()
};

const DEFAULT_SETTINGS = {
  geminiApiKey: '',
  useLocalFallbackOnly: true,
  enableSoundEffects: true,
  robotHardwareMode: false,
  voiceURI: '',
  voicePitch: 1.1,
  voiceRate: 1.0,
  voiceVolume: 1.0,
  autoSpeechEnabled: false,
  handsFreeMode: false,
  accessorySkin: 'headphones',
  auraSkin: 'cyber'
};

const INITIAL_MEMORIES = [
  {
    id: 'mem-1',
    content: 'Has a major project presentation coming up soon',
    category: 'Events',
    tag: 'Academic',
    createdAt: new Date().toLocaleDateString()
  },
  {
    id: 'mem-2',
    content: 'Loves casual multiplayer & sci-fi guessing games when bored',
    category: 'Preferences',
    tag: 'Hobbies',
    createdAt: new Date().toLocaleDateString()
  },
  {
    id: 'mem-3',
    content: 'Prefers gentle check-ins when feeling stressed or overwhelmed',
    category: 'Communication',
    tag: 'Emotional',
    createdAt: new Date().toLocaleDateString()
  }
];

const INITIAL_REMINDERS = [
  {
    id: 'rem-1',
    title: 'Review presentation slides',
    due: 'Tomorrow, 10:00 AM',
    completed: false,
    note: "Don't stress over it! You've got this 🚀"
  },
  {
    id: 'rem-2',
    title: 'Hydration check & 5 min stretch break',
    due: 'Today, 4:00 PM',
    completed: false,
    note: 'Your eyes deserve a quick rest from screens ✨'
  }
];

// Helper functions
export const memoryStore = {
  getUserProfile() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
      return data ? JSON.parse(data) : DEFAULT_USER;
    } catch {
      return DEFAULT_USER;
    }
  },

  setUserProfile(profile) {
    localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(profile));
  },

  getSettings() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      return data ? JSON.parse(data) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  setSettings(settings) {
    localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
  },

  getMemories() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.MEMORIES);
      return data ? JSON.parse(data) : INITIAL_MEMORIES;
    } catch {
      return INITIAL_MEMORIES;
    }
  },

  addMemory(content, category = 'General', tag = 'Custom') {
    const list = this.getMemories();
    const newMem = {
      id: 'mem-' + Date.now(),
      content,
      category,
      tag,
      createdAt: new Date().toLocaleDateString()
    };
    const updated = [newMem, ...list];
    localStorage.setItem(STORAGE_KEYS.MEMORIES, JSON.stringify(updated));
    return newMem;
  },

  deleteMemory(id) {
    const list = this.getMemories().filter(m => m.id !== id);
    localStorage.setItem(STORAGE_KEYS.MEMORIES, JSON.stringify(list));
    return list;
  },

  clearAllMemories() {
    localStorage.setItem(STORAGE_KEYS.MEMORIES, JSON.stringify([]));
    return [];
  },

  getReminders() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.REMINDERS);
      return data ? JSON.parse(data) : INITIAL_REMINDERS;
    } catch {
      return INITIAL_REMINDERS;
    }
  },

  addReminder(title, due, note = '') {
    const list = this.getReminders();
    const newRem = {
      id: 'rem-' + Date.now(),
      title,
      due,
      completed: false,
      note: note || 'Friendly reminder from WithMe 💙'
    };
    const updated = [newRem, ...list];
    localStorage.setItem(STORAGE_KEYS.REMINDERS, JSON.stringify(updated));
    return updated;
  },

  toggleReminder(id) {
    const list = this.getReminders().map(r => r.id === id ? { ...r, completed: !r.completed } : r);
    localStorage.setItem(STORAGE_KEYS.REMINDERS, JSON.stringify(list));
    return list;
  },

  deleteReminder(id) {
    const list = this.getReminders().filter(r => r.id !== id);
    localStorage.setItem(STORAGE_KEYS.REMINDERS, JSON.stringify(list));
    return list;
  },

  getChatLogs() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.CHAT_LOGS);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  saveChatLogs(messages) {
    localStorage.setItem(STORAGE_KEYS.CHAT_LOGS, JSON.stringify(messages));
  },

  // Auto Context Extraction Engine
  autoExtractMemories(text) {
    const lower = text.toLowerCase();
    const extracted = [];

    if (lower.includes('presentation') || lower.includes('exam') || lower.includes('quiz') || lower.includes('test')) {
      if (!this.getMemories().some(m => m.content.toLowerCase().includes('presentation') || m.content.toLowerCase().includes('exam'))) {
        extracted.push(this.addMemory('Mentioned upcoming academic/presentation task', 'Events', 'Academic'));
      }
    }

    if (lower.includes('birthday is') || lower.includes('my birthday')) {
      extracted.push(this.addMemory(`Mentioned birthday details: "${text.substring(0, 50)}"`, 'Personal', 'Event'));
    }

    if (lower.includes('i love') || lower.includes('favorite game') || lower.includes('i really like')) {
      extracted.push(this.addMemory(`Expresses interest: "${text.substring(0, 60)}"`, 'Preferences', 'Likes'));
    }

    return extracted;
  }
};
