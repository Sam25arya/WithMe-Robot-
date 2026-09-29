# WithMe AI Core — Model Architecture Specification (Phase 2)

> **Philosophy**: *"A small, genuine, transparent Transformer model designed for local educational experimentation and emotional companion research on Windows CPUs."*

---

## 1. Architectural Overview

`WithMeTransformerLM` is a decoder-only causal language model initialized from scratch with randomly distributed weights ($\mathcal{N}(0.0, 0.02)$).

```text
Input Token IDs [B, T]
       │
       ▼
┌───────────────────────────────┐
│   Token Embedding (vocab, d)  │ ◄─── Padding Mask
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Sinusoidal Positional Encoding│
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐ ◄─── Repeat N_Layers
│      Transformer Block        │
│  ┌─────────────────────────┐  │
│  │ LayerNorm (Pre-LN)      │  │
│  │ Causal Multi-Head Attn  │  │
│  │ Residual Dropout & Add  │  │
│  ├─────────────────────────┤  │
│  │ LayerNorm (Pre-LN)      │  │
│  │ Feed-Forward MLP (GELU) │  │
│  │ Residual Dropout & Add  │  │
│  └─────────────────────────┘  │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Final LayerNorm (ln_f)        │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Language Modeling Head (d->V) │
└──────────────┬────────────────┘
               │
               ▼
Logits [B, T, vocab_size]
```

---

## 2. Key Components

### A. Sinusoidal Positional Encoding
Given token index $t$ and dimension channel $i$:
$$\text{PE}(t, 2i) = \sin\left(\frac{t}{10000^{2i/d}}\right), \quad \text{PE}(t, 2i+1) = \cos\left(\frac{t}{10000^{2i/d}}\right)$$
Adds deterministic positional information to token embeddings without requiring learned position weights.

### B. Causal Multi-Head Self-Attention
- **Projection**: Maps input tensor $X \in \mathbb{R}^{B \times T \times d}$ into queries $Q$, keys $K$, and values $V$ using learned linear projections.
- **Lower-Triangular Causal Mask**: Enforces the autoregressive property. Position $t$ can only attend to positions $\le t$:
  $$\text{Mask}_{i,j} = \begin{cases} 0 & \text{if } j \le i \\ -\infty & \text{if } j > i \end{cases}$$
- **Scaled Dot-Product Attention**:
  $$\text{Attention}(Q, K, V) = \text{Softmax}\left(\frac{QK^T}{\sqrt{d_{\text{head}}}} + \text{Mask}\right) V$$
- **Pre-LayerNorm Architecture**: Normalizes input before attention and FFN sub-layers, providing superior gradient propagation and stable training on CPUs without warm-up instability.

### C. Feed-Forward Network (FFN)
Two-layer projection with Gaussian Error Linear Unit (GELU) activation:
$$\text{FFN}(x) = \text{GELU}(x W_1 + b_1) W_2 + b_2$$
where $W_1 \in \mathbb{R}^{d \times d_{\text{ffn}}}$ and $W_2 \in \mathbb{R}^{d_{\text{ffn}} \times d}$.

---

## 3. Parameter Calculation Formula

The total trainable parameters for a WithMe Transformer model are calculated as:

$$\text{Parameters} = \underbrace{V \cdot d}_{\text{Token Embeddings}} + N_{\text{layers}} \times \left( \underbrace{4 d^2 + 4 d}_{\text{Attention } (Q, K, V, \text{Out})} + \underbrace{4 d}_{\text{LayerNorms}} + \underbrace{2 d \cdot d_{\text{ffn}} + d_{\text{ffn}} + d}_{\text{Feed-Forward MLP}} \right) + \underbrace{2 d}_{\text{Final LN}} + \underbrace{d \cdot V}_{\text{LM Head}}$$

---

## 4. Validated Configuration & CPU Presets

`ModelConfig` enforces structural constraints before model allocation:
- **Divisibility Rule**: $d_{\text{model}} \pmod{n_{\text{heads}}} = 0$.
- **Parameter Validation**: Requires positive dimensions and valid dropout rates ($0.0 \le p < 1.0$).

### Standard CPU Presets:

| Preset Name | $d_{\text{model}}$ | $N_{\text{layers}}$ | $N_{\text{heads}}$ | $d_{\text{ffn}}$ | Max Seq | Approx. Parameters | Target Use Case |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `cpu_smoke_test` | 64 | 2 | 2 | 128 | 64 | ~45,000 | Fast sanity verification (< 5s on CPU) |
| `cpu_standard` | 128 | 4 | 4 | 256 | 128 | ~350,000 | Recommended for local Windows laptops |
| `cpu_extended` | 256 | 6 | 8 | 512 | 256 | ~2,500,000 | Extended local experimentation |

---

## 5. Tokenizer Suite & Hinglish Handling

WithMe provides three modular tokenizers conforming to `BaseWithMeTokenizer`:

1. **`WithMeTokenizer`**: Standard word and sub-token engine with conversational tags (`<user>`, `<assistant>`, `<system>`, `<robot>`) and full multilingual Unicode support (Latin, Devanagari).
2. **`WithMeCharTokenizer`**: Educational character-level tokenizer mapping individual symbols to integer IDs.
3. **`WithMeSubwordTokenizer`**: Byte-Pair Encoding (BPE) subword tokenizer that learns frequent character n-gram merges. It decomposes colloquial and Hinglish words (e.g. *"Namaste"*, *"kaise"*, *"theek"*) into subword tokens, preventing out-of-vocabulary (`<unk>`) token explosions.
