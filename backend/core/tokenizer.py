"""
WithMe AI Core - Custom Conversational Tokenizer Suite
Provides:
1. BaseWithMeTokenizer (Abstract interface)
2. WithMeTokenizer (Hybrid word/punct conversational tokenizer)
3. WithMeCharTokenizer (Character-level educational baseline)
4. WithMeSubwordTokenizer (Byte-Pair Encoding subword tokenizer with multilingual & Hinglish support)
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Union, Optional, Tuple, Set, Any

SPECIAL_TOKENS = [
    "<pad>",
    "<unk>",
    "<bos>",
    "<eos>",
    "<user>",
    "<assistant>",
    "<system>",
    "<robot>"
]

PAD_TOKEN_ID = 0
UNK_TOKEN_ID = 1
BOS_TOKEN_ID = 2
EOS_TOKEN_ID = 3
USER_TOKEN_ID = 4
ASSISTANT_TOKEN_ID = 5
SYSTEM_TOKEN_ID = 6
ROBOT_TOKEN_ID = 7


class BaseWithMeTokenizer:
    """Abstract base class defining tokenizer contract."""

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        raise NotImplementedError

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        raise NotImplementedError

    @property
    def vocab_size(self) -> int:
        raise NotImplementedError

    @property
    def pad_id(self) -> int:
        return PAD_TOKEN_ID

    @property
    def eos_id(self) -> int:
        return EOS_TOKEN_ID

    @property
    def bos_id(self) -> int:
        return BOS_TOKEN_ID


class WithMeTokenizer(BaseWithMeTokenizer):
    """
    Standard conversational tokenizer for WithMe models.
    Supports tokenizing conversational text, handling special role tokens,
    vocabulary persistence, and subword/token frequency building with Hinglish support.
    """

    def __init__(self, vocab: Optional[Dict[str, int]] = None):
        self.special_tokens = SPECIAL_TOKENS.copy()
        if vocab:
            self.token2id = vocab
            self.id2token = {v: k for k, v in vocab.items()}
        else:
            self.token2id = {token: idx for idx, token in enumerate(self.special_tokens)}
            self.id2token = {idx: token for token, idx in self.token2id.items()}

    @property
    def vocab_size(self) -> int:
        return len(self.token2id)

    def _basic_tokenize(self, text: str) -> List[str]:
        """Split text into words, punctuation, numbers, preserving special tokens and multilingual Unicode."""
        special_pattern = "|".join(re.escape(tok) for tok in self.special_tokens)
        # Unicode-aware word and punctuation matching including Devanagari (\u0900-\u097F)
        pattern = rf"({special_pattern}|[\w\u0900-\u097F]+|[^\w\s])"
        tokens = re.findall(pattern, text, re.UNICODE)
        return [t for t in tokens if t.strip()]

    def train_from_corpus(self, texts: List[str], max_vocab_size: int = 1500, min_freq: int = 1):
        """Train vocabulary directly from provided training corpus."""
        freq: Dict[str, int] = {}
        for text in texts:
            tokens = self._basic_tokenize(text)
            for tok in tokens:
                if tok not in self.special_tokens:
                    freq[tok] = freq.get(tok, 0) + 1

        sorted_tokens = sorted(
            [tok for tok, count in freq.items() if count >= min_freq],
            key=lambda t: (-freq[t], t)
        )

        remaining_slots = max(0, max_vocab_size - len(self.special_tokens))
        top_tokens = sorted_tokens[:remaining_slots]

        self.token2id = {token: idx for idx, token in enumerate(self.special_tokens)}
        for tok in top_tokens:
            if tok not in self.token2id:
                new_id = len(self.token2id)
                self.token2id[tok] = new_id

        self.id2token = {idx: tok for tok, idx in self.token2id.items()}

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Convert string to list of token IDs."""
        tokens = self._basic_tokenize(text)
        ids = []
        if add_special_tokens:
            ids.append(BOS_TOKEN_ID)

        for tok in tokens:
            ids.append(self.token2id.get(tok, UNK_TOKEN_ID))

        if add_special_tokens:
            ids.append(EOS_TOKEN_ID)
        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """Convert list of token IDs back into readable string."""
        tokens = []
        for idx in ids:
            tok = self.id2token.get(idx, "<unk>")
            if skip_special_tokens and tok in self.special_tokens:
                continue
            tokens.append(tok)

        text = ""
        for i, tok in enumerate(tokens):
            if i == 0 or tok in ".,!?;:'\")}]" or text.endswith("(") or text.endswith("[") or text.endswith('"'):
                text += tok
            else:
                text += " " + tok
        return text.strip()

    def format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format a list of multi-turn messages into tokenizable sequence."""
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "").strip()
            if role == "system":
                formatted += f"<system> {content} "
            elif role == "user":
                formatted += f"<user> {content} "
            elif role == "assistant":
                formatted += f"<assistant> {content} "
            elif role == "robot":
                formatted += f"<robot> {content} "
        return formatted.strip()

    def save(self, filepath: Union[str, Path]):
        """Persist tokenizer configuration and vocabulary to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "type": "WithMeTokenizer",
            "vocab": self.token2id,
            "special_tokens": self.special_tokens,
            "vocab_size": self.vocab_size
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "WithMeTokenizer":
        """Load tokenizer from saved JSON file."""
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(vocab=data.get("vocab", {}))


