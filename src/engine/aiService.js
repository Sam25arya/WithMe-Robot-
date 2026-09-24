// WithMe Friendship AI Engine & Hybrid Provider

import { getMoodById } from './moodThemeEngine';
import { memoryStore } from './memoryStore';

// Companion System Prompt Template for API calls
function buildSystemPrompt(userMoodId, userName) {
  const mood = getMoodById(userMoodId);
  const memories = memoryStore.getMemories().map(m => `- ${m.content}`).join('\n');
  const user = memoryStore.getUserProfile();

  return `You are WithMe, a warm, casual, non-judgmental, friendship-style AI emotional companion.
Your user's name is ${userName || user.name}.
Their current self-reported mood is: ${mood.label} (${mood.emoji}).
Your conversation tone should be: ${mood.toneInstruction}.

IMPORTANT RULES:
1. DO NOT act like a generic search assistant or customer support bot. NEVER say "How can I assist you today?" or "As an AI language model...".
2. Speak like a supportive best friend: casual, empathetic, using occasional emoji, asking natural follow-up questions.
3. Keep answers concise (1-3 conversational sentences) unless the user asks for a story or deep vent.
4. DO NOT offer medical or clinical advice. If asked, respond with warmth and care.
5. Use remembered context when relevant. Current memory vault for ${user.name}:
${memories || '(No specific memories yet)'}

If the user expresses feeling bad, sad, or overwhelmed, ask gentle clarifying questions like "What happened?" or "Was it college or something else?" rather than giving immediate bulleted advice.`;
}

