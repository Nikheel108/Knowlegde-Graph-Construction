from __future__ import annotations

import math
import random
import re
from collections import Counter
from typing import Any

_POSITIVE_WORDS = {"excellent", "good", "great", "happy", "love", "success", "successful", "benefit", "beneficial", "improve", "improved", "innovative", "positive", "support", "supports", "effective", "growth", "achieved", "won"}
_NEGATIVE_WORDS = {"bad", "poor", "fail", "failed", "failure", "harm", "harmful", "risk", "risky", "problem", "problems", "decline", "negative", "crisis", "damage", "damaged", "difficult", "loss", "lost", "concern", "concerns"}
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Transparent lexicon baseline; this is not a trained sentiment model."""
    tokens = [token.lower() for token in _TOKEN_RE.findall(text)]
    positive = sum(token in _POSITIVE_WORDS for token in tokens)
    negative = sum(token in _NEGATIVE_WORDS for token in tokens)
    # A simple nearby negation rule prevents common inversions from being ignored.
    for i, token in enumerate(tokens):
        if token in _POSITIVE_WORDS and any(w in {"not", "never", "no"} for w in tokens[max(0, i-3):i]):
            positive -= 1; negative += 1
        elif token in _NEGATIVE_WORDS and any(w in {"not", "never", "no"} for w in tokens[max(0, i-3):i]):
            negative -= 1; positive += 1
    total = positive + negative
    score = round((positive - negative) / max(total, 1), 3)
    label = "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"
    return {"label": label, "score": score, "positive_terms": max(0, positive), "negative_terms": max(0, negative), "method": "transparent_lexicon_baseline"}


_STOP_WORDS = {"the", "and", "for", "are", "was", "were", "with", "that", "this", "from", "into", "their", "they", "have", "has", "had", "but", "not", "you", "its", "his", "her", "who", "what", "where", "when", "which", "will", "would", "could", "should", "about", "after", "before", "over", "under", "than", "then", "there", "here", "been", "being", "also", "more", "most", "some", "such", "each", "while", "because", "through", "during", "between", "within", "company", "said"}


def tokenize(text: str) -> list[str]:
    return [w.lower() for w in _TOKEN_RE.findall(text) if len(w) > 2 and w.lower() not in _STOP_WORDS]


def tfidf_features(sentences: list[str], max_terms: int = 12) -> dict[str, Any]:
    """Small-corpus TF-IDF using smoothed IDF; no external service required."""
    docs = [tokenize(s) for s in sentences]
    df = Counter(term for doc in docs for term in set(doc))
    n = len(docs)
    terms = sorted(df, key=lambda term: (df[term], term), reverse=True)[:max_terms]
    ranked = []
    for term in terms:
        tf_values = [doc.count(term) / max(len(doc), 1) for doc in docs]
        idf = 1 + math.log((1 + n) / (1 + df[term]))
        ranked.append({"term": term, "score": round(max(tf_values, default=0) * idf, 4), "document_frequency": df[term]})
    return {"method": "tf_idf", "document_count": n, "vocabulary_size": len(df), "top_terms": sorted(ranked, key=lambda x: x["score"], reverse=True)}


def topic_model(corpus: list[dict[str, Any]], topic_count: int = 3, iterations: int = 20) -> list[dict[str, Any]]:
    """Collapsed-Gibbs LDA across available analyzed documents (max 12 sessions)."""
    # Bound work for long uploads and keep interactive analysis responsive.
    docs = [tokenize(" ".join(item.get("sentences", [])))[:1800] for item in corpus]
    vocab = sorted({word for doc in docs for word in doc})
    if len(vocab) < 2 or len([d for d in docs if d]) < 2:
        return []
    word_id = {word: i for i, word in enumerate(vocab)}
    tokens = [[word_id[w] for w in doc] for doc in docs]
    k = min(topic_count, 3, len(vocab), max(2, len([d for d in docs if d])))
    rng = random.Random(17)
    alpha, beta = 0.1, 0.01
    z = [[rng.randrange(k) for _ in doc] for doc in tokens]
    ndk = [[0] * k for _ in docs]
    nkw = [[0] * len(vocab) for _ in range(k)]
    nk = [0] * k
    for di, doc in enumerate(tokens):
        for wi, topic in zip(doc, z[di]):
            ndk[di][topic] += 1; nkw[topic][wi] += 1; nk[topic] += 1
    for _ in range(iterations):
        for di, doc in enumerate(tokens):
            for ti, wi in enumerate(doc):
                old = z[di][ti]
                ndk[di][old] -= 1; nkw[old][wi] -= 1; nk[old] -= 1
                probs = [(ndk[di][t] + alpha) * (nkw[t][wi] + beta) / (nk[t] + beta * len(vocab)) for t in range(k)]
                draw = rng.random() * sum(probs); new = k - 1
                for t, prob in enumerate(probs):
                    draw -= prob
                    if draw <= 0:
                        new = t; break
                z[di][ti] = new
                ndk[di][new] += 1; nkw[new][wi] += 1; nk[new] += 1
    out = []
    for topic in range(k):
        top = sorted(range(len(vocab)), key=lambda wi: nkw[topic][wi], reverse=True)[:5]
        related = []
        for di, assignments in enumerate(z):
            count = assignments.count(topic)
            if count and count / len(assignments) >= 0.15:
                related.append({"filename": corpus[di]["filename"], "weight": round(count / len(assignments), 3)})
        out.append({"topic": topic + 1, "terms": [vocab[i] for i in top if nkw[topic][i]], "documents": related})
    return out