class WithMeCharTokenizer(BaseWithMeTokenizer):
    """
    Pure character-level tokenizer for initial baseline experiments.
    Maps individual characters (ASCII, Unicode, punctuation) to IDs.
    """

    def __init__(self, vocab: Optional[Dict[str, int]] = None):
        self.special_tokens = SPECIAL_TOKENS.copy()
        if vocab:
            self.token2id = vocab
            self.id2token = {v: k for k, v in vocab.items()}
        else:
            self.token2id = {token: idx for idx, token in enumerate(self.special_tokens)}
            self.id2token = {idx: token for token, idx in self.token2id.items()}

    @property
    def vocab_size(self) -> int:
        return len(self.token2id)

    def train_from_corpus(self, texts: List[str]):
        """Build character set from corpus."""
        chars: Set[str] = set()
        for t in texts:
            chars.update(set(t))

        self.token2id = {tok: idx for idx, tok in enumerate(self.special_tokens)}
        for ch in sorted(chars):
            if ch not in self.token2id:
                self.token2id[ch] = len(self.token2id)
        self.id2token = {v: k for k, v in self.token2id.items()}

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        ids = []
        if add_special_tokens:
            ids.append(BOS_TOKEN_ID)
        for ch in text:
            ids.append(self.token2id.get(ch, UNK_TOKEN_ID))
        if add_special_tokens:
            ids.append(EOS_TOKEN_ID)
        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        out = []
        for idx in ids:
            ch = self.id2token.get(idx, "")
            if skip_special_tokens and ch in self.special_tokens:
                continue
            out.append(ch)
        return "".join(out)

    def format_conversation(self, messages: List[Dict[str, str]]) -> str:
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "").strip()
            formatted += f"<{role}> {content} "
        return formatted.strip()

    def save(self, filepath: Union[str, Path]):
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "type": "WithMeCharTokenizer",
                "vocab": self.token2id,
                "vocab_size": self.vocab_size
            }, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "WithMeCharTokenizer":
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(vocab=data.get("vocab", {}))


