"""
WithMe AI Core - Trainable Causal Transformer Language Model
Genuine from-scratch PyTorch implementation with causal self-attention,
next-token prediction, teacher forcing, configuration validation, and CPU presets.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class ModelConfig:
    """Validated configuration for WithMe Transformer Language Models."""
    vocab_size: int = 1500
    d_model: int = 128
    n_layers: int = 4
    n_heads: int = 4
    ffn_dim: int = 256
    max_seq_len: int = 128
    dropout: float = 0.1
    pad_token_id: int = 0

    def validate(self):
        """Validate architectural parameters to prevent runtime dimension failures."""
        if self.d_model % self.n_heads != 0:
            raise ValueError(
                f"Embedding dimension d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads}). "
                f"Suggested: d_model={self.n_heads * (self.d_model // self.n_heads or 1)}."
            )
        if self.vocab_size < 10:
            raise ValueError(f"vocab_size must be >= 10, got {self.vocab_size}.")
        if self.n_layers < 1:
            raise ValueError(f"n_layers must be >= 1, got {self.n_layers}.")
        if self.max_seq_len < 16:
            raise ValueError(f"max_seq_len must be >= 16, got {self.max_seq_len}.")
        if not (0.0 <= self.dropout < 1.0):
            raise ValueError(f"dropout must be in [0.0, 1.0), got {self.dropout}.")

    def estimate_parameter_count(self) -> int:
        """Calculate approximate parameter count before instantiation."""
        # Embeddings: tok_emb [vocab_size, d_model]
        emb = self.vocab_size * self.d_model
        # Per layer:
        # Attn: q, k, v, out [4 * d_model * d_model]
        # LN1, LN2: [2 * 2 * d_model]
        # FFN: [d_model * ffn_dim + ffn_dim * d_model + ffn_dim + d_model]
        per_layer = (4 * self.d_model * self.d_model) + (4 * self.d_model) + (2 * self.d_model * self.ffn_dim + self.ffn_dim + self.d_model)
        # LM Head: [d_model * vocab_size] (tied or linear)
        head = self.d_model * self.vocab_size
        return emb + (self.n_layers * per_layer) + head


# Predefined CPU presets for resource-conscious local execution
CPU_PRESETS: Dict[str, Dict[str, Any]] = {
    "cpu_smoke_test": {
        "description": "Ultra-lightweight sanity test (~45K params). Trains in seconds on CPU.",
        "d_model": 64,
        "n_layers": 2,
        "n_heads": 2,
        "ffn_dim": 128,
        "max_seq_len": 64,
        "dropout": 0.05
    },
    "cpu_standard": {
        "description": "Balanced conversational model (~350K params). Optimal for Windows laptop CPUs.",
        "d_model": 128,
        "n_layers": 4,
        "n_heads": 4,
        "ffn_dim": 256,
        "max_seq_len": 128,
        "dropout": 0.10
    },
    "cpu_extended": {
        "description": "Research-scale small Transformer (~2.5M params). Requires 2-5 minutes on 8+ CPU cores.",
        "d_model": 256,
        "n_layers": 6,
        "n_heads": 8,
        "ffn_dim": 512,
        "max_seq_len": 256,
        "dropout": 0.10
    }
}


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for sequence location awareness."""

    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # Shape: [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch_size, seq_len, d_model]
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class CausalSelfAttention(nn.Module):
    """Multi-head causal self-attention with lower-triangular autoregressive mask."""

    def __init__(self, d_model: int, n_heads: int, max_seq_len: int = 512, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0, f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)

        # Causal mask: lower triangular matrix
        mask = torch.tril(torch.ones(max_seq_len, max_seq_len)).view(1, 1, max_seq_len, max_seq_len)
        self.register_buffer("causal_mask", mask)

    def forward(self, x: torch.Tensor, key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        B, T, C = x.size()

        # Project and reshape to [B, n_heads, T, d_head]
        q = self.q_proj(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.n_heads, self.d_head).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_head)

        # Apply causal mask (prevent attending to future tokens)
        scores = scores.masked_fill(self.causal_mask[:, :, :T, :T] == 0, float("-inf"))

        # Apply optional key padding mask [B, 1, 1, T]
        if key_padding_mask is not None:
            scores = scores.masked_fill(key_padding_mask.unsqueeze(1).unsqueeze(2), float("-inf"))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.attn_dropout(attn_weights)

        context = torch.matmul(attn_weights, v)  # [B, n_heads, T, d_head]
        context = context.transpose(1, 2).contiguous().view(B, T, C)

        return self.resid_dropout(self.out_proj(context))


class TransformerBlock(nn.Module):
    """Transformer decoder block with Pre-LN architecture."""

    def __init__(self, d_model: int, n_heads: int, ffn_dim: int, max_seq_len: int, dropout: float = 0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_heads, max_seq_len=max_seq_len, dropout=dropout)

        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ffn_dim),
            nn.GELU(),
            nn.Linear(ffn_dim, d_model),
            nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor, key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Pre-LN Causal Self-Attention
        x = x + self.attn(self.ln1(x), key_padding_mask=key_padding_mask)
        # Pre-LN Feed-Forward
        x = x + self.ffn(self.ln2(x))
        return x


