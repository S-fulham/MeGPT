import re
import json
import os
from collections import Counter
from textstat import textstat

PROFILE_PATH = "profile_data.json"

STOPWORDS = {
    "the","and","is","in","to","of","a","that","it","on",
    "for","as","with","was","were","be","by","this","are",
    "or","an","at","from"
}


def analyze_text(text: str):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]

    paragraphs = [p for p in text.split("\n") if p.strip()]

    words = re.findall(r'\b\w+\b', text.lower())

    bigrams = zip(words, words[1:])
    bigram_freq = Counter([" ".join(b) for b in bigrams])

    stopword_count = sum(1 for word in words if word in STOPWORDS)

    total_sentences = len(sentences)
    total_words = len(words)
    total_characters = sum(len(word) for word in words)
    total_paragraphs = len(paragraphs)

    readability = textstat.flesch_reading_ease(text)

    return {
        "total_sentences": total_sentences,
        "total_words": total_words,
        "total_characters": total_characters,
        "total_paragraphs": total_paragraphs,
        "stopword_count": stopword_count,
        "readability": readability,
        "word_freq": Counter(words),
        "bigram_freq": bigram_freq,
        "punctuation": Counter(re.findall(r'[^\w\s]', text))
    }


def load_profile():
    if not os.path.exists(PROFILE_PATH):
        return None

    with open(PROFILE_PATH, "r") as f:
        data = json.load(f)

    data["word_freq"] = Counter(data["word_freq"])
    data["bigram_freq"] = Counter(data["bigram_freq"])
    data["punctuation"] = Counter(data["punctuation"])

    return data


def save_profile(profile):
    profile_to_save = profile.copy()
    profile_to_save["word_freq"] = dict(profile["word_freq"])
    profile_to_save["bigram_freq"] = dict(profile["bigram_freq"])
    profile_to_save["punctuation"] = dict(profile["punctuation"])

    with open(PROFILE_PATH, "w") as f:
        json.dump(profile_to_save, f, indent=4)


def update_profile(texts: list):
    existing_profile = load_profile()

    if not existing_profile:
        existing_profile = {
            "total_texts": 0,
            "total_sentences": 0,
            "total_words": 0,
            "total_characters": 0,
            "total_paragraphs": 0,
            "total_readability": 0,
            "total_stopwords": 0,
            "word_freq": Counter(),
            "bigram_freq": Counter(),
            "punctuation": Counter()
        }

    for text in texts:
        analysis = analyze_text(text)

        existing_profile["total_texts"] += 1
        existing_profile["total_sentences"] += analysis["total_sentences"]
        existing_profile["total_words"] += analysis["total_words"]
        existing_profile["total_characters"] += analysis["total_characters"]
        existing_profile["total_paragraphs"] += analysis["total_paragraphs"]
        existing_profile["total_readability"] += analysis["readability"]
        existing_profile["total_stopwords"] += analysis["stopword_count"]

        existing_profile["word_freq"] += analysis["word_freq"]
        existing_profile["bigram_freq"] += analysis["bigram_freq"]
        existing_profile["punctuation"] += analysis["punctuation"]

    save_profile(existing_profile)

    return build_readable_profile(existing_profile)


def build_readable_profile(profile):
    avg_sentence_length = (
        profile["total_words"] / profile["total_sentences"]
        if profile["total_sentences"] else 0
    )

    avg_word_length = (
        profile["total_characters"] / profile["total_words"]
        if profile["total_words"] else 0
    )

    avg_readability = (
        profile["total_readability"] / profile["total_texts"]
        if profile["total_texts"] else 0
    )

    avg_paragraph_length = (
        profile["total_words"] / profile["total_paragraphs"]
        if profile["total_paragraphs"] else 0
    )

    stopword_ratio = (
        profile["total_stopwords"] / profile["total_words"]
        if profile["total_words"] else 0
    )

    vocabulary_richness = (
        len(profile["word_freq"]) / profile["total_words"]
        if profile["total_words"] else 0
    )

    return {
        "total_texts": profile["total_texts"],
        "avg_sentence_length": round(avg_sentence_length, 2),
        "avg_word_length": round(avg_word_length, 2),
        "avg_paragraph_length": round(avg_paragraph_length, 2),
        "avg_readability": round(avg_readability, 2),
        "vocabulary_richness": round(vocabulary_richness, 4),
        "stopword_ratio": round(stopword_ratio, 4),
        "top_10_words": profile["word_freq"].most_common(10),
        "top_10_bigrams": profile["bigram_freq"].most_common(10),
        "punctuation_usage": dict(profile["punctuation"])
    }


def get_profile():
    profile = load_profile()
    if not profile:
        return {"message": "No profile created yet."}

    return build_readable_profile(profile)


def reset_profile():
    if os.path.exists(PROFILE_PATH):
        os.remove(PROFILE_PATH)

    return {"message": "Profile reset successfully."}