class WithMeSubwordTokenizer(BaseWithMeTokenizer):
    """
    Subword Byte-Pair (BPE) tokenizer with multilingual & Hinglish support.
    Iteratively learns frequent character n-gram merges to tokenize unseen words gracefully.
    """

    def __init__(self, vocab: Optional[Dict[str, int]] = None, merges: Optional[List[Tuple[str, str]]] = None):
        self.special_tokens = SPECIAL_TOKENS.copy()
        self.merges: List[Tuple[str, str]] = merges or []

        if vocab:
            self.token2id = vocab
            self.id2token = {v: k for k, v in vocab.items()}
        else:
            self.token2id = {token: idx for idx, token in enumerate(self.special_tokens)}
            self.id2token = {idx: token for token, idx in self.token2id.items()}

    @property
    def vocab_size(self) -> int:
        return len(self.token2id)

    def train_from_corpus(self, texts: List[str], max_merges: int = 100):
        """Train BPE subword merges from conversational texts."""
        # Initialize characters from corpus
        all_chars: Set[str] = set()
        words = []
        for text in texts:
            # Tokenize into whitespace words
            raw_words = re.findall(r"[\w\u0900-\u097F]+|[^\w\s]", text, re.UNICODE)
            for w in raw_words:
                if w.strip() and w not in self.special_tokens:
                    chars = list(w)
                    all_chars.update(chars)
                    words.append(chars)

        # Seed base character vocabulary
        self.token2id = {token: idx for idx, token in enumerate(self.special_tokens)}
        for ch in sorted(all_chars):
            if ch not in self.token2id:
                self.token2id[ch] = len(self.token2id)

        # Iteratively learn merges
        self.merges = []
        for _ in range(max_merges):
            pair_counts: Dict[Tuple[str, str], int] = {}
            for w in words:
                for i in range(len(w) - 1):
                    pair = (w[i], w[i + 1])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

            if not pair_counts:
                break

            best_pair = max(pair_counts, key=pair_counts.get)
            if pair_counts[best_pair] < 2:
                break

            self.merges.append(best_pair)
            merged_token = "".join(best_pair)
            if merged_token not in self.token2id:
                self.token2id[merged_token] = len(self.token2id)

            # Apply merge to words
            new_words = []
            for w in words:
                new_w = []
                i = 0
                while i < len(w):
                    if i < len(w) - 1 and (w[i], w[i + 1]) == best_pair:
                        new_w.append(merged_token)
                        i += 2
                    else:
                        new_w.append(w[i])
                        i += 1
                new_words.append(new_w)
            words = new_words

        self.id2token = {idx: token for token, idx in self.token2id.items()}

    def _tokenize_word(self, word: str) -> List[str]:
        tokens = list(word)
        for pair in self.merges:
            merged = "".join(pair)
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == pair:
                    new_tokens.append(merged)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        return tokens

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        words = re.findall(r"<[^>]+>|[\w\u0900-\u097F]+|[^\w\s]", text, re.UNICODE)
        ids = []
        if add_special_tokens:
            ids.append(BOS_TOKEN_ID)

        for w in words:
            if w in self.special_tokens:
                ids.append(self.token2id.get(w, UNK_TOKEN_ID))
            else:
                subtokens = self._tokenize_word(w)
                for st in subtokens:
                    ids.append(self.token2id.get(st, UNK_TOKEN_ID))

        if add_special_tokens:
            ids.append(EOS_TOKEN_ID)
        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        tokens = []
        for idx in ids:
            tok = self.id2token.get(idx, "")
            if skip_special_tokens and tok in self.special_tokens:
                continue
            tokens.append(tok)
        return "".join(tokens)

    def format_conversation(self, messages: List[Dict[str, str]]) -> str:
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "").strip()
            formatted += f"<{role}> {content} "
        return formatted.strip()

    def save(self, filepath: Union[str, Path]):
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "type": "WithMeSubwordTokenizer",
                "vocab": self.token2id,
                "merges": self.merges,
                "vocab_size": self.vocab_size
            }, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "WithMeSubwordTokenizer":
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(vocab=data.get("vocab", {}), merges=[tuple(m) for m in data.get("merges", [])])


def check_tokenizer_compatibility(tokenizer: BaseWithMeTokenizer, checkpoint_config: Dict[str, Any]) -> Tuple[bool, str]:
    """Check that active tokenizer matches checkpoint vocabulary size and pad/eos tokens."""
    expected_vocab = checkpoint_config.get("vocab_size")
    if expected_vocab is not None and expected_vocab != tokenizer.vocab_size:
        return False, f"Vocabulary size mismatch: Model checkpoint expects {expected_vocab} tokens, but active tokenizer has {tokenizer.vocab_size}."
    return True, "Tokenizer is fully compatible."
