from nltk.tokenize import word_tokenize
import app 

def rephrase(sent):
    words = []
    for s in word_tokenize(sent):
        if not s in set('[|]|{|}'.split('|')):
            if s[0]== '+' and s[-1] =='+':
                words.append(s[1:-1])
            elif s[0]=='-' and s[-1] == '-':
                continue
            else:
                words.append(s)
    return words


def geniatag(line):
    taggers = app.tagger.parse(line)
    a = []
    b = []
    c = []
    d = []
    tmp = []
    for parse in taggers:
        a.append([parse[0]])
        b.append([parse[1]])
        c.append([parse[2]])
        d.append([parse[3]])
    tmp.append(a)
    tmp.append(b)
    tmp.append(c)
    tmp.append(d)
    return tmp
