#!/usr/bin/env python3
"""

"""
import codecs
import re



def main():
    with codecs.open("subtitles.log", 'r', "utf-8") as f:
        for line in f:
            print(line)

if __name__ == "__main__":
    main()