// Built-in Contextual Smart Fallback Response Generator
function generateFallbackResponse(userMessage, moodId, userName) {
  const msg = userMessage.toLowerCase().trim();
  const mood = getMoodById(moodId);
  const name = userName || 'friend';
  const memories = memoryStore.getMemories();

  // Check for Game Triggers
  if (msg.includes('would you rather') || msg.includes('play game') || msg.includes('game')) {
    const dilemmas = [
      "Alright! Would you rather be able to talk to animals 🐶 OR speak every human language fluently 🌍? (I think I'd choose animals so I could translate cat attitude!)",
      "Ooh fun! Would you rather have unlimited free coffee/boba for life 🧋 OR never need to sleep and never get tired ⚡?",
      "Here's a good one: Would you rather live in a cozy cabin in the snowy mountains 🏔️ OR a beachfront villa on a tropical island 🏝️?",
      "Would you rather be able to teleport anywhere instantly 🌌 OR turn back time by 10 minutes whenever you make a mistake ⏳?"
    ];
    const pick = dilemmas[Math.floor(Math.random() * dilemmas.length)];
    return {
      text: pick,
      emotionState: 'playful'
    };
  }

  if (msg.includes('bored') || msg.includes('nothing to do')) {
    return {
      text: `Bored already, ${name}? 😭 What kind of bored are we talking about—'nothing to do' bored or 'I don't feel like doing anything' bored? I can give you a riddle, start a story, or play Would You Rather!`,
      emotionState: 'playful'
    };
  }

  // Empathetic triggers
  if (msg.includes('bad day') || msg.includes('terrible day') || msg.includes('horrible day') || msg.includes('really bad')) {
    return {
      text: `Oh no, ${name}... 🥺 Today was really that bad? What happened—was it college, work, or just one of those days where everything felt overwhelming?`,
      emotionState: 'caring'
    };
  }

  if (msg.includes('presentation') || msg.includes('exam') || msg.includes('test') || msg.includes('interview')) {
    return {
      text: `Oof, pre-event jitters are so real! 😅 When is it taking place? Remember you've prepared for this, and I'll be right here cheering for you!`,
      emotionState: 'supportive'
    };
  }

  if (msg.includes('excited') || msg.includes('great news') || msg.includes('happy') || msg.includes('won') || msg.includes('passed')) {
    return {
      text: `Yessss! 🙌 That is incredible, ${name}! Tell me all the details—what happened?`,
      emotionState: 'happy'
    };
  }

  if (msg.includes('forgot') || msg.includes('messed up') || msg.includes('ruined')) {
    return {
      text: `Ouch... That's such an annoying feeling. 😭 But hey, don't beat yourself up too hard. Did anyone say anything to you about it?`,
      emotionState: 'caring'
    };
  }

  if (msg.includes('lonely') || msg.includes('alone') || msg.includes('no one to talk to')) {
    return {
      text: `I'm right here with you, ${name}. 💙 You don't have to carry your thoughts by yourself. What's been running through your mind today?`,
      emotionState: 'caring'
    };
  }

  if (msg.includes('hi') || msg.includes('hello') || msg.includes('hey')) {
    return {
      text: `${mood.greeting} I was hoping you'd stop by! How's your day treating you so far?`,
      emotionState: mood.avatarState
    };
  }

  if (msg.includes('riddle') || msg.includes('guess')) {
    return {
      text: `Here is a quick riddle for you! 🤔 "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?" (Hint: Think about sounds in a valley!)`,
      emotionState: 'curious'
    };
  }

  // Memory integration check
  const eventMem = memories.find(m => m.category === 'Events' || m.tag === 'Academic');
  if (eventMem && Math.random() > 0.6) {
    return {
      text: `I hear you. By the way, I was just thinking about how you mentioned: "${eventMem.content}". How are you feeling about that right now, ${name}?`,
      emotionState: 'attentive'
    };
  }

  // General conversational fallbacks adapting to mood
  const generalResponses = {
    happy: [
      `I love that energy! 😄 What else has been going well for you today?`,
      `That sounds so refreshing! Tell me more about it! ✨`,
      `That definitely put a smile on my face too! What's next on your agenda?`
    ],
    sad: [
      `I'm really listening, ${name}. Take all the time you need to share what's on your heart. 🫂`,
      `That sounds genuinely tough... I'm right here with you. Do you want to talk it through or just take a small mental break?`,
      `Thank you for trusting me with how you're feeling. You're not alone in this.`
    ],
    stressed: [
      `That sounds like a lot to hold at once. 🌬️ Let's take it one step at a time. What's the biggest thing weighing on you right now?`,
      `Deep breath... 🌿 You don't have to solve everything today. What's one tiny thing we can check off or simplify?`
    ],
    angry: [
      `Ugh, I would be frustrated too! 😤 Vent it all out—I'm totally in your corner.`,
      `That sounds super unfair! Tell me what happened next!`
    ],
    default: [
      `I hear you, ${name}. That's really interesting—how did that make you feel?`,
      `I get that! Tell me a bit more about what was going through your mind.`,
      `That's totally understandable. What are you planning to do for the rest of the day?`
    ]
  };

  const list = generalResponses[moodId] || generalResponses.default;
  const picked = list[Math.floor(Math.random() * list.length)];

  return {
    text: picked,
    emotionState: mood.avatarState
  };
}

// Main API / Fallback Dispatcher
export async function sendCompanionMessage({ userMessage, moodId, userName }) {
  const settings = memoryStore.getSettings();
  
  // Auto-extract memories in background
  memoryStore.autoExtractMemories(userMessage);

  // If Gemini API Key exists and local fallback is not forced
  if (settings.geminiApiKey && !settings.useLocalFallbackOnly) {
    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${settings.geminiApiKey}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [
              {
                role: 'user',
                parts: [
                  { text: buildSystemPrompt(moodId, userName) },
                  { text: `User message: "${userMessage}"` }
                ]
              }
            ],
            generationConfig: {
              maxOutputTokens: 250,
              temperature: 0.8
            }
          })
        }
      );

      if (response.ok) {
        const data = await response.json();
        const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (text) {
          return {
            text: text.trim(),
            emotionState: getMoodById(moodId).avatarState,
            source: 'gemini'
          };
        }
      }
    } catch (err) {
      console.warn('Gemini API call failed, falling back to smart local engine:', err);
    }
  }

  // Simulate human typing delay (400ms - 800ms) for natural feel
  await new Promise(res => setTimeout(res, 500 + Math.random() * 400));
  const fallback = generateFallbackResponse(userMessage, moodId, userName);
  return {
    ...fallback,
    source: 'local'
  };
}
