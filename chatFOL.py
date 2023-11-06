import argparse
import spacy
import nltk
import random
from spacy import displacy
from nltk import load_parser
from nltk.corpus import wordnet
import spacy_transformers
# from spacy.matcher import PhraseMatcher
# from nltk.stem import WordNetLemmatizer

used_variables = []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest = "file", nargs="?")
    args = parser.parse_args()

    nlp = spacy.load("en_core_web_trf")
    if args.file: # if text file is provided as an argument
        try:
            with open(args.file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    original_line = line.strip()
                    word_list = preprocess(original_line, nlp)
                    #print(word_list)
                    translated_line = translate_line(word_list)
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
            word_list = preprocess(user_input, nlp)
            #print(word_list)
            translated_line = translate_line(word_list)
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
            if (idx+1 < len(word_list) and word_list[idx + 1][0] == "not"):
                word_list[idx], word_list[idx+1] = word_list[idx + 1], word_list[idx]
        elif lemma == "who" or lemma== "too":
            word_list[idx] = get_antecedent(word_list, idx)
        elif lemma in ["he", "she", "her", "him", "herself", "himself"]:
            word_list[idx] = get_first_noun(word_list, idx)
    return word_list

def translate_line(word_list):
    used_variables = []
    count = 0
    print(word_list)
    for i, (lemma, pos) in enumerate(word_list):
        if lemma == 'someone' or lemma == 'somebody':
            return get_quantifier_loops(word_list, i, f'exist {get_variable()}.')
        if lemma == 'nobody' or (lemma == 'no' and word_list[i+1][0] == 'one'):
            return get_quantifier_loops(word_list, i, f'-exist {get_variable()}.')
        if lemma == 'everyone':
            return get_quantifier_loops(word_list, i, f'all {get_variable()}.')
        # if lemma == 'exactly' and word_list[i+1][0] == 'one':
        #     word_list[i] = ('x', 'NOUN')
        #     return 'all x. ()'
        # If “Exactly one” N AUX ADJ/VB:
        # 		All x ( exists y. ADJ/VB(y) &  -exists z. (ADJ/VB((z) & -(z =y)) )

    # find number of verbs / adjs in sentence
    for (lemma, pos) in word_list:
        if pos == 'VERB' or pos == 'ADJ':
            count += 1
    print("count = "+ str(count))
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
                                return f"{word_list[j][0]}({N1}, {N2})"
                            else:
                                return f"{word_list[j][0]}({N2})"
    elif count == 1:
        i, verb = [(i, v) for i, (v, pos) in enumerate(word_list) if pos == 'VERB' or pos == 'ADJ'][0]
        N1 = None
        N2 = None
        if i > 0: # if the verb is not the very first word
            N2_pos = get_antecedent(word_list, i) # get noun in front of verb
            if N2_pos:
                N2 = N2_pos[0]
                if word_list[ word_list.index(N2_pos) -1][1] == 'CCONJ' or word_list[word_list.index(N2_pos)-2][1] == 'CCONJ': # ___ CCONJ (DET) N2 -> must be another noun 
                    N1 = get_antecedent(word_list, word_list.index(N2_pos) -1)[0]
        if N1 == None:
            N1 = N2
            N2 = None
        if i < len(word_list) - 1:
            N2 = get_subsequent(word_list, i)
            if N2:
                N2 = N2[0]
        if N1 and N2:
            return f"{verb}({N1}, {N2})"
        elif N1:
            return f"{verb}({N1})"
        elif N2:
            return f"{verb}({N2})"

    # elif count == 2: # look at conjunctions
    #     conj_map = {"but": "&", "and": "&", "or": "|", "if": "->"}
    #     conj = get_conjunction(word_list)
    #     word = conj[0] # the word
    #     i = conj[2] #the index of the conj returned from get_conjunction()
    #     return translate_line(word_list[:i], nlp) + " " + conj_map[word] + " " + translate_line(word_list[i+1:], nlp)

    # return final_string

def get_variable():
    randomVar = chr(random.randint(ord('a'), ord('z')))
    if randomVar not in used_variables:
        used_variables.append(randomVar)
        return randomVar
    else:
        return get_variable()        

def get_quantifier_loops(word_list, i, quantifier):
    word_list[i] = (quantifier[-2], 'NOUN')
    #still need to translate anything before word and anything after
    if get_antecedent(word_list, i) and get_subsequent(word_list,i):
        return quantifier + translate_line(word_list[:i+1]) + translate_line(word_list[i+1:])
    # if at end of chunk or entire sentence, finish translating the sentence in front
    elif i == len(word_list)-1 or get_antecedent(word_list,i):
        return quantifier + translate_line(word_list[:i+1])
    # if at beginning of chunk or entire sentence, finish translating the sentence in back
    elif i == 0 or get_subsequent(word_list, i):
        return quantifier + translate_line(word_list[i:])

def get_antecedent(word_list, idx):
    # go backwards from the idx until we find a noun and return it
    for i in range(idx - 1, -1, -1):
        lemma, pos = word_list[i]
        if pos == "NOUN" or pos == "PROPN" or pos == "PRON":
            return (lemma, pos)
    return None

def get_subsequent(word_list, idx):
    # go forwards from the idx until we find a noun and return it
    for i in range(idx + 1, len(word_list)):
        lemma, pos = word_list[i]
        if pos == "NOUN" or pos == "PROPN" or pos == "PRON":
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

def get_conjunction(word_list):
    for i in range(0, len(word_list)):
        lemma, pos = word_list[i]
        if pos == "CCONJ":
            return (lemma, pos, i)
    return None

if __name__ == "__main__":
    main()