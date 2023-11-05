import argparse
import spacy
import nltk
from spacy import displacy
from nltk import load_parser
from spacy.matcher import PhraseMatcher
from nltk.stem import WordNetLemmatizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest = "file", nargs="?")
    args = parser.parse_args()

    nlp = spacy.load("en_core_web_sm")
    nltk.download('wordnet')

    if args.file: # if text file is provided as an argument
        try:
            with open(args.file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    original_line = line.strip()
                    translated_line = translate_line(original_line, nlp)
                    print(f"Translated: {translated_line}\n")
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
    else: # interactive mode
        while True:
            user_input = input("] ")
            if not user_input:
                print("Please enter an input. Type q, Q, quit or QUIT to exit.")
                break
            if user_input.lower() in ["q", "quit"]:
                break
            translated_line = translate_line(user_input, nlp)
            print(f"Translated: {translated_line}")

def translate_line(sentence, nlp):
    word_list = preprocess(sentence, nlp)

def preprocess(sentence, nlp):
    doc = nlp(sentence)
    # returns a nested list of form [[word, POS]...]
    # lemmatize the verbs, removes determiners and punctuation
    word_list = [(token.lemma_, token.pos_) for token in doc if token.pos_ != "PUNCT"]
    # replace "who", pronouns and "do" with the things they refer too
    for idx, (lemma, pos) in enumerate(word_list):
        if lemma == "do":
            word_list[idx] = get_closest_verb(word_list, idx)[0]
        elif lemma == "who" or lemma== "too":
            word_list[idx] = get_antecedent(word_list, idx)
        elif lemma in ["he", "she", "her", "him", "herself", "himself"]:
            word_list[idx] = get_first_noun(word_list, idx)
    print(word_list)
    return word_list

def get_antecedent(word_list, idx):
    for i in range(idx - 1, -1, -1):
        lemma, pos = word_list[i]
        if pos == "NOUN" or pos == "PROPN":
            return (lemma, pos)
    return None

def get_closest_verb(word_list, idx):
    # go backwards from the idx until we find a verb and return it
    for i in range(idx-1, -1, -1):
        if word_list[i] and word_list[i][1] == "VERB":
            return (word_list[i], word_list[i+1])
    return None
    
def get_first_noun(word_list, idx):
    for i in range(0, len(word_list)):
        lemma, pos = word_list[i]
        if pos == "NOUN" or pos == "PROPN":
            return (lemma, pos)
    return None

if __name__ == "__main__":
    main()