import os
import re
from collections import Counter
from generate_stopwords import clean_str

SPECIES = [line.rstrip().split(",")[0] for line in open(os.path.join("data", "species.csv"))]
NAMES = [line.rstrip().split(",")[1] for line in open(os.path.join("data", "species.csv"))]
GENES = [line.rstrip() for line in open(os.path.join("data", "gene.txt"))]
DRUGS = [line.rstrip() for line in open(os.path.join("data", "drugs.txt"))]


def contain_binary_phrase(text):
    for species in SPECIES:
        species_connect = species.replace(" ", "_")
        text = text.replace(species, species_connect)
    for name in NAMES:
        name_connect = name.lower().replace(" ", "_")
        text = text.replace(name, name_connect)
        text = text.replace(name.lower(), name_connect)
    return text


def process_word_freq(word_freq):
    uniq = Counter(word.lower() for word in word_freq)
    duplicate = [word for word, freq in uniq.items() if freq > 1]
    remove = Counter()
    add = Counter()
    for word in duplicate:
        freq = 0
        for key in word_freq.keys():
            if key.lower() == word:
                freq += word_freq[key]
                remove[key] = word_freq[key]
        add[word] = freq
    word_freq = word_freq - remove + add
    high_frep = word_freq.most_common(200)
    low_freq = [(key, value) for (key, value) in word_freq.most_common() if (key, value) not in high_frep]
    genes_drugs = [(word, freq) for (word, freq) in low_freq if word in GENES or word in DRUGS]
    freq = word_freq.most_common(200 - len(genes_drugs)) + genes_drugs
    words_f = dict()

    for word, count in freq:
        if str(re.match("\d+", word)) == 'None':
            words_f[word.replace("_", " ")] = count

    return words_f


def process_text(text):
    while text != clean_str(text):
        text = clean_str(text)
    return contain_binary_phrase(text)
