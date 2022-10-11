import ahocorasick
from .config import get_config

wordlist = get_config('ban_word', 'wordlist')
def build_actree(wordlist):
    actree = ahocorasick.Automaton()
    for index, word in enumerate(wordlist):
        actree.add_word(word, (index, word))
    actree.make_automaton()
    return actree

def guolv(sent):
    words = wordlist
    actree = build_actree(wordlist=words)
    sent_cp = sent.lower() #转为小写
    tags_guolu = ""
    for i in actree.iter(sent):
        sent_cp = sent_cp.replace(i[1][1], "")
        tags_guolu += str(i[1][1]) + " "
    sent_cp = sent_cp.replace("landscape", "Landscape")
    sent_cp = sent_cp.replace("portrait", "Portrait")
    sent_cp = sent_cp.replace("square", "Square")
    return sent_cp,tags_guolu