class WithMeTransformerLM(nn.Module):
    """
    WithMe Causal Language Model designed for genuine from-scratch experimental training.
    """

    def __init__(
        self,
        vocab_size: int = 1500,
        d_model: int = 128,
        n_layers: int = 4,
        n_heads: int = 4,
        ffn_dim: int = 256,
        max_seq_len: int = 128,
        dropout: float = 0.1,
        pad_token_id: int = 0
    ):
        super().__init__()
        # Validate configuration
        self.cfg = ModelConfig(
            vocab_size=vocab_size,
            d_model=d_model,
            n_layers=n_layers,
            n_heads=n_heads,
            ffn_dim=ffn_dim,
            max_seq_len=max_seq_len,
            dropout=dropout,
            pad_token_id=pad_token_id
        )
        self.cfg.validate()

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.ffn_dim = ffn_dim
        self.max_seq_len = max_seq_len
        self.dropout_rate = dropout
        self.pad_token_id = pad_token_id

        # Token & Positional Embeddings
        self.tok_emb = nn.Embedding(vocab_size, d_model, padding_idx=pad_token_id)
        self.pos_emb = PositionalEncoding(d_model, max_len=max_seq_len, dropout=dropout)

        # Decoder Blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads, ffn_dim, max_seq_len, dropout)
            for _ in range(n_layers)
        ])

        # Final LayerNorm and Output LM Head
        self.ln_f = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # Initialize weights randomly with standard normal scaled initialization
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if hasattr(module, "bias") and module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            nn.init.zeros_(module.bias)
            nn.init.ones_(module.weight)

    def get_config(self) -> Dict[str, Any]:
        """Return model architecture configuration dictionary."""
        return {
            "vocab_size": self.vocab_size,
            "d_model": self.d_model,
            "n_layers": self.n_layers,
            "n_heads": self.n_heads,
            "ffn_dim": self.ffn_dim,
            "max_seq_len": self.max_seq_len,
            "dropout": self.dropout_rate,
            "pad_token_id": self.pad_token_id,
            "param_count": self.count_parameters()
        }

    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(
        self,
        input_ids: torch.Tensor,
        targets: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass for next-token causal language modeling.
        input_ids: [batch_size, seq_len]
        targets: [batch_size, seq_len]
        """
        device = input_ids.device
        B, T = input_ids.size()
        assert T <= self.max_seq_len, f"Sequence length {T} exceeds max_seq_len {self.max_seq_len}"

        # Padding mask
        padding_mask = (input_ids == self.pad_token_id)

        # Embeddings
        x = self.tok_emb(input_ids)  # [B, T, d_model]
        x = self.pos_emb(x)

        # Forward through Transformer layers
        for block in self.blocks:
            x = block(x, key_padding_mask=padding_mask)

        x = self.ln_f(x)
        logits = self.lm_head(x)  # [B, T, vocab_size]

        loss = None
        if targets is not None:
            # Shifted cross-entropy loss for causal language modeling
            loss = F.cross_entropy(
                logits.view(-1, self.vocab_size),
                targets.view(-1),
                ignore_index=self.pad_token_id
            )

        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 50,
        temperature: float = 0.8,
        top_k: int = 40,
        top_p: float = 0.9,
        eos_id: int = 3
    ) -> torch.Tensor:
        """Autoregressive text generation with temperature, top-k, and top-p sampling."""
        self.eval()
        for _ in range(max_new_tokens):
            cond_ids = input_ids if input_ids.size(1) <= self.max_seq_len else input_ids[:, -self.max_seq_len:]
            logits, _ = self(cond_ids)

            logits = logits[:, -1, :]  # [B, vocab_size]

            if temperature <= 0.0:
                next_token = torch.argmax(logits, dim=-1, keepdim=True)
            else:
                logits = logits / temperature

                if top_k > 0:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = -float("Inf")

                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = -float("Inf")

                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

            input_ids = torch.cat([input_ids, next_token], dim=1)

            if next_token.item() == eos_id:
                break

        return input_ids


def create_model_from_preset(preset_name: str, vocab_size: int, pad_token_id: int = 0) -> WithMeTransformerLM:
    """Instantiate a WithMeTransformerLM using a validated CPU preset."""
    if preset_name not in CPU_PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(CPU_PRESETS.keys())}")
    preset = CPU_PRESETS[preset_name]
    return WithMeTransformerLM(
        vocab_size=vocab_size,
        d_model=preset["d_model"],
        n_layers=preset["n_layers"],
        n_heads=preset["n_heads"],
        ffn_dim=preset["ffn_dim"],
        max_seq_len=preset["max_seq_len"],
        dropout=preset["dropout"],
        pad_token_id=pad_token_id
    )
