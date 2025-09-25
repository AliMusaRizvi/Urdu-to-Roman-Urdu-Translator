# model_wrapper.py - Updated for deployment with attention model

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence
import os
import json
import sentencepiece as spm
import unicodedata
import re
import time
from datetime import datetime
import math
import numpy as np

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class SimplifiedMultiLevelTokenizer:
    """Simplified multi-level tokenizer for deployment."""

    def __init__(self, prefix, vocab_sizes=[15000]):
        self.prefix = prefix
        self.vocab_sizes = vocab_sizes
        self.tokenizers = {}

    def load_pretrained(self, model_file):
        """Load pre-trained SentencePiece model."""
        if os.path.exists(model_file):
            sp = spm.SentencePieceProcessor()
            sp.load(model_file)
            self.tokenizers['level0'] = sp
            print(f"Loaded {self.prefix} tokenizer with vocab size: {sp.get_piece_size()}")
            return True
        return False

    def encode_multilevel(self, text):
        """Encode text using primary level."""
        if 'level0' not in self.tokenizers:
            raise ValueError("Tokenizer not loaded")

        primary_tokenizer = self.tokenizers['level0']
        ids = [3] + primary_tokenizer.encode(text, out_type=int) + [1]  # BOS + text + EOS
        return {'level0': ids}

    def decode_multilevel(self, ids, level='level0'):
        """Decode from specific level."""
        if level in self.tokenizers:
            clean_ids = [id for id in ids if id not in [0, 1, 3]]  # Remove PAD, EOS, BOS
            return self.tokenizers[level].decode(clean_ids)
        return ""

    def get_vocab_size(self, level='level0'):
        """Get vocabulary size for specific level."""
        if level in self.tokenizers:
            return self.tokenizers[level].get_piece_size()
        return 0


