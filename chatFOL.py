import argparse
import spacy
import nltk
from spacy import displacy
from nltk import load_parser
from nltk.corpus import wordnet
# from spacy.matcher import PhraseMatcher
# from nltk.stem import WordNetLemmatizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest = "file", nargs="?")
    args = parser.parse_args()

    nlp = spacy.load("en_core_web_sm")
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
    return word_list

def translate_line(sentence, nlp):
    word_list = preprocess(sentence, nlp)
    print(word_list)
    count = 0
    final_string = ""
    # find number of verbs / adjs in sentence
    for (lemma, pos) in word_list:
        if pos == 'VERB' or pos == 'ADJ':
            count += 1
    if count == 0: # no clear descriptor -> look into auxillaries
        for i, (lemma, pos) in enumerate(word_list):
            if pos == 'AUX':
                if lemma == 'be': # be, is, are
                    N1 = None
                    N2 = get_antecedent(word_list, i)[0]
                    if word_list[i-1][1] == 'CCONJ' or word_list[i-2][1] == 'CCONJ': # ___ CCONJ (DET) N2 -> must be another noun 
                        N1 = get_antecedent(word_list, i-1)[0]
                    # get following noun
                    for j in range(i, len(word_list)):
                        if word_list[j][1] == 'NOUN':
                            if N1:
                                final_string += f"{word_list[j][0]}({N1}, {N2})"
                            else:
                                final_string += f"{word_list[j][0]}({N2})"
    elif count == 1:
        i, verb = [(i, v) for i, (v, pos) in enumerate(word_list) if pos == 'VERB' or pos == 'ADJ'][0]
        N1 = None
        N2 = None
        if i > 0:
            N2_pos = get_antecedent(word_list, i)
            N2 = N2_pos[0]
            if word_list[ word_list.index(N2_pos) -1][1] == 'CCONJ' or word_list[word_list.index(N2_pos)-2][1] == 'CCONJ': # ___ CCONJ (DET) N2 -> must be another noun 
                N1 = get_antecedent(word_list, word_list.index(N2_pos) -1)[0]
        if N1 == None:
            N1 = N2
            N2 = None
        if i < len(word_list) - 1:
            N2 = get_subsequent(word_list, i)[0]
        if N1 and N2:
            final_string += f"{verb}({N1}, {N2})"
        elif N1:
            final_string += f"{verb}({N1})"
        elif N2:
            final_string += f"{verb}({N2})"


    # elif count == 2: # look at conjunctions
    return final_string

def get_antecedent(word_list, idx):
    # go backwards from the idx until we find a noun and return it
    for i in range(idx - 1, -1, -1):
        lemma, pos = word_list[i]
        if pos == "NOUN" or pos == "PROPN":
            return (lemma, pos)
    return None

def get_subsequent(word_list, idx):
    # go forwards from the idx until we find a noun and return it
    for i in range(idx + 1, len(word_list)):
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