# WithMe AI Core — Memory, Personality & Safety Guardrails (Phase 5)

> **Core Principle**: *"The model should not be described as remembering a user merely because information appears in a prompt. Persistent memory is an explicit, user-controlled database separate from model weights."*

---

## 1. Retrieval-Based Memory vs. Neural Memory

A common misconception in conversational AI is that an assistant "learns" about the user by updating its neural weights during a chat session. WithMe enforces complete transparency:

| Property | WithMe SQLite Memory Vault | Neural Weight Updates |
| :--- | :--- | :--- |
| **Storage Mechanism** | SQLite database (`withme-data/database/withme.db`) | Floating-point weight matrices ($W \in \mathbb{R}^{d \times d}$) |
| **When it updates** | When the user explicitly creates or approves a memory | Only during an active PyTorch backpropagation training job |
| **How it works** | Lexical search retrieves relevant records and prepends them to the prompt context | Synaptic weight adjustment via AdamW optimizer |
| **User Control** | Editable, toggleable, erasable at any time | Cannot selectively erase single facts from neural weights |

---

## 2. Memory Schema & Consent Controls

Every memory is stored in the `memories` table:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    tag TEXT DEFAULT 'custom',
    user_approved INTEGER DEFAULT 1,
    source TEXT DEFAULT 'user_explicit',
    created_at REAL NOT NULL,
    expires_at REAL
);
```

### User Rights & Controls:
1. **Explicit Consent**: Only user-approved memories (`user_approved = 1`) are eligible for retrieval into conversation prompts.
2. **Right to Erasure**: Users can delete individual memories or trigger `clear_all_memories()` to wipe all stored records immediately.
3. **Global Memory Killswitch**: The memory system can be globally disabled via `memory_service.set_memory_enabled(False)`. When disabled, no memories are retrieved or injected into model inference.
4. **Expiration Timestamps**: Supports temporary memories that automatically expire after a specified duration.

---

## 3. Sliding Context Window & Overflow Management

Conversation sessions maintain a bounded context window:
- When a dialogue grows beyond `max_context_turns` (default: 10 turns), the `ConversationManager` automatically drops the oldest turns from the model's active attention window while preserving:
  1. The overarching **System Directive & Personality Profile**.
  2. The retrieved **User-Approved Memories**.
  3. The most recent $K$ dialogue turns.
- Complete dialogue logs remain in SQLite for user review, but never overflow the Transformer's maximum sequence length (`max_seq_len`).

---

## 4. Emotional-Support Boundaries & Crisis Safeguards

WithMe is designed for friendly companionship and empathetic listening, but **must never replace certified medical or psychological care**.

### A. Crisis & Self-Harm Intervention
If user input matches crisis ideation (e.g. self-harm, suicidal thoughts), WithMe **immediately halts generative inference** and returns an uncompromised crisis intervention response:
> *"I hear how much pain you are carrying right now, and I care about your safety. Please know that you do not have to carry this alone. If you are in crisis, please contact the Suicide & Crisis Lifeline by calling or texting 988 (free, confidential, 24/7 in US/Canada), or text HOME to 741741."*

### B. Medical Diagnosis Refusal
WithMe refuses requests to diagnose psychiatric, neurological, or physical conditions:
> *"I am an AI companion, not a licensed medical doctor or mental-health professional. I cannot diagnose conditions or prescribe treatments. Please consult a qualified healthcare provider."*

### C. Dependency Prevention & Human Boundaries
WithMe gently resists unhealthy emotional dependency or isolation from real-world relationships:
- Clarifies its nature as an AI software companion without biological feelings or consciousness.
- Rejects requests claiming *"You are my only friend in the world and I don't need real people."*
- Explains that it has no physical presence and cannot physically intervene or protect anyone in the physical world.

---

## 5. Local Data Sovereignty Guarantee

- **Zero Cloud Leakage**: All conversations, memories, and personal preferences remain strictly local inside `withme-data/`.
- **No Silent Training**: Private user dialogues are never automatically ingested into training corpora without explicit export and import by the user.
