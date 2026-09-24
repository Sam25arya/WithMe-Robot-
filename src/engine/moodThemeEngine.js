// WithMe Mood & Theme Adaptation Engine

export const MOODS = [
  {
    id: 'happy',
    emoji: '😊',
    label: 'Happy',
    accentColor: '#10b981',
    glowColor: 'rgba(16, 185, 129, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(16, 185, 129, 0.22), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'vibrant, cheerful, playful, celebrating small wins',
    avatarState: 'happy',
    greeting: "Love the energy today! 🎉 What's making you smile?"
  },
  {
    id: 'good',
    emoji: '🙂',
    label: 'Good',
    accentColor: '#3b82f6',
    glowColor: 'rgba(59, 130, 246, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(59, 130, 246, 0.2), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'warm, relaxed, easygoing, friendly conversation',
    avatarState: 'smile',
    greeting: "Hey! Glad you're feeling good today. What's on your mind?"
  },
  {
    id: 'okay',
    emoji: '😐',
    label: 'Okay',
    accentColor: '#8b5cf6',
    glowColor: 'rgba(139, 92, 246, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(139, 92, 246, 0.2), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'attentive, cozy, inviting user to share if they want to',
    avatarState: 'curious',
    greeting: "Just an 'okay' day? I get those. Want to chat or just hang out?"
  },
  {
    id: 'sad',
    emoji: '😔',
    label: 'Sad',
    accentColor: '#6366f1',
    glowColor: 'rgba(99, 102, 241, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(99, 102, 241, 0.22), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'gentle, deeply empathetic, supportive, comforting, soft spoken',
    avatarState: 'caring',
    greeting: "I'm right here with you. 🫂 Want to talk about what's feeling heavy?"
  },
  {
    id: 'angry',
    emoji: '😡',
    label: 'Angry',
    accentColor: '#ef4444',
    glowColor: 'rgba(239, 68, 68, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(239, 68, 68, 0.22), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'validating, calming, non-dismissive, listening ear to vent',
    avatarState: 'focused',
    greeting: "Sounds like something really got to you. Vent away, I'm listening!"
  },
  {
    id: 'tired',
    emoji: '😴',
    label: 'Tired',
    accentColor: '#a855f7',
    glowColor: 'rgba(168, 85, 247, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(168, 85, 247, 0.18), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'low-energy, soothing, concise, gentle banter',
    avatarState: 'sleepy',
    greeting: "Exhausted? 🥱 Take it easy. I'm here if you want low-key company."
  },
  {
    id: 'stressed',
    emoji: '🤯',
    label: 'Stressed',
    accentColor: '#f59e0b',
    glowColor: 'rgba(245, 158, 11, 0.35)',
    bgGlow: 'radial-gradient(circle at 50% 20%, rgba(245, 158, 11, 0.22), rgba(11, 13, 20, 0.95) 70%)',
    toneInstruction: 'grounding, reassuring, step-by-step calm perspective',
    avatarState: 'attentive',
    greeting: "Breathe in... 🌬️ Too much happening at once? Let's untangle it together."
  }
];

export function getMoodById(id) {
  return MOODS.find(m => m.id === id) || MOODS[2]; // Default 'okay'
}

export function applyMoodTheme(moodId) {
  const mood = getMoodById(moodId);
  const root = document.documentElement;
  root.style.setProperty('--accent-primary', mood.accentColor);
  root.style.setProperty('--accent-glow', mood.glowColor);
  root.style.setProperty('--mood-bg-glow', mood.bgGlow);
}
