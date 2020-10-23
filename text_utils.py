import os


SPECIES = [line.rstrip().split(",")[0] for line in open(os.path.join("data", "species.csv"))]
GENES = [line.rstrip() for line in open(os.path.join("data", "gene.txt"))]
DRUGS = [line.rstrip() for line in open(os.path.join("data", "drugs.txt"))]


def contain_binary_phrase(text):
    for species in SPECIES:
        species_connect = species.replace(" ", "_")
        text = text.replace(species, species_connect)
    return text
