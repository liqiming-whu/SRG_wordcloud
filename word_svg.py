#!/usr/bin/env python3
"""
Symbol, Species, Number, RGB, Sex
"""
import re


class SVG:
    def __init__(self, path):
        self.svg = path

    def iter(self):
        line_gen = open(self.svg)
        for line in line_gen:
            if line.startswith("<text"):
                yield line

    def to_dict(self, males, females):
        word_rgb = dict()
        word_patter = re.compile('>([^<]+)<')
        rgb_patter = re.compile('"fill:([^"]+)"')

        for line in self.iter():
            word = word_patter.findall(line)[0]
            rgb = rgb_patter.findall(line)[0]
            if word in males:
                rgb = 'rgb(116, 173, 209)'
            if word in females:
                rgb = 'rgb(244, 109, 67)'
            word_rgb[word] = rgb

        return word_rgb