def ultra_clean_urdu(text: str) -> str:
    """Enhanced Urdu cleaning for deployment."""
    if not isinstance(text, str):
        return ""

    # Multiple normalization passes
    text = unicodedata.normalize("NFC", text)

    # Remove all diacritics
    diacritics_pattern = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u08F0-\u08FF]")
    text = diacritics_pattern.sub("", text)

    # Comprehensive Arabic to Urdu normalization
    replacements = {
        "ك": "ک", "ي": "ی", "ة": "ہ", "أ": "ا", "إ": "ا", "آ": "ا",
        "ؤ": "و", "ئ": "ی", "ء": "", "ً": "", "ٌ": "", "ٍ": "",
        "َ": "", "ُ": "", "ِ": "", "ّ": "", "ْ": "", "ٰ": ""
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Clean whitespace around punctuation
    text = re.sub(r'\s*([۔،؍؎؏؞؟])\s*', r' \1 ', text)
    text = re.sub(r'\s+', ' ', text)

    # Remove non-Urdu characters but keep essential punctuation
    text = re.sub(r'[^\u0600-\u06FF\s۔،؍؎؏؞؟]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# Attention Mechanism
class BahdanauAttention(nn.Module):
    """Bahdanau attention mechanism for deployment."""

    def __init__(self, encoder_hidden_dim, decoder_hidden_dim, attention_dim=256):
        super().__init__()
        self.encoder_hidden_dim = encoder_hidden_dim
        self.decoder_hidden_dim = decoder_hidden_dim
        self.attention_dim = attention_dim

        self.encoder_projection = nn.Linear(encoder_hidden_dim, attention_dim)
        self.decoder_projection = nn.Linear(decoder_hidden_dim, attention_dim)
        self.attention_vector = nn.Linear(attention_dim, 1)
        self.dropout = nn.Dropout(0.1)

    def forward(self, encoder_outputs, decoder_hidden, src_lengths=None):
        batch_size, src_seq_len, _ = encoder_outputs.size()

        # Project encoder outputs
        encoder_proj = self.encoder_projection(encoder_outputs)

        # Project decoder hidden state and expand
        decoder_proj = self.decoder_projection(decoder_hidden).unsqueeze(1)
        decoder_proj = decoder_proj.expand(-1, src_seq_len, -1)

        # Compute attention scores
        attention_input = torch.tanh(encoder_proj + decoder_proj)
        attention_scores = self.attention_vector(attention_input).squeeze(-1)

        # Apply length mask if provided
        if src_lengths is not None:
            mask = torch.arange(src_seq_len, device=encoder_outputs.device).expand(
                batch_size, src_seq_len
            ) < src_lengths.unsqueeze(1)
            attention_scores = attention_scores.masked_fill(~mask, -1e9)

        # Apply softmax
        attention_weights = F.softmax(attention_scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # Compute context vector
        context = torch.bmm(attention_weights.unsqueeze(1), encoder_outputs).squeeze(1)

        return context, attention_weights


# Encoder
class StabilizedEncoder(nn.Module):
    """Stabilized encoder for deployment."""

    def __init__(self, vocab_size, embedding_dim, hidden_dim, num_layers=2, dropout=0.2):
        super().__init__()

        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embedding_norm = nn.LayerNorm(embedding_dim)
        self.embedding_dropout = nn.Dropout(dropout * 0.3)

        self.lstm = nn.LSTM(
            embedding_dim, hidden_dim, num_layers,
            bidirectional=True, dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )

        self.output_projection = nn.Linear(hidden_dim * 2, hidden_dim)
        self.output_norm = nn.LayerNorm(hidden_dim)

    def forward(self, input_ids, lengths):
        # Embedding
        embedded = self.embedding(input_ids)
        embedded = self.embedding_norm(embedded)
        embedded = self.embedding_dropout(embedded)

        # Pack sequences
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)

        # LSTM forward pass
        packed_output, (hidden, cell) = self.lstm(packed)

        # Unpack sequences
        encoder_outputs, _ = pad_packed_sequence(packed_output, batch_first=True)

        # Project to compatible dimensions
        encoder_outputs = self.output_projection(encoder_outputs)
        encoder_outputs = self.output_norm(encoder_outputs)

        return encoder_outputs, hidden, cell


# Decoder
class AttentionLSTMDecoder(nn.Module):
    """LSTM decoder with attention for deployment."""

    def __init__(self, vocab_size, embedding_dim, encoder_hidden_dim,
                 decoder_hidden_dim, num_layers=4, dropout=0.2, attention_dim=256):
        super().__init__()

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.decoder_hidden_dim = decoder_hidden_dim
        self.num_layers = num_layers
        self.encoder_hidden_dim = encoder_hidden_dim

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.embedding_norm = nn.LayerNorm(embedding_dim)
        self.embedding_dropout = nn.Dropout(dropout * 0.3)

        self.attention = BahdanauAttention(encoder_hidden_dim, decoder_hidden_dim, attention_dim)

        # LSTM layers
        self.lstm_cells = nn.ModuleList()
        for i in range(num_layers):
            input_size = embedding_dim + encoder_hidden_dim if i == 0 else decoder_hidden_dim
            self.lstm_cells.append(nn.LSTMCell(input_size, decoder_hidden_dim))

        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(decoder_hidden_dim) for _ in range(num_layers)
        ])

        # Bridge networks
        self.hidden_bridge = nn.Linear(encoder_hidden_dim * 2, decoder_hidden_dim * num_layers)
        self.cell_bridge = nn.Linear(encoder_hidden_dim * 2, decoder_hidden_dim * num_layers)

        # Output layers
        self.context_projection = nn.Linear(encoder_hidden_dim, decoder_hidden_dim)
        self.output_projection = nn.Linear(decoder_hidden_dim * 2, decoder_hidden_dim)
        self.final_output = nn.Linear(decoder_hidden_dim, vocab_size)

        self.dropout = nn.Dropout(dropout)

    def init_hidden_states(self, encoder_outputs, encoder_hidden, encoder_cell):
        """Initialize decoder hidden states."""
        batch_size = encoder_outputs.size(0)

        # Combine final states from both directions
        forward_hidden = encoder_hidden[::2]
        backward_hidden = encoder_hidden[1::2]
        forward_cell = encoder_cell[::2]
        backward_cell = encoder_cell[1::2]

        final_hidden = torch.cat([forward_hidden[-1], backward_hidden[-1]], dim=1)
        final_cell = torch.cat([forward_cell[-1], backward_cell[-1]], dim=1)

        # Project to decoder dimensions
        decoder_hidden = self.hidden_bridge(final_hidden)
        decoder_cell = self.cell_bridge(final_cell)

        # Reshape
        decoder_hidden = decoder_hidden.view(batch_size, self.num_layers, self.decoder_hidden_dim)
        decoder_cell = decoder_cell.view(batch_size, self.num_layers, self.decoder_hidden_dim)

        h_list = [decoder_hidden[:, i, :] for i in range(self.num_layers)]
        c_list = [decoder_cell[:, i, :] for i in range(self.num_layers)]

        return h_list, c_list

    def forward_step(self, input_token, hidden_states, cell_states, encoder_outputs, src_lengths):
        """Single forward step."""
        # Embedding
        embedded = self.embedding(input_token.squeeze(1))
        embedded = self.embedding_norm(embedded)
        embedded = self.embedding_dropout(embedded)

        # Attention
        context, attention_weights = self.attention(encoder_outputs, hidden_states[-1], src_lengths)

        # LSTM layers
        lstm_input = torch.cat([embedded, context], dim=1)
        new_hidden_states = []
        new_cell_states = []

        for i in range(self.num_layers):
            h, c = self.lstm_cells[i](lstm_input, (hidden_states[i], cell_states[i]))
            h = self.layer_norms[i](h)
            h = self.dropout(h)

            new_hidden_states.append(h)
            new_cell_states.append(c)
            lstm_input = h

        # Output computation
        top_hidden = new_hidden_states[-1]
        projected_context = self.context_projection(context)

        combined = torch.cat([top_hidden, projected_context], dim=1)
        output = self.output_projection(combined)
        output = F.gelu(output)
        output = self.dropout(output)
        output = output + top_hidden

        logits = self.final_output(output)

        return logits, new_hidden_states, new_cell_states, attention_weights

    def forward(self, encoder_outputs, encoder_hidden, encoder_cell, src_lengths, max_length=200):
        """Forward pass for inference."""
        batch_size = encoder_outputs.size(0)
        device = encoder_outputs.device

        hidden_states, cell_states = self.init_hidden_states(encoder_outputs, encoder_hidden, encoder_cell)

        outputs = []
        input_token = torch.full((batch_size, 1), 3, dtype=torch.long).to(device)  # BOS token

        for step in range(max_length):
            output, hidden_states, cell_states, _ = self.forward_step(
                input_token, hidden_states, cell_states, encoder_outputs, src_lengths
            )
            outputs.append(output.unsqueeze(1))

            # Greedy decoding
            input_token = output.argmax(dim=1, keepdim=True)

            # Early stopping
            if (input_token == 1).all():  # EOS token
                break

        return torch.cat(outputs, dim=1) if outputs else torch.zeros(batch_size, 1, self.vocab_size).to(device)


