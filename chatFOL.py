import argparse
import spacy
from spacy import displacy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest = "file", nargs="?")
    args = parser.parse_args()

    if args.file: # if text file is provided as an argument
        try:
            with open(args.file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    original_line = line.strip()
                    translated_line = translate_line(original_line)
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
            translated_line = translate_line(user_input)
            print(f"Translated: {translated_line}")

def translate_line(original_line):
    # get parts of speech
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(original_line)
    for token in doc:
        print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_)
    
    options = {"compact": True, "add_lemma": True}
    displacy.serve(doc, auto_select_port=True)
    displacy.serve(doc, style="dep", options = options)

if __name__ == "__main__":
    main()