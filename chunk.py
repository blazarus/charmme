from nltk.chunk import RegexpParser
from nltk import pos_tag
from csc.nl import get_nl
en_nl = get_nl('en')

parser = RegexpParser(
'''
NP: {<JJ.*>* <NN.*>+}                # compound noun (including proper)
NP: {<VBN.*>+ <NP>}                  # modifier + noun
NP: {<NP> <IN> <DT>? <NP>}           # noun with preposition
''')

demo_text = '''
When people communicate, they rely on a large body of shared common sense knowledge in order to understand each other. Many barriers we face today in artificial intelligence and user interface design are due to the fact that computers do not share this knowledge. To improve computers' understanding of the world that people live in and talk about, we need to provide them with usable knowledge about the basic relationships between things that nearly every person knows.

In 1999, we began a project at the MIT Media Lab to collect common sense from volunteers on the internet. Ten years later our project has expanded to encompass many different areas, languages, and problems. Currently, the English site has over a million sentences from over 15,000 contributors.
'''

def np_chunk(text):
    tokens = en_nl.tokenize(text).split()
    chunked = parser.parse(pos_tag(tokens))
    return chunked

def extract_noun_phrases(text):
    chunked = np_chunk(text)
    for tree in chunked.subtrees():
        if tree.node == 'NP':
            flat = [leaf[0] for leaf in tree.flatten()]
            yield en_nl.untokenize(' '.join(flat))

if __name__ == '__main__':
    for np in extract_noun_phrases(demo_text):
        print np
        