# Main Model
class EnhancedSeq2SeqModel(nn.Module):
    """Enhanced Seq2Seq model for deployment."""

    def __init__(self, src_vocab_size, tgt_vocab_size, embedding_dim,
                 encoder_hidden_dim, decoder_hidden_dim, dropout=0.2, attention_dim=256):
        super().__init__()

        self.encoder = StabilizedEncoder(
            vocab_size=src_vocab_size,
            embedding_dim=embedding_dim,
            hidden_dim=encoder_hidden_dim,
            num_layers=2,
            dropout=dropout
        )

        self.decoder = AttentionLSTMDecoder(
            vocab_size=tgt_vocab_size,
            embedding_dim=embedding_dim,
            encoder_hidden_dim=encoder_hidden_dim,
            decoder_hidden_dim=decoder_hidden_dim,
            num_layers=4,
            dropout=dropout,
            attention_dim=attention_dim
        )

    def forward(self, src_ids, src_lengths, max_length=200):
        encoder_outputs, encoder_hidden, encoder_cell = self.encoder(src_ids, src_lengths)
        decoder_outputs = self.decoder(encoder_outputs, encoder_hidden, encoder_cell, src_lengths, max_length)
        return decoder_outputs


class UrduRomanTranslator:
    """Main translator class for deployment."""

    def __init__(self, model_path='best_attention_model.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.src_tokenizer = None
        self.tgt_tokenizer = None
        self.config = None
        self.best_bleu = 0

        # Session statistics
        self.session_stats = {
            'total_translations': 0,
            'avg_translation_time': 0,
            'total_characters_processed': 0
        }

        # Load model and tokenizers
        self._load_model(model_path)

    def _load_model(self, model_path):
        """Load the trained model and tokenizers."""
        try:
            print(f"Loading model from {model_path}...")

            # Load tokenizers
            self.src_tokenizer = SimplifiedMultiLevelTokenizer('urdu', vocab_sizes=[15000])
            self.tgt_tokenizer = SimplifiedMultiLevelTokenizer('roman', vocab_sizes=[12000])

            # Load SentencePiece models
            urdu_loaded = self.src_tokenizer.load_pretrained('urdu_level0.model')
            roman_loaded = self.tgt_tokenizer.load_pretrained('roman_level0.model')

            if not urdu_loaded or not roman_loaded:
                raise FileNotFoundError("Tokenizer model files not found")

            # Load model checkpoint
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device)

                # Get configuration
                self.config = checkpoint.get('config', {})
                self.best_bleu = checkpoint.get('best_bleu', 0)

                # Create model with loaded vocab sizes
                src_vocab_size = self.src_tokenizer.get_vocab_size('level0')
                tgt_vocab_size = self.tgt_tokenizer.get_vocab_size('level0')

                self.model = EnhancedSeq2SeqModel(
                    src_vocab_size=src_vocab_size,
                    tgt_vocab_size=tgt_vocab_size,
                    embedding_dim=self.config.get('embedding_dim', 512),
                    encoder_hidden_dim=self.config.get('encoder_hidden_dim', 512),
                    decoder_hidden_dim=self.config.get('decoder_hidden_dim', 512),
                    dropout=self.config.get('dropout', 0.1),
                    attention_dim=self.config.get('attention_dim', 256)
                ).to(self.device)

                # Load trained weights
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.model.eval()

                print(f"✅ Model loaded successfully!")
                print(f"   BLEU Score: {self.best_bleu:.2f}")
                print(f"   Device: {self.device}")
                print(f"   Urdu Vocab: {src_vocab_size:,}")
                print(f"   Roman Vocab: {tgt_vocab_size:,}")

            else:
                raise FileNotFoundError(f"Model file {model_path} not found")

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise e

    def translate(self, urdu_text, max_length=200):
        """Translate Urdu text to Roman Urdu."""
        if not self.model or not self.src_tokenizer or not self.tgt_tokenizer:
            return "Error: Model not loaded properly", 0

        start_time = time.time()

        try:
            # Clean input text
            cleaned_text = ultra_clean_urdu(urdu_text.strip())

            if not cleaned_text:
                return "Error: Empty or invalid text", 0

            # Encode source text
            src_encodings = self.src_tokenizer.encode_multilevel(cleaned_text)
            src_ids = torch.tensor([src_encodings['level0']]).to(self.device)
            src_lengths = torch.tensor([len(src_encodings['level0'])]).to(self.device)

            # Generate translation
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(src_ids, src_lengths, max_length=max_length)
                pred_tokens = outputs[0].argmax(dim=-1).cpu().numpy()

            # Decode output
            pred_tokens_clean = [int(t) for t in pred_tokens if t not in [0, 1, 2, 3]]
            translation = self.tgt_tokenizer.decode_multilevel(pred_tokens_clean, 'level0').strip()

            if not translation:
                translation = "Translation unavailable"

            translation_time = time.time() - start_time

            # Update statistics
            self._update_stats(urdu_text, translation_time)

            return translation, translation_time

        except Exception as e:
            print(f"Translation error: {e}")
            return f"Error: Translation failed - {str(e)}", time.time() - start_time

    def _update_stats(self, input_text, translation_time):
        """Update session statistics."""
        self.session_stats['total_translations'] += 1
        self.session_stats['total_characters_processed'] += len(input_text)

        if self.session_stats['avg_translation_time'] == 0:
            self.session_stats['avg_translation_time'] = translation_time
        else:
            current_avg = self.session_stats['avg_translation_time']
            new_avg = (current_avg + translation_time) / 2
            self.session_stats['avg_translation_time'] = new_avg