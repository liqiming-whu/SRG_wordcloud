import os
from collections import Counter
from generate_stopwords import clean_str

SPECIES = [line.rstrip().split(",")[0] for line in open(os.path.join("data", "species.csv"))]
NAMES = [line.rstrip().split(",")[1] for line in open(os.path.join("data", "species.csv"))]
GENES = open(os.path.join("data", "gene.txt"), encoding="utf-8").read().split()
DRUGS = open(os.path.join("data", "drugs.txt"), encoding="utf-8").read().split()


def contain_binary_phrase(text):
    for species in SPECIES:
        species_connect = species.replace(" ", "_")
        text = text.replace(species, species_connect)
    for name in NAMES:
        name_connect = name.lower().replace(" ", "_")
        text = text.replace(name, name_connect)
        text = text.replace(name.lower(), name_connect)
    return text


def process_freq_dict(freq_dict, filename):
    words_freq_dir = os.path.join("results", "words_freq")
    if os.path.exists(words_freq_dir):
        os.mkdir(words_freq_dir)
    if not freq_dict:
        freq_tsv_dir = os.path.join("results", "freq_tsv")
        if not os.path.exists(freq_tsv_dir):
            os.mkdir(freq_tsv_dir)
        freq_tsv = os.path.join(freq_tsv_dir, filename+".tsv")
        whitelist_dir = os.path.join("data", "whitelist_species", filename)
        if not os.path.exists(whitelist_dir):
            return None
        male = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "male.txt"))]
        female = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "female.txt"))]
        with open(freq_tsv, "w", encoding="utf-8") as f:
            for word in male:
                f.write(word + "\t1\tmale\n")
            for word in female:
                f.write(word + "\t1\tfemale\n")
        return dict((i, 1) for i in male+female)

    species_stopwords = os.path.join("data", "stopwords_species", filename+".txt")
    if os.path.exists(species_stopwords):
        StopWords = open(species_stopwords).read().split("\n")
        freq_dict = dict(i for i in freq_dict.items() if i[0] not in StopWords)
    whitelist_dir = os.path.join("data", "whitelist_species", filename)
    if not os.path.exists(whitelist_dir):
        freq_tsv_dir = os.path.join("results", "freq_tsv")
        if not os.path.exists(freq_tsv_dir):
            os.mkdir(freq_tsv_dir)
        freq_tsv = os.path.join(freq_tsv_dir, filename+".tsv")
        with open(freq_tsv, "w", encoding="utf-8") as f:
            for word, count in freq_dict.items():
                f.write("{}\t{}\tNA\n".format(word, count))
        return freq_dict
    freq = list(freq_dict.items())
    male = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "male.txt"))]
    female = [i.rstrip("\n").strip('"') for i in open(os.path.join(whitelist_dir, "female.txt"))]
    add = [(i, 1) for i in male+female if i not in freq_dict.keys()]
    words_count = len(freq) + len(add)
    if words_count <= 200:
        freq = freq + add
    if words_count > 200:
        freq = freq[:200-words_count] + add
    assert len(freq) <= 200
    freq_tsv_dir = os.path.join("results", "freq_tsv")
    if not os.path.exists(freq_tsv_dir):
        os.mkdir(freq_tsv_dir)
    freq_tsv = os.path.join(freq_tsv_dir, filename+".tsv")

    with open(freq_tsv, "w", encoding="utf-8") as f:
        for word, count in freq:
            if word in male:
                f.write("{}\t{}\tmale\n".format(word, count))
            elif word in female:
                f.write("{}\t{}\tfemale\n".format(word, count))
            else:
                f.write("{}\t{}\tNA\n".format(word, count))
    return dict(freq)


def process_word_freq(word_freq, filename):
    if not word_freq:
        return process_freq_dict(None, filename)
    print("word_freq length: ", len(word_freq))
    uniq = Counter(word.lower() for word in word_freq)
    duplicate = [word for word, freq in uniq.items() if freq > 1]
    remove = Counter()
    add = Counter()
    for word in duplicate:
        freq = 0
        order = 0
        for key in word_freq.keys():
            if key.lower() == word:
                order += 1
                if order == 1:
                    add_key = key
                freq += word_freq[key]
                remove[key] = word_freq[key]
        add[add_key] = freq
    word_freq = word_freq - remove + add
    high_frep = word_freq.most_common(200)
    low_freq = [(key, value) for (key, value) in word_freq.most_common() if (key, value) not in high_frep]
    genes_drugs = [(word, freq) for (word, freq) in low_freq if word in GENES or word in DRUGS]
    freq = word_freq.most_common(200 - len(genes_drugs)) + genes_drugs

    freq_dict = dict((word.replace("_", " "), count) for word, count in freq)

    return process_freq_dict(freq_dict, filename)


def process_text(text):
    text = clean_str(text)
    return contain_binary_phrase(text)
