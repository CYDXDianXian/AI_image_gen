import unicodedata
# import ahocorasick
from .config import get_config

wordlist = get_config('ban_word', 'wordlist')

def guolv(sent=str):
    sent_cp = unicodedata.normalize('NFKC', sent) # 中文标点转为英文
    sent_cp = sent_cp.lower() #转为小写
    sent_cp = sent_cp.replace('&shape=portrait', '&shape=Portrait')
    sent_cp = sent_cp.replace('&shape=landscape', '&shape=Landscape')
    sent_cp = sent_cp.replace('&shape=square', '&shape=Square')
    sent_list_ = sent_cp.split(",") # 从逗号处分开，返回列表
    
    sent_list = []
    for m in sent_list_:
        sent_list.append(m.strip()) # 移除空格

    # 生成过滤词列表
    tags_guolu_list = []
    for i in sent_list:
        i_list = i.split(" ")
        for o in i_list:
            if o.strip() in wordlist:
                tags_guolu_list.append(i)
    
    # 移除发送列表中的违禁词
    for j in tags_guolu_list:
        sent_list.remove(j)

    # 将过滤后的列表拼接为字符串
    sent_str = ",".join(sent_list)
    tags_guolu = ",".join(tags_guolu_list)
    return sent_str, tags_guolu

# def build_actree(wordlist):
#     actree = ahocorasick.Automaton()
#     for index, word in enumerate(wordlist):
#         actree.add_word(word, (index, word))
#     actree.make_automaton()
#     return actree

# def guolv(sent):
#     words = wordlist
#     actree = build_actree(wordlist=words)
#     sent_cp = sent.lower() #转为小写
#     tags_guolu = ""
#     for i in actree.iter(sent):
#         sent_cp = sent_cp.replace(i[1][1], "")
#         tags_guolu += str(i[1][1]) + " "
#     sent_cp = sent_cp.replace("landscape", "Landscape")
#     sent_cp = sent_cp.replace("portrait", "Portrait")
#     sent_cp = sent_cp.replace("square", "Square")
#     return sent_cp,tags_guolu