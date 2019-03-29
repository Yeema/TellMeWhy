# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify
from nltk.stem import WordNetLemmatizer
import spacy
import operator
from nltk.stem.lancaster import LancasterStemmer
from collections import Counter,defaultdict
import geniatagger
from geniatagger import GeniaTagger
from nltk import word_tokenize, pos_tag
from nltk.stem import WordNetLemmatizer
import re
import spacy
from nltk.tokenize import sent_tokenize,word_tokenize
import requests
import json

GEC_API = 'https://whisky.nlplab.cc/translate/?text={}'
ab = re.compile(r"\w*'\w*|\w*’\w*")
loss_del = re.compile(r'\[ *- *([^\[\]]*?) *- *\]')
loss_add = re.compile(r'\{\ *\+ *([^\[\]]*?) *\+ *\}')
delandadd = re.compile(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}')
deletion = re.compile(r'\[- *([^\[\]]*?) *-\]')
addition = re.compile(r'\{\+ *([^\[\]]*?) *\+\}')
braces = re.compile(r'\[ *(.*?) *\]')
multi_delandadd = re.compile(r'(\[-([^\[\]]*?)-\] *\{\+([^\{\}]*?)\+\} *)+')

app = Flask(__name__)
tagger = GeniaTagger('/home/nlplab/yeema/geniataggerPython/geniatagger-3.0.2/geniatagger')
wordnet_lemmatizer = WordNetLemmatizer()
nlp = spacy.load('en')

dictWord = defaultdict(lambda: defaultdict(list))
phraseV = defaultdict(lambda: defaultdict(list))
dictPhrase = defaultdict(lambda: defaultdict(list))
dictDef = defaultdict(lambda: defaultdict(list))
miniparCol = defaultdict(lambda: defaultdict(lambda: Counter()))
pw = defaultdict(lambda: defaultdict(lambda:Counter()))
pw_ratio = defaultdict(lambda: defaultdict(lambda:Counter()))

@app.route('/')	
def index():
    return render_template('template.html')

@app.route('/query', methods=['POST'])
def query_entry():
    text = request.form['text_field']
    print("GET HTTP POST REQUEST:", text)
    text = beautify(text)
    result = defaultdict(lambda: defaultdict())
    explain(text,result,'explain')
    res = {}
    htmlize(result,res,'Example')
    return jsonify(res)

@app.route('/color',methods = ['POST'])
def query_color():
    string = request.form['sent']
    pos = request.form['pos']
    pos = [int(p) for p in pos.split('\t')]
    if pos[1]<len(string):
        return string[:pos[0]]+'<span style="color:red">%s</span>'%string[pos[0]:pos[1]]+string[pos[1]:]

@app.route('/GEC',methods=['POST'])
def query_GEC():
    string = request.form['sent']
    edits = requests.get(GEC_API.format(string))
    edits = eval(edits.text)
    # correction = edits['word_diff']
    correction = edits['word_diff_by_sent']
    res = {}
    if correction:
        correction = beautify(correction[0])
        result = defaultdict(lambda: defaultdict())
        explain(correction,result,'GEC')
        htmlize(result,res,'GEC')
    return jsonify(res)

def htmlize(result,res,mode):
    myPanel = ''
#     {'a':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','b':'<ul><li>'+'</li><li>'.join(['bbb','bbbb']),'c':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','d':'<ul><li>'+'</li><li>'.join(['bbb','bbbb']),'e':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','f':'<ul><li>'+'</li><li>'.join(['bbb','bbbb'])}
    for id,mod in result.items():
        # res['%d\tpos'%(id)] = '%d\t%d'%(mod['pos'][0],mod['pos'][1])
        tmp = '<ul><li> %s </li></ul>'%('</li><li>'.join([r for r in mod['body'] if r.replace('<p></p>','').strip()]))
        myPanel += '<div class="card shadow-sm rounded bg-white">'+'<div class="card-header" id="heading%d">'%(id)+'<h2 class="mb-0">'+'<button class="btn collapsed" type="button" data-toggle="collapse" data-target="#collapse%d" aria-expanded="false" aria-controls="collapse%d" data-edit="edit%d">'%(id,id,id)+'%s'%(mod['header'])+ '</button>'+'</h2>'+'</div>'+'<div id="collapse%d" class="collapse" aria-labelledby="heading%d" data-parent="#accordion%s" data-edit="edit%d">'%(id,id,mode,id)+'<div class="card-body">'+'%s'%(tmp)+'</div>'+'</div>'+'</div>'

    res['sent'] = result[0]['sent']
    res['html'] = myPanel.replace('<li></li>','')


dictDet = {'some' :"<b>Some</b> is usually used to show that there is a quantity of something or a number of things or people, without being precise. It is used with uncountable nouns and plural countable nouns.",
'a2some' : "When you want to emphasize that you do not know the identity of a person or thing, or you think their identity is not important, you can use <b>some</b> with a sigular countable noun, instead of a or an.",
'any' : "<b>Any</b> is used before pluarl nouns and uncountable nouns when you are refferring to or asking whether a quantity of something that may or may not exist.",
'another' : "<b>Another</b> is used with singular countable nouns to talk about an additional person or thing of the same type as you have already mentioned.",
'other' : "<b>Other</b> is used with plural nouns, or occasionally with uncountable nouns.",
'enough' : "<b>Enough</b> is used to say that there is as much of something as is needed, or as many things as are needed. You can therefore use enough in front of uncountable nounds or plural nouns.",
'few' : "When you want to emphasize that there is only a samll number of things of a particular kind, you use <b>few</b> with a plural countable noun.",
'many' : "<b>Many</b> indicates that there is a large number of things, without being very precise. You use <b>many</b> with a plural countable noun.",
'most' : "<b>Most</b> indicates nearly all of a group or amount. You use <b>most</b> with an uncountable noun or a plural countable noun.",
'several' : "<b>Several</b> usually indicates an imprecise number that is not very large, but it is more than two. You use <b>several</b> with a plural countable noun.",
'all' : "<b>All</b> includes every person or thing of a particaular kind. You use <b>all</b> with an uncountable noun or a plural countable noun.",
'both' : "<b>Both</b> is used to say something about two people or things of the same kind. You use both with a plural countable noun." ,
'either' : "<b>Either</b> is used to talk about two things, but usaully indicates that only one of the two is invloved. You use either with a singular countable noun.",
'each' : "<b>Each</b> is used when you are thinking about the members as individuals. You use <b>each</b> with a singular countable noun.",
'every' : "<b>Every</b> is used when you are making a general statement about all of them. You use <b>every</b> with a singular countbale noun.",
'little' : "<b>Little</b> is used to emphasize only a small amount of something. You use <b>little</b> with uncountable nouns.",
'much' : "<b>Much</b> is used to emphasize a large amount. You use <b>much</b> with uncountable nouns.",
'this' : "<b>This</b> is used to talk about people or things that are very obvious in the situation that you are in.",
'these' :  "<b>There</b> is used to talk about people or things that are very obvious in the situation that you are in. You use <b>these</b> with a plural countable noun.",
'that' : "<b>That</b> is used to  talk about people or things that are you can see but that are not very cloased to you.",
'those' : "<b>Those</b> is used to  talk about people or things that are you can see but that are not very cloased to you. You use <b>those</b> with a plural countable noun.",
'the':"<b>The</b> is used before a noun when <b>a</b> has been mentioned or nouns are sprecific names or proper nouns.",
'a':"<b>A<b> is used for talking about a person or thing when it is not important or not clear.",
'an':"<b>An<b> is used for talking about a person or thing when it is not important or not clear."}

verbpat =  ['V that', 'V n that', 'V n', 'V pron-refl', 'V n of n', 'V n to inf', 'V in n', 'V wh', 'V adv',\
'V n from n', 'V pron-refl with n', 'V pron-refl by n', 'V n adj', 'V for n', 'V n in n', \
'V to inf', 'V n for n', 'V to n', 'V on n', 'be V-ed in n', 'be V-ed as n', 'be V-ed with n',\
'V with n', 'be V-ed on n', 'V n with n', 'V through n', 'V n by n', 'V into n',\
'V across n', 'V around n', 'V n on n', 'V -ing', 'V from n', 'V after n', 'V n to n', \
'V pron-refl to n', 'V at n', 'V n at n', 'V n n', 'V n into n', 'be V-ed of n', 'V of n',\
'V n against n', 'V by n', 'V pron-refl out', 'V n as n', 'V over n', 'V n -ing', 'V n through n',\
'V against n', 'V adj', 'be V-ed of', 'V n out', 'V n up', 'V about n', 'V that n inf', \
'V pron-refl up', 'be V-ed to n', 'be V-ed n', 'be V-ed adj', 'V inf', 'V n inf', 'V n about n', \
'V n over n', 'V toward n', 'V towards n', 'be V-ed against n', 'be V-ed at n', 'V off n', \
'V behind n', 'V pron-refl on n', 'V pron-refl for n', 'V out of n', 'be V-ed amount', \
'be V-ed to', 'V under n', 'be V-ed into n', 'V amount', 'be V-ed with', 'V pron-refl in n', \
'V among n', 'V as n', 'V n off', 'V pron-refl at n', 'be V-ed from n', 'be V-ed for n', 'V n under n',\
'V pron-refl from n', 'V pron-refl off', 'be V-ed across n', 'V n without n', 'V n toward n', \
'V between n', 'be V-ed over n', 'be V-ed to inf', 'V n after n', 'V n across n', 'be V-ed against', \
'V n down', 'be V-ed as', 'be V-ed for', 'V pron-refl into n', 'V n off n', 'V without n', 'be V-ed off n', \
'V pron-refl of n', 'be V-ed about n', 'be V-ed that', 'V n among n', 'be V-ed about', \
'V pron-refl against n', 'V n between n', 'V n around n', 'V pron-refl as n', 'be V-ed by', 'be V-ed after n',\
'be V-ed by n', 'be V-ed on', 'be V-ed among n', 'be V-ed between n', 'be V-ed at',\
'be V-ed around n', 'V n behind n', 'V pron-refl down', 'be V-ed in', 'be V-ed under n', \
'be V-ed without n', 'be V-ed through', 'be V-ed after', 'be V-ed through n', 'V n towards n',\
'V pron-refl off n', 'V pron-refl between n']+\
['V wh n','V n wh','V wh to inf']
verbpat.extend([v.replace('wh',tar) for v in set([v for v in verbpat if 'wh' in v]) for tar in ['how' , 'who' , 'what', 'when','why','where']])
verbpat = set(verbpat)
nounpat = ['adj N', 'with N', 'from N', 'n N', 'to N', '(v) N in n', 'into N', 'v N with n', \
               '(v) N of n', 'amount N', '(v) N to n', 'in N', '(v) N on n', 'on N', 'at N', 'N of n', \
               '(v) N into n', 'N as n', '(v) N with n', '(v) N from n', '(v) N for n', 'N in n', 'v N over n', \
               'N for -ing', 'N to inf', 'N to n', 'v N in n', 'without N', 'N from n', 'v N about n', 'under N', \
               'N to -ing', 'N on n', 'v N from n', 'v N between n', '(v) N over n', 'N for n', 'in N of n', \
               '(v) N through n', '(v) N toward n', '(v) N against n', '(v) N towards n', 'N that', 'on N of n',\
               '(v) N at n', '(v) N between n', 'v N by n', 'v N through n', '(v) N around n', 'v N for n', \
               '(v) N about n', 'v N on n', 'v N of n', 'v N without n', 'N with n', '(v) N among n', 'N by n', \
               'N about n', 'N through n', '(v) N behind n', '(v) N as n', 'v N as n', 'N among n', '(v) N by n', \
               'v N against n', 'N about -ing', 'N around n', 'v N across n', 'N at n', 'N between n', 'v N to n', \
               'N over n', 'N toward n', 'v N at n', 'N in -ing', 'v N into n', 'v N off n', 'N against n', 'N into n',\
               'N across n', 'v N toward n', 'N under n', 'v N after n', 'v N among n', 'v as N', 'v N under n', \
               '(v) in N', 'N on -ing', 'N behind n', '(v) N across n', 'v N around n', '(v) N under n', 'N from -ing', 'v N out n'] + \
             ['N %s wh to inf'% pg for pg in ['in','of','on']]
nounpat.extend([v.replace('wh',tar) for v in set([v for v in nounpat if 'wh' in v]) for tar in ['how' , 'who' , 'what', 'when','why','where']])
nounpat = set(nounpat)
adjpat = ['ADJ n', 'ADJ to n', 'ADJ and adj', 'n ADJ', 'ADJ that', 'ADJ in n', 'ADJ about n', 'n N', 'N at n', \
             'ADJ for n', 'ADJ with n', 'ADJ to inf', 'ADJ on n', 'ADJ as n', 'adj N', 'ADJ into n', 'ADJ of n', \
             'amount N', 'ADJ toward n', 'N to n', 'amount ADJ', 'ADJ from n', 'ADJ at n', 'N of n', 'ADJ by n',\
             'ADJ against n', 'ADJ among n', 'ADJ in n with n', 'ADJ -ing', 'ADJ through n', 'N from n', 'ADJ over n',\
             'ADJ wh', 'ADJ without n', 'ADJ under n', 'N on n', 'N in n', 'of N', 'N with n', 'ADJ between n', 'N as n',\
             'N among n', 'ADJ on n for n', 'N by n', 'ADJ in n from n', 'ADJ to n for n', 'ADJ after n', 'N behind n', \
             'N through n', 'ADJ around n', 'N over n', 'N for n', 'N after n', 'ADJ across n']

selfWords = {'oneself', 'myself', 'ourselves', 'yourself', 'himself', 'herself', 'themselves','me','him','you','her','them','it'}
pgPreps = 'under|without|around|round|in_favor_of|_|about|after|against|among|as|at|between|behind|by|for|from|in|into|of|on|upon|over|through|to|toward|forward|off|on|across|towards|with|out'.split('|')
otherPreps ='out|off|down|up|across'.split('|')
reserveWord = {'for', 'over', 'at', 'about', 'up', 'by', 'under', 'among', 'on', 'out', 'that', 'against', 'of', 'in', 'amount', 'to', 'between', 'toward', 'towards', 'down', 'from', 'as', 'through', 'around', 'and', 'off', 'into', 'without', 'with', 'after', 'across', 'behind'}
allreserved = set()
allreserved = allreserved.union(set(pgPreps) , set(otherPreps) , reserveWord)
pos_map = {'N':'N','J':'ADJ','V':'V','A':'ADJ'}
det_s = set("a,an,this,that,each,every,either,another,the,no".split(','))
det_p = set("the,some,these,those,much,many,any,all,most,enough,several,other,few,both".split(','))
MONTH = set("january,february,march,april,may,june,july,august,september,october,november,december".split(','))
WEATHER = set("spring,summer,fall,autumn,winter".split(","))
DATES = set("monday,tuesday,wednesday,thursday,friday,saturday,sunnday".split(","))
HOLIDAY = set("christmas,easter,hannukkah,ramadan".split(","))
CLOCKTIME = set("midnight/noon/dawn/lunch".split('/'))
POD = set("morning/afternoon/evening".split("/"))
mapHead = dict( [('H-NP', 'N'), ('H-VP', 'V'), ('H-ADJP', 'ADJ'), ('H-ADVP', 'ADV'), ('H-VB', 'V')] )
mapRest = dict( [('VBG', '-ing'), ('VBD', 'v-ed'), ('VBN', 'v-ed'), ('VB', 'v'), ('NN', 'n'), ('NNS', 'n'), ('JJ', 'adj'), ('RB', 'adv'),('NP', 'n'), ('VP', 'v'), ('JP', 'adj'), ('ADJP', 'adj'), ('ADVP', 'adv'), ('SBAR', 'that')] )
modeMap = {'V':'V','J':'ADJ','N':'N'}
vowel = set([i for i in 'aeiouh'])
vowelMap = {'a':['apple','apartment'],'e':['elephant','element'],'i':['igloo','island'],'o':['oven','octopus'],'u':['umbrella','unexpected error'],'h':['hour','honour']}
TIME = set(list(MONTH)+\
                list(WEATHER)+\
                list(DATES)+\
                list(HOLIDAY)+\
                list(CLOCKTIME)+\
                list(POD)+\
                ['weekend','weekends'])
maxDegree = 9
tmp_abbrs = {'it’s':'it is','what’s':'what is','how’s':'how is','they’re':'they are','we’re':'we are','i’m':'I am','don’t':'do not','doesn’t':'does not','didn’t':'did not','won’t':'will not','hadn’t':'had not','haven’t':'have not','wouldn’t':'would not','couldn’t':'could not','can’t':'can not','shouldn’t':'should not'}
abbrs = defaultdict()
for key,val in tmp_abbrs.items():
    abbrs[key.replace("’","'")] = val
    abbrs[key] = val
aux = set([('will','would'),('can','could'),('shall','should'),('may','might')])
str_example = '<div class="px-2 py-1 mt-2 text-monospace"><p>%s</p></div>'
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

def simplify(pat):
    i=0
    for p in pat[::-1]:
        if p=='adv':
            i-=1
        else:
            break
    return pat[:i]

def sentence_to_ngram(words, lemmas, tags, chunks): 
    return [ (k, k+degree) for k in range(0,len(words)) for degree in range(1, min(maxDegree, len(words)-k+1)) ]

def hasTwoObjs(tag, chunk):
    if chunk[-1] != 'H-NP': return False
    return (len(tag) > 1 and tag[0] in pronOBJ) or (len(tag) > 1 and 'DT' in tag[1:])
def chunk_to_element(words, lemmas, tags, chunks, i, isHead):
    if isHead:
        if len(chunks[i][-1])>3:
            # print('chunk',chunks[i][-1])
            if lemmas[i-1][-1] =='be' and tags[i][0]=='VBN': return 'V-ed'
            elif tags[i][-1][0] in ['V','N']:
                return tags[i][-1][0] 
            elif tags[i][-1][0]=='J':
                return 'ADJ'
            elif lemmas[i][-1] in pgPreps:
                return lemmas[i][-1]
    if tags[i][-1] == 'DT': return ""
    if lemmas[i-1][-1]=="to" and tags[i][0]=='VB': return 'inf'
    if lemmas[i][-1].lower() in reserveWord: return lemmas[i][0].lower() 
    if lemmas[i][-1].lower()  == 'be': return 'be'
    if lemmas[i][-1].lower()  in ['how' , 'who' , 'what', 'when','why','where'] : return lemmas[i][-1].lower()
    if chunks[i][0][2:5]=='ADV': return 'adv'
    if chunks[i][0]=='I-ADJP': return 'adj'
    if lemmas[i][-1] in selfWords : return 'pron-refl'
    if tags[i-1][0]=='V' and lemmas[i][0]=='VB': return 'inf'
    if  lemmas[i-2][0]+" "+tags[i][0]== "that N" and lemmas[i][0] =='VB': return 'inf'
    if tags[i][0] == 'VBG': return '-ing'
    if tags[i][0] == 'CD': return 'amount'
    if tags[i][0]=='J': return 'adj'
    if tags[i][0]=='V': return 'v'
    if tags[i][0]=='N': return 'n'
    if tags[i][0]=='PRP': return 'n'
    if tags[i][0] == 'PRP$': return 'adj'
    if lemmas[i][0] == 'favour' and words[i-1][-1]=='in' and words[i+1][0]=='of': return 'favour'
    if tags[i][-1] == 'RP' and tags[i-1][-1][:2] == 'VB':                return '_'
    if tags[i][0]=='CD': return 'amount'
    if hasTwoObjs(tags[i], chunks[i]):                                              return 'n n'
    if tags[i][-1] in mapRest:                            return mapRest[tags[i][-1]]
    if tags[i][-1][:2] in mapRest:                        return mapRest[tags[i][-1][:2]]
    if chunks[i][-1] in mapHead:                            return mapHead[chunks[i][-1]].lower()
    if lemmas[i][-1] in pgPreps:                                         return lemmas[i][-1]
    return lemmas[i][-1]

def simplifyPat(pat): 
    if pat == 'V ,':
        return 'V'
    elif pat =='N ,':
        return 'N'
    elif pat =='J ,':
        return 'ADJ'
    else:
        return pat.replace(' _', '').replace('_', ' ').replace('  ', ' ')

def ngram_to_pat(words, lemmas, tags, chunks, start, end):
    pat, doneHead = [], False
    head_pos = start
    change_start = False
    for i in range(start, end):
        isHead = tags[i][-1][0] in ['V','J','N'] and not doneHead
        if isHead:
            if tags[i][-1][0]=='V':
                if lemmas[i][-1] =='be' and tags[i+1][0]=='VBN':
                    isHead = False
            elif tags[i][-1][0]=='N':
                if i>0:
                    if tags[i-1][-1][0]=='V': pat.append('(v)')
                    if tags[i-1][-1][0]=='J': 
#                         change_start = True
                        pat.append('adj')
            else:
                isHead = not lemmas[start][-1].lower() in pgPreps
        pat.append( chunk_to_element(words, lemmas, tags, chunks, i, isHead) )
        if isHead: doneHead = True
        else:
            if not doneHead: head_pos+=1

    pat = simplifyPat(' '.join(pat))
    tmp_pat= []
    for p in pat.split():
        if not tmp_pat:
            tmp_pat.append(p)
        else:
            if p!=tmp_pat[-1]:
                tmp_pat.append(p)
    if head_pos<end:
        pat = pat.replace('adj n','n')
        if isverbpat(lemmas[head_pos][0],pat):
            mode = 'V'
            return pat,head_pos,change_start
        elif isverbpat(lemmas[head_pos][0],pat.replace('wh','n')):
            mode = 'V'
            return pat,head_pos,change_start
        elif isverbpat(lemmas[head_pos][0],pat.replace('and','').replace('adj n','n')):
            mode = 'V'
            return pat.replace('and','').replace('adj n','n'),head_pos,change_start
        elif isverbpat(lemmas[head_pos][0],pat.replace('and','').replace('adj n','n')):
            mode = 'V'
            return pat.replace('and','').replace('adj n','n'),head_pos,change_start
        elif isverbpat(lemmas[head_pos][0],pat.replace('pron-refl','n').replace('adj n','n')):
            mode = 'V'
            return pat.replace('adj n','n'),head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat):
            mode = 'N'
            return pat,head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('-ing','n')):
            mode = 'N'
            return pat,head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('wh','n')):
            mode = 'N'
            return pat,head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('amount N','n N')):
            mode = 'N'
            return pat[4:].replace('adv','').replace('amount N','n N'),head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('amount N','N')):
            mode = 'N'
            return pat[4:].replace('amount N','N'),head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('amount N','N')):
            mode = 'N'
            return pat.replace('adv','').replace('amount N','N'),head_pos,change_start
        elif pat[:3] =='(n)' and isnounpat(lemmas[head_pos][0],pat[4:].replace('amount N','n N')):#(n)
            mode = 'N'
            return pat[4:].replace('amount N','n N'),head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('adj N','N')):
            mode = 'N'
            return pat.replace('adj N','N'),head_pos,change_start
        elif isnounpat(lemmas[head_pos][0],pat.replace('what','n')):
            mode = 'N'
            return pat.replace('what','n'),head_pos,change_start
        elif isadjpat(lemmas[head_pos][0],pat):
            mode = 'ADJ'
            return pat,head_pos,change_start
        elif isadjpat(lemmas[head_pos][0],pat.replace('-ing','n')):
            mode = 'ADJ'
            return pat,head_pos,change_start
        elif isadjpat(lemmas[head_pos][0],pat.replace('wh','n')):
            mode = 'ADJ'
            return pat,head_pos,change_start
        elif isadjpat(lemmas[head_pos][0],pat.replace('amount N','n N')):
            mode = 'ADJ'
            return pat[4:].replace('amount N','n N'),head_pos,change_start
        elif isadjpat(lemmas[head_pos][0],pat.replace('amount N','N')):
            mode = 'ADJ'
            return pat[4:].replace('amount N','N'),head_pos,change_start
        elif pat[:3] =='(n)' and isadjpat(lemmas[head_pos][0],pat[4:].replace('amount N','n N')):#(n)
            mode = 'ADJ'
            return pat[4:].replace('amount N','n N'),head_pos,change_start
    return "" ,start,change_start

def isverbpat(key,pat):
    pat = ' '.join(pat.split())
    return  pat in verbpat

def isnounpat(key,pat):
    pat = ' '.join(pat.split())
    return pat in nounpat

def isadjpat(key,pat):
    pat = ' '.join(pat.split())
    return pat in adjpat

def ngram_to_head(words, lemmas, tags, chunks, start, end,real_start):
    for i in range(start, end):
        if tags[i][-1][0] in ['V','N','J']:  
            return modeMap[tags[i][-1][0]],lemmas[i][-1].upper(),words[real_start:end]
    return "",""

def geniatag(line):
    taggers = tagger.parse(line)
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

def find_patterns(parse,target):
    tmp = []
    for start, end in sentence_to_ngram(*parse):
        pat, head_pos,change_start = ngram_to_pat(*parse, start, end) 
        if pat:
            if change_start:
                start -= 1
            mode,head,sent = ngram_to_head(*parse, head_pos, end,start)
            pat = ' '.join(pat.split())
            head = head.lower()
            pat_example = ' '.join([s[0] for s in sent])
            whs = [wh for wh in ['how' , 'who' , 'what', 'when','why','where'] if wh in pat]
            if whs:
                for wh in whs:
                    tmp.append([pat.replace(wh,'wh'),head,mode,pat_example])
            if any([t for t in target if re.findall(r'\b' + re.escape(t)+r'\b', pat_example)]):
#                 if any([pat[0].split("%")[0] for pat in dictWord[mode][head]]):
                    tmp.append([pat,head,mode,pat_example])
    return tmp

def find_phrases(patterns,head,part):
    output_phrases = []
    for pattern in patterns:
        words = word_tokenize(pattern)
        words = ' '.join([w for w in words if w in allreserved or w==part]).replace(part,head)
        output_phrases.extend([phrase for phrase in phraseV[head].keys() if phrase.split('%')[0] == words])
    return set(output_phrases)

def find_meaning(lista,listb,a,b):
    worda = []
    wordb = []
#     print(list(dicta.values()))
    if not [t[1].strip() for t in lista if t[1].strip()] :
        worda.append(a)
    else:
        worda = [la[1].replace('SOMETHING','').replace('THING','').strip() for la in lista if la[1].replace('SOMETHING','').replace('THING','')]
    if not [t[1].strip() for t in listb if t[1].strip()]:
        wordb.append(b)
    else:
        wordb = [la[1].replace('SOMETHING','').replace('THING','').strip() for la in listb if la[1].replace('SOMETHING','').replace('THING','')]
   
    index, _ = max(enumerate( [nlp(wa.lower())[0].similarity(nlp(wb.lower())[0]) for wa in worda for wb in wordb]), key=operator.itemgetter(1))
    if len(lista[int(index/len(wordb))][2][0]) == 2:
        eng = lista[int(index/len(wordb))][2][0][0]
        ch = " ( "+lista[int(index/len(wordb))][2][0][1] +" )"
    else:
        eng = lista[int(index/len(wordb))][2][0][1]
        ch = " ( "+lista[int(index/len(wordb))][2][0][2] +" )"
    if braces.search(eng):
            eng = eng.replace(braces.search(eng)[0],'') 
    attra = eng+ch
    
    if len(listb[index%len(wordb)][2][0]) == 2:
        eng = listb[index%len(wordb)][2][0][0]
        ch = " ( "+ listb[index%len(wordb)][2][0][1]+" )"
    else:
        eng = listb[index%len(wordb)][2][0][1]
        ch = " ( "+ listb[index%len(wordb)][2][0][2]+" )"
    if braces.search(eng):
            eng = eng.replace(braces.search(eng)[0],'')
    attrb = eng + ch
    return attra,attrb

def explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part):
    output = []
    output.append('It is a semantic error.')
    listd = dictDef[d_lemma][d_part.upper()]
    lista = dictDef[a_lemma][a_part.upper()]
    if not listd:
        listd = dictDef[d_lemma]['']
    if not lista:
        lista = dictDef[a_lemma]['']
    if listd and lista:
        delmeaning,addmeaning = find_meaning(listd,lista,d_lemma,a_lemma)
        tmp = []
        if delmeaning:
            tmp.append('<b>%s</b> :\t%s.'%(d_lemma,delmeaning))
        if addmeaning:
            tmp.append("<b>%s</b> :\t%s."%(a_lemma,addmeaning))
        if tmp:
            output.append("<br>%s</br>"%('</br><br>'.join(tmp)))
        
    return '<p>'+'</p><p>'.join(output)+'</p>'

def explain_VT_error(head,correction,pattern,ex):
    output = []
    head = head.lower()
    if dictDef[head]:
        Ts = []
        Is = []
        emp = []
        for  df in dictDef[head]['V']:
            if 'T' in df[0]:
                Ts.append(merge_def(df))
            elif 'I' in df[0]:
                Is.append(merge_def(df))
            elif not df[0]:
                emp.append(merge_def(df))
        if Ts and not Is and not emp:
            output.append("For all the situations, the verb <b>%s</b> is not followed by a preposition <b>%s</b> because <b>%s</b> is a transitive verb."%(head,deletion.search(correction).group(1),head))
        elif Ts and Is:
            output.append("The verb <b>%s</b> can be both transitive and intransitive verb. When it means %s, it is a transitive verb. However, when it describes that %s, it represents a intransitive verb."%(head,' or '.join(Ts[:2]),' or '.join(Is[:2])))
        elif emp:
            output.append("Normally, the verb <b>%s</b> is not followed by a preposition <b>%s</b> because <b>%s</b> is a transitive verb. Besides, it means %s."%(head,deletion.search(correction).group(1),head,emp[0]))
        tmp = explain_pattern(ex,head,'V',pattern)
        if type(tmp) == list:
            output.extend(tmp)
        else:
            output.append(tmp)
    else:
        output.append("Normally, the verb <b>%s</b> is not followed by a preposition <b>%s</b> because <b>%s</b> is a transitive verb."%(head,deletion.search(correction).group(1),head))
        tmp = explain_pattern(ex,head,'V',pattern)
        if type(tmp) == list:
            output.extend(tmp)
        else:
            output.append(tmp)
    return '<br>'.join(output)
        
def explain_VI_error(head,correction,pattern,ex):
    output = []
    head = head.lower()
    if dictDef[head]:
        Ts = []
        Is = []
        emp = []
        for  df in dictDef[head]['V']:
            if 'I' in df[0]:
                Is.append(merge_def(df))
            if 'T' in df[0]:
                Ts.append(merge_def(df))
                
        if Is and not Ts:
            output.append("The verb <b>%s</b> is absolutely an intransitive verb and it means %s."%(head,' or '.join(Is[:2])))
        elif Ts:
            output.append("The verb <b>%s</b> is an intransitive verb here which means %s. However, it can be transitive sometimes depending on the scenerio."%(head,' or '.join(Is[:2])))
        else:
            output.append("Normally, the verb <b>%s</b> is necessarily followed by a preposition <b>%s</b> because <b>%s</b> is a intransitive verb."%(head,addition.search(correction).group(1),head))
            tmp = explain_pattern(ex,head,'V',pattern)
            if type(tmp) == list:
                output.extend(tmp)
            else:
                output.append(tmp)
    return '<br>'.join(output)

            
def merge_def(df):
    defsent = ' '.join(df[2][0][:-1]).strip()
    defsent += ' ( '+df[2][0][-1].strip()+' )'
    if braces.search(defsent):
        idx = defsent.find(braces.search(defsent).group(0))
        if idx == 0:
            defsent = defsent.replace(braces.search(defsent).group(0),"").strip()
            return defsent
        else:
            return defsent
    else:
        return defsent
    
def find_N_meaning(head,isUncount = False):
    output = []
    head = head.lower()
    if dictDef[head]:
        Cs = []
        Us = []
        emp = []
        for  df in dictDef[head]['N']:
            part_ = [d.strip() for d in ' '.join([braces.search(d).group(1) for d in df[2][0] if braces.search(d)]).split('or') if d.strip()]
            if isUncount:
                if 'U' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Us.append(def_sent)
                elif 'C' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Cs.append(def_sent)
                elif 'PLURAL' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Cs.append(def_sent)
                elif not part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        emp.append(def_sent)
            else:
                if 'C' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Cs.append(def_sent)
                elif 'U' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Us.append(def_sent)
                elif 'PLURAL' in part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        Cs.append(def_sent)
                elif not part_:
                    def_sent = merge_def(df)
                    if def_sent:
                        emp.append(def_sent)
#         print(Cs,Us,emp)
        if isUncount:
            if Us and not Cs:
                output.append("The noun <b>%s</b> is uncountable all the time. It means %s which describes relatively abstract concept."%(head,' or '.join(Us[:2])))
            elif Us and Cs:
                output.append("The noun <b>%s</b> can be both countable and uncountable which depends on its definition. When it means %s, it expresses an abstract concept so it is uncountable for sure. However, when it explians %s, it represents a countable noun."%(head,' or '.join(Us),' or '.join(Cs)))
            elif emp:
                output.append("The noun <b>%s</b> is uncountable because it descibes relatively abstract concept that <b>%s</b>."%(head,' or '.join(emp[:2])))
        else:
            if Cs and not Us:
                output.append("The noun <b>%s</b> is countable all the time. It means %s which describes relatively abstract concept."%(head,' or '.join(Cs[:2])))
            elif Us and Cs:
                output.append("The noun <b>%s</b> can be both countable and uncountable which depends on its definition. When it means %s, it expresses an abstract concept so it is uncountable for sure. However, when it explians %s, it represents a countable noun."%(head,' or '.join(Us),' or '.join(Cs)))
            elif emp:
                output.append("The noun <b>%s</b> is countable when it means <b>%s</b>."%(head,' or '.join(emp[:2])))
    return '<p>'+'</p><p>'.join(output)+'</p>'

def check_uncountable(head):
    head = head.lower()
    if dictDef[head]:
        for  df in dictDef[head]['N']:
            part_ = [d.strip() for d in ' '.join([braces.search(d).group(1) for d in df[2][0] if braces.search(d)]).split('or') if d.strip()]
            if 'U' in part_:
                return True
    return False

def my_lemma(correction,entails_sent):
    delset = []
    delword = []
    if deletion.search(correction):
        head = deletion.search(correction).group(1)
        entails_sent = correction.replace(deletion.search(correction).group(0),head)
        tags = geniatag(entails_sent)
    else:
        head = addition.search(correction).group(1)
        tags = geniatag(' '.join(entails_sent))
    idx = [t[0] for t in tags[0]].index(head)
    
    return tags[1][idx][0],tags[2][idx][0]

def find_voc_meaning(head,part):
    output = []
    part = part.upper()
    mapp_ = {'V':'verb','N':'noun','ADJ':'adjective','C':'countable','U':'uncountable','PLURAL':'usually in plural format','I':'intransitive','T':'transitive'}
    head = head.lower()
    if dictDef[head] and dictDef[head][part]:
#         find alternative part description
        is_mapp_ = set([mapp_[ex] for exs in dictDef[head][part] for ex in exs[0] if ex in mapp_])
#         output.append(head,part,dictDef[head][part][0][2])
        eng = dictDef[head][part][0][2][0][0].strip()
        if braces.search(eng):
            eng = eng.replace(braces.search(eng)[0],'')
        ch = '( '+dictDef[head][part][0][2][0][1] + ' )'
        if is_mapp_:
            if 'uncountable' in is_mapp_:
                output.append("<b>%s</b> can be %s %s which means '%s.''"%(head,' and '.join(is_mapp_),mapp_[part],eng+ch ))
            else:
                output.append(is_mapp_)
                output.append("<b>%s</b> is %s %s which means '%s.'"%(head,' and '.join(is_mapp_),mapp_[part],eng+ch))
        else:
            if 'A' in is_mapp_:
                output.append("<b>%s</b> can be %s which means '%s.'"%(head,mapp_[part],eng+ch))
            else:
                output.append("<b>%s</b> can be %s which means '%s.'"%(head,mapp_[part],eng+ch))
    return '<p>'+'</p><p>'.join(output)+'</p>'

def explain_pattern(ex,head,part,pattern):
#     [['N on how to inf%0', [], ['And , yes , I do send the parents home with instructions on how to use the drops if need be .', '', '']]]
    output = []
    if pattern == ex[0].split('%')[0]:
        if pattern[-1].isupper():
            tmp = []
            tmp.append('The usage of <b>%s</b> is <b>%s</b>.'%(head,pattern))
            tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
            output.append('<br>'.join(tmp))
        else:
            tmp = []
            tmp.append('The usage of <b>%s</b> is <b>%s</b>.'%(head,pattern.replace(part,head)))
            tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
            output.append('<br>'.join(tmp))
    else:
        tmp = []
        if ex[0].split('%')[0].replace(part,head)[:3] != '(v)':
            tmp.append('The usage of <b>%s</b> is <b>%s</b>.'%(head,'" or "'.join([ex[0].split('%')[0].replace(part,head),pattern.replace(part,head)])))
        else:
            tmp.append('The usage of <b>%s</b> is <b>%s</b>.'%(head,ex[0].split('%')[0].replace(part,head)))
        tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
        output.append('br'.join(tmp))
    if miniparCol[head][ex[0].split('%')[0]]:
        _pos = {'ADJ':'adjective','V':'verb','N':'noun'}
        if output:
            output[-1] += "<li>Besides, it is often paired the %s <b>%s</b> with vocabularies such as <b>%s</b>.</li>"%(_pos[part],head,','.join([v[0] for v in miniparCol[head][ex[0].split('%')[0]].most_common(3)]))
        else:
            output.append("Besides, it is often paired the %s <b>%s</b> with vocabularies such as <b>%s</b>."%(_pos[part],head,','.join([v[0] for v in miniparCol[head][ex[0].split('%')[0]].most_common(3)])))
        return output
    return '<p>'+'</p><p>'.join(output)+'</p>'

def select_examples(pattern,head,part):
    res = [item for item in dictWord[part][head] if pattern == item[0].split('%')[0]]
    if res:
        return res
    res = [item for item in dictWord[part][head] if pattern== item[0].split('%')[0].replace('(v)','').strip() or pattern.replace('-ing','n')== item[0].split('%')[0].replace('(v)','').strip() or pattern.replace('pron-refl','n') == item[0].split('%')[0]]
    return res

def find_nextword(entails_sent,target,pos = ''):
    idx = entails_sent.index(target)
    default_idx = idx+1
    default = entails_sent[default_idx]
    tagging = geniatag(' '.join(entails_sent))
    if not pos:
        return default,tagging[1][default_idx][0]
    else:
        while(idx+1 < len(entails_sent)):
            if tagging[2][idx][0][0] == pos:
                return entails_sent[idx],tagging[1][idx][0]
            else:
                idx += 1
        return default,tagging[1][default_idx][0]
    
def find_idx(tagging,target):
    words = [key[0] for key in tagging[0]]
    lemmas = [key[0] for key in tagging[1]]
    tags = [key[0] for key in tagging[2]]
    if target in words:
        return words.index(target),words,lemmas,tags
    else:
        tmp = ' '.join(words)
        idx = tmp.find(target)
        return len(tmp[:idx].strip().split()),words,lemmas,tags

def find_idioms(entails_sent,target):
    tagging = geniatag(' '.join(entails_sent))
    done = False
    if len(target) == 1:
        idx,words,lemmas,tags = find_idx(tagging,target[0])
        phrase = target[0]
        while idx >0:
            idx -= 1
            if tags[idx][0] in ['V','N','J'] or lemmas[idx] in allreserved:
                head = lemmas[idx]
                phrase = head +' '+ phrase
                if dictPhrase[phrase]:
                    done = True
                    break
    else:
        for t in target:
            if not done:
                idx,words,lemmas,tags = find_idx(tagging,target[0].split()[0])
                phrase = t
            while idx >0 and not done:
                idx -= 1
                if tags[idx][0] in ['V','N','J'] or lemmas[idx] in allreserved:
                    head = lemmas[idx]
                    phrase = head +' '+ phrase
                    if dictPhrase[phrase]:
                        done = True
                        break
    if done:
        return phrase,head
    else:
        return '',''

def find_idioms_from_gps(gps):
    output = []
    for  pattern , head , part , _,_ in gps[::-1]:
        if phraseV[head]:
            phrases = find_phrases([pattern],head,part)
            if phrases:
                for phrase in phrases:
                    if phrase.split('%')[0] in dictPhrase:
                        output.append('<b>%s</b> is a phrase which means <b>%s</b>.'%(phrase.split('%')[0],' '.join(list(dictPhrase[phrase.split('%')[0]].values())[0][0])))
                    if  '  '.join(phraseV[head][phrase][0][2][:2]):
                        output.append(str_example%("For example: %s"%('  '.join(phraseV[head][phrase][0][2][:2]))))
    return '<p>'+'</p><p>'.join(output)+'</p>'
                        
def compare_lemma(correction):
    dels = deletion.search(correction)
    adds = addition.search(correction)
    
    d_tar = dels.group(1)
    a_tar = adds.group(1)
    
    before = ' '.join(correction.replace(dels.group(0),dels.group(1)).replace(adds.group(0),'').split())
    after = ' '.join(correction.replace(adds.group(0),adds.group(1)).replace(dels.group(0),'').split())
    
    before = geniatag(before)
    after = geniatag(after)
    idx,words,lemmas,tags = find_idx(before,d_tar)
    if tags[idx][0] == 'J':
        d = words[idx],lemmas[idx],'ADJ'
    else:
        d = words[idx],lemmas[idx],tags[idx][0]
    idx,words,lemmas,tags = find_idx(after,a_tar)
    if tags[idx][0] == 'J':
        a = words[idx],lemmas[idx],'ADJ'
    else:
        a = words[idx],lemmas[idx],tags[idx][0]
    return d,a

def find_collocations(gps,tagging,a_lemma,d_lemma):
    output = []
    for gp in gps[::-1]:
        pattern = ' '.join([g for g in gp[0].replace('(v)','').split() if g.strip()])
        if len(pattern.split()) == 3 or pattern == 'V n':
            headword, pos, sent = gp[1:]
            idx,words,lemmas,tags = find_idx(tagging,sent.split()[-1])
            tail = lemmas[idx]
            if headword == a_lemma:
                if miniparCol[a_lemma][pattern][lemmas[idx]] and miniparCol[d_lemma][pattern][lemmas[idx]]:
                    if pattern == 'V n':
                        col = ' '.join([a_lemma,tail])
                        wcol = ' '.join([d_lemma,tail])
                    else:
                        prep = pattern.split()[1] 
                        col = ' '.join([a_lemma,prep,tail])
                        wcol = ' '.join([d_lemma,prep,tail])
                    percentage = miniparCol[a_lemma][pattern][tail] / (miniparCol[a_lemma][pattern][tail] + miniparCol[d_lemma][pattern][tail])
                    output.append('<b>%s</b> is a more common collocation than <b>%s</b>.'%(col,wcol))
                    output.append('The probability of using <b>%s</b> is %s%s.'%(col,"{:3.2f}".format(percentage*100),'%'))
                elif miniparCol[headword][pattern][a_lemma]:
                    if pattern == 'V n':
                        col = ' '.join([headword,a_lemma])
                        wcol = ' '.join([headword,d_lemma])
                    else:
                        prep = pattern.split()[1] 
                        col = ' '.join([headword,prep,a_lemma])
                        wcol = ' '.join([headword,prep,d_lemma])
                        output.append('People always use <b>%s</b>. It is impossible to use <b>%s</b>'%(col,wcol))
            else:
                if miniparCol[headword][pattern][a_lemma] and miniparCol[headword][pattern][d_lemma]:
                    if pattern == 'V n':
                        col = ' '.join([headword,a_lemma])
                        wcol = ' '.join([headword,d_lemma])
                    else:
                        col = ' '.join([headword,pattern.split()[1],a_lemma])
                        wcol = ' '.join([headword,pattern.split()[1],d_lemma])
                    percentage = miniparCol[headword][pattern][a_lemma] / (miniparCol[headword][pattern][a_lemma] + miniparCol[headword][pattern][d_lemma])
                    output.append('<b>%s</b> is a more common collocation than <b>%s</b>.'%(col,wcol))
                    output.append('The probability of using <b>%s</b> is %s%s.'%(col,"{:3.2f}".format(percentage*100),'%'))
                elif miniparCol[headword][pattern][a_lemma]:
                    if pattern == 'V n':
                        col = headword + a_lemma
                    else:
                        col = headword + ' ' +pattern.split()[1] + ' ' + a_lemma
                        wcol = headword + ' ' +pattern.split()[1] + ' ' + d_lemma
                        output.append('People always use <b>%s</b>. It is impossible to use <b>%s</b>'%(col,wcol))
    return '<br>'+'</br><br>'.join(output)+'</br>'
def explain_INF():
    inf = "When verbs followed by a to-infinitive often indicate the intention of an action or a future event."
    ing = "Compare: Verbs followed by an <b>-ing<b> form often emphasize on a status, fact, or activity."
    return "<br>"+inf+"</br><br>"+ing+"</br>"
def explain_INF():
    ing = "when verbs followed by an <b>-ing<b> form often emphasize on a status, fact, or activity."
    inf = "Compare: Verbs followed by a to-infinitive often indicate the intention of an action or a future event."
    return "<br>"+ing+"</br><br>"+inf+"</br>"
def check_P(word,lemma):
    word = word.strip()
    if word!= lemma:
        if word[-1] == 's':
            return True
        return False
    else:
        if any([True for item in dictDef[word.strip()]['N'] if 'PLURAL' in item[0] or 'PLURAL' in re.findall(braces,item[2][0][0])]):
            return True
        elif any([True for item in dictDef[word.strip()]['N'] for i in re.findall(braces,item[2][0][0]) if 'plural' in i.lower()]):
            return True
        else:
            return False
def check_U(word,lemma):
    return any([True for item in dictDef[word.strip()]['N'] if 'U' in item[0] or 'U' in re.findall(braces,item[2][0][0])])
def check_S(word,lemma):
    if word == lemma:
        return True
    else:
        return False
        
def explain_time_error(head):
    res = []
#     in main part of the day
    if head in ['morning','afternoon','evening']:
        res.append("When you refer to 'main parts of the day' such as %s, use <b>in the</b> + time."%('morning/afternoon/evening'))
        res.append(str_example%("For example:\tIn the %s we went for a walk along the Seine."%(head)))
        res.append("Compare:\tat night: ‘I don’t like driving at night.’")
    elif head in MONTH or head.isdigit() and len(head)>2:
        head = head[0].upper() + head[1:]
        res.append("When you refer to 'months, years, centuries', use <b>in</b> + time.")
        if head in MONTH:
            res.append(str_example%("For example:\tShe’ll be coming back home in %s."%(head)))
        else:
            res.append("For example:\tIn %s he decided to join the army."%(head))
    elif head in SEASONS:
        res.append("When you refer to 'seasons', use <b>in the</b> + time.")
        res.append(str_example%("For example:\tThey’re getting married in the %s"%(head)))
    elif head in DATES:
        head = head[0].upper() + head[1:]
        res.append("When you refer to 'specific days/dates/ mornings/afternoons, etc', use 'on' + time.")
        re.append(str_example%("For example:\ton %s, on %s morning"%(head,head)))
    elif head in HOLIDAY:
        head = head[0].upper() + head[1:]
        res.append("When you refer to 'the holiday period around Christmas, Easter, Hannukkah, Ramadan, etc', use 'at' + time.")
        res.append(str_example%("For example:\tWe like to stay at home at %s."%(head)))
        res.append("Compared:\ton Christmas Day, on Easter Sunday")
    elif head in CLOCKTIME:
        res.append("When you refer to <b>main points of time in the day (e.g: midnight/noon/dawn/lunch)</b>, use at + time.")
        res.append(str_example%("For example:\tWe usually open our presents at %s."%(heads)))
    elif head == 'weekend':
        res.append("When you refer to 'weekend', use at the weekend. BUT (American English) on the weekend")
        res.append(str_example%("For example:\tWhat are you doing at the weekend?"))
    elif head == 'weekends':
        res.append("When you refer to <b>weekends</b>, use at the weekends.")
        res.append(str_example%("For example:\tI never do any work at weekends."))
    return ''.join(res)

def explain_replace(correction,entails_sent,correction_split,threshold,done = False):
    output = []
#     output.append('[ replace type ]')
    if deletion.search(correction).group(1) in allreserved:
        a_lemma = delandadd.search(correction).group(2)
        # print('a_lemma',a_lemma)
        nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
        nextdigit,nextdigit_lemma = find_nextword(entails_sent,a_lemma,'C')
        if nextword.lower() in TIME or nextdigit.isdigit():
            time_error = explain_time_error(nextword.lower())
            if time_error:
                output.append(time_error)
                done = True
        else:
            target = [delandadd.search(correction).group(2)]
            wedit = delandadd.search(correction).group(1)
            gps = find_patterns(geniatag(' '.join(entails_sent)),target)
            if gps:
                gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
                isTo = wedit=='to' or target[0]=='to'
                if not any(p>0 and isTo for _,_,part,_,p in gps):
                    if all( pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in dictWord[part][head]] for pattern,head,part,_,p in gps):
                        gps = gps[::-1]
                        gps = sorted(gps,key = lambda x: pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                    elif any( pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in dictWord[part][head]] for pattern,head,part,_,p in gps):
                        gps = [(pattern,head,part,ex,p) for pattern,head,part,ex,p in gps if pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in dictWord[part][head]]]
                    else:
                        gps = gps[::-1]
                        gps = sorted(gps,key = lambda x: pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                else:
                    headhalf = sorted([g for g in gps if g[4]>0],key = lambda x: pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                    tailhalf = [g for g in gps[::-1] if g[4]<1]
                    gps = headhalf + tailhalf
                for  pattern , head , part , _,_ in gps:
                    if head in dictWord[part]:
                        examples = select_examples(pattern,head,part)
                        if examples:
                            for ex in examples:
                                tmp = explain_pattern(ex,head,part,pattern)
                                if type(tmp) == list:
                                    output.extend(tmp)
                                else:
                                    output.append(tmp)
                            done = True
                            break
                    else:
                            ini = ['V','N','ADJ']
                            ini.remove(part)
                            for pos in ini:
                                examples = select_examples(pattern.replace(part,pos),head,pos)
                                if examples:
                                    for ex in examples:
                                        tmp = explain_pattern(ex,head,pos,pattern.replace(part,pos))
                                        if type(tmp) == list:
                                            output.extend(tmp)
                                        else:
                                            output.append(tmp)
                                        last_pat = pattern.split()[-1]
                                        if part == 'V':
                                            if isTo and last_pat == 'inf':
                                                output.append(explain_INF())
                                            elif isTo and last_pat == '-ing':
                                                output.append(explain_ING())
                                            else:
                                                output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                    done = True
                                    break
                if not done:
                    output.append(find_idioms_from_gps(gps))
            else:
                idioms = find_idioms(entails_sent,target)
                if idioms:
                    tmp = []
                    tmp.append('"<b>%s</b>" is a phrase.'%(idioms[0]))
                    tmp.append("This means that %s."%('\t'.join(list(dictPhrase[idioms[0]].values())[0][0]).strip()))
                    output.append("<br>%s</br>"%('</br><br>'.join(tmp)))
    else:
        delset,addset = compare_lemma(correction)
        d_word,d_lemma,d_part = delset
        a_word,a_lemma,a_part = addset
        d_lemma = d_lemma.lower()
        a_lemma = a_lemma.lower()
        parts = [d_part,a_part]
        if d_lemma == a_lemma:
            if 'V' in parts:
                if d_lemma == a_lemma:
                    target = [delandadd.search(correction).group(2)]
                    gps = find_patterns(geniatag(' '.join(entails_sent)),target)
                    if gps:
                        for pattern,head,part,ex in gps:
                            if ex.find(target[0]) > ex.find(head):
                                if pattern.split()[-2] in allreserved:
                                    output.append('The tense error is caused by <b>%s</b>.'%(pattern.split()[-2]))
                                    break
                                elif len(pattern.split()) and a_lemma != head:
                                    output.append('The tense error is caused by <b>%s</b>.'%(head))
                                    break
                    output.append('Tense error!')
                else:
                    output.append(explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part))
            # countable uncountable?
            elif 'N' in parts:
#                 if a_word[-1] != 's' and d_word[-1]=='s' and d_lemma == a_lemma:
                if check_U(a_word,a_lemma) and d_word[-1]=='s':
#                     show_uncountable_meaning(addword)
                    output.append('When you refer to an uncountable word, use the singular form.')
                    output.append(find_N_meaning(a_lemma,'U'))
                else:
                    if d_lemma == a_lemma:
                        output.append(find_N_meaning(a_lemma))
                    else:
                        output.append(explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part))
            else:
                output.append(explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part))
        elif d_part != a_part:
            output.append("Misuse part of speech!")
            output.append("<br>%s: %s</br><br>vs</br><br>%s: %s</br>"%(d_word,d_part,a_word,a_part))
        elif d_lemma in det_s.union(det_p) and a_lemma in det_s.union(det_p):
#             an -> a
            if d_lemma == 'an' and a_lemma == 'a':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma)
                if nextword[0] == 'h':
                    tmp = []
                    tmp.append("Before a word beginning with h, use a if the h is pronounced: <b>a house</b>, <b>a half</b>, <b>a horrible day</b>.") 
                    tmp.append("Use an if the h is silent: <b>an hour</b>, <b>an honour</b>.") 
                    tmp.append("If the h is pronounced but the syllable is unstressed, it is possible to use a or an (<b>a/an hotel</b>).")  
                    tmp.append("However, the use of an here is considered old fashioned and most people use a.")
                    output.append('<br>%s</br>'%('</br><br>'.join(tmp)))
                else:
                    if nextword[0].lower() in ['u','o']:
                        output.append("In this case, %s is pronounced as y which is a consonant sound, use a (NOT an)."%(nextword[0].lower()))
                    else:
                        output.append("Always use a (NOT an) before a word beginning with a consonant sound.")
#             a -> an
            elif d_lemma == 'a' and a_lemma == 'an':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma)
                if nextword[0].lower() in vowel:
                    if nextword[0] == 'h':
                        output.append("Use an (NOT a) before words beginning with h when the h is not pronounced: <b>an honour</b> , <b>an hour</b>.")
                    else:
                        output.append("Always use an (NOT a) before a word beginning with a vowel sound: <b>an %s</b> or <b>an %s</b>."%(vowelMap[nextword[0].lower()][0],vowelMap[nextword[0].lower()][1]))
                elif nextword[0].isupper():
                    output.append("Use an (NOT a) before an abbreviation that begins with a vowel sound")
            elif d_lemma == 'the' or a_lemma == 'the':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                nextdigit,nextdigit_lemma = find_nextword(entails_sent,a_lemma,'C')
                if nextword.lower() in TIME or nextdigit.isdigit():
                    time_error = explain_time_error(nextword.lower())
                    if time_error:
                        output.append(time_error)
                        done = True
                else:
                    output.append(dictDet[d_lemma])
                    output.append(dictDet[a_lemma])
            elif d_lemma=='any' and a_lemma in det_s.union(det_p):
                if a_lemma in ['each','every','all'] : 
                    output.append('To refer to all the people or things in a group or category, use "each/every + singular countable noun" OR "all + plural countable noun".')
                    tmp = []
                    tmp.append('For example:')
                    tmp.append('Every house in the street had one or two broken windows.')
                    tmp.append('All students are required to register during the first week.')
                    output.append('<br>%s</br>'%('</br><br>'.join(tmp)))
                elif a_lemma in det_s:
                    output.append("Any is usually used with uncountable nouns and plural countables (NOT with singular countable nouns).")
                    tmp = []
                    tmp.append("Compare: ‘Do you have any money? (money is an uncountable noun)")
                    tmp.append("Do you have any fifty-cent coins? (coins is a plural countable noun)")
                    tmp.append("Do you have a fifty-cent coin? (coin is a singular countable noun)")
                    output.append(str_example%('</p><p>'.join(tmp)))
                else:
                    output.append(dictDet[d_lemma])
                    output.append(dictDet[a_lemma])
            elif d_lemma in det_p and a_lemma in det_s:
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                if check_S(nextword,nextword_lemma):
                    output.append('<b>%s</b> is usually used with singular countable nouns.'%(a_lemma))
                    output.append(find_N_meaning(nextword))
                else:
                    output.append("%s -> %s :  this case hasn't handled yet."%(d_lemma,a_lemma))
            elif d_lemma in ['no','some'] and a_lemma == 'any':
                output.append('After negative words, you usaully use "any, anyone, anything, etc (Not some, someone, something, etc)".')
            elif 'at that moment' in ' '.join(entails_sent).lower():
                output.append(" When you are telling a story or reporting what happened, use <b>at that moment</b>\t:\tAt that moment the car skidded on the ice and went off the road.")
            elif d_lemma in det_s and a_lemma in det_p:
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                if check_S(nextword,nextword_lemma):
                    output.append('<b>%s</b> is usually used with singular countable nouns. Besides, <b>%s</b> is usually used with uncountable nouns and plural countables (NOT with singular countable nouns)'%(d_lemma,a_lemma))
                else:
                    output.append('<b>%s</b> is usually used with <b>uncountable nouns</b> such as %s.'%(a_lemma,nextword))
                    output.append(find_N_meaning(nextword,'U'))
            elif d_lemma in det_p and a_lemma in det_s:
                output.append('<b>%s</b> is usually used with plural countable nouns. Besides, <b>%s</b> is usually used with singular countable nouns.'%(d_lemma,a_lemma))
            else:
                output.append(dictDet[d_lemma])
                output.append(dictDet[a_lemma])
            
        elif not parts[0].upper() in pos_map or not any([part for part in ['v','a','n'] if d_lemma in dictWord[pos_map[part.upper()]]]):
            if tuple(sorted([d_lemma,a_lemma])) in aux:
                output.append('Tense error!')
            else:
                output.append('It is a spelling error. To be more precisely, the spelling of <b>%s</b> is correct!'%(delandadd.search(correction).group(2)))
        else:
            output.append(explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part))
#             find collocation according to minipar
            tagging = geniatag(' '.join(entails_sent))
            gps = find_patterns(tagging,[a_word])
            output.append(find_collocations(gps,tagging,a_lemma,d_lemma))
    return output  

def explain_unnecessary(correction,entails_sent,correction_split,threshold,done = False):
    output = []
#     output.append('[ Unnecessary type ]')
    focus = deletion.search(correction).group(1)
    focus = focus.lower()
    idx = correction_split.index(deletion.search(correction).group(0))
    target = []
    if idx > 0:
        target.append(correction_split[idx-1])
    if idx+1 < len(correction_split):
        target.append(correction_split[idx+1])
    if focus in det_p.union(det_s) or focus in allreserved:
        if any(t in MONTH for t in target) and focus.lower() in ['the','of']: 
            output.append("When you say the date, use %s %s  or <b>WITHOUT the or of</b>."%(target[0],target[1],target[1],target[0]))
            done = True
        elif focus == 'the':
            nextwordN,nextwordN_lemma = find_nextword(entails_sent,target[-1],'N')
            done = True
            if nextwordN[0].isupper():
    #             Proprietary
                output.append('Do not use <b>the</b> before the names of %s.'%("a language, disease, mountain, airports,railway stations, streets and roads"))
            elif check_P(nextwordN,nextwordN_lemma):
    #             plural form of countable noun
                output.append("Do not use the with the plural form of a countable noun when it is used in a general sense.")
                tmp = []
                tmp.append("Compare: ‘She likes cats.’ (= cats in general)")
                tmp.append("The cats we saw in Venice looked very hungry.’ (= a particular group of cats)")
                output.append(str_example%('</p><p>'.join(tmp)))
            elif check_uncountable(nextwordN):
                rule = "Do not use the with an uncountable noun when it is used in a general sense:"
                tmp = []
                tmp.append("She hates dishonesty.")
                tmp.append("Power doesn’t interest him.")
                output.append(rule + str_example%('</p><p>'.join(tmp)))
                
                rule = "The is used when the sense is restricted:"
                tmp = []
                tmp.append("She hates the dishonesty of the man.") 
                tmp.append("The power enjoyed by politicians doesn’t interest him.")
                output.append(rule + str_example%('</p><p>'.join(tmp)))
            else:
                output.append(dictDet[focus])
        elif any(t.lower() in TIME for t in target) and (focus.lower() in det_s or focus.lower() in allreserved):
            for t in target:
                if t.lower() in TIME or t.isdigit():
                    time_error = explain_time_error(t.lower())
                    if time_error:
                        output.append(time_error)
                        done = True
                        break
        elif focus in det_s:
            print(1182)
            nextwordN,nextwordN_lemma = find_nextword(entails_sent,target[-1],'N')
            nextwordJ,nextwordJ_lemma = find_nextword(entails_sent,target[-1],'J')
    #             uncountable
            if check_uncountable(nextwordN):
                output.append('<b>%s</b> is uncountable so it must not be used with <b>%s</b> whcih is usually paired with singular countable nouns.'%(nextwordN,focus))
                done = True
            elif check_P(nextwordN,nextwordN_lemma):
                output.append('<b>%s</b> is usually used with singular countable nouns.'%(focus))
                done = True
#             elif entails_sent.index(nextwordN) - entails_sent.index(nextwordJ) < 2:
#     #             adjective to be noun
#                 output.append("Do not use %s before an adjective (e.g. ‘deaf’, ‘British’) unless the adjective is followed by a noun"%(focus))
#                 output.append(dictDet[focus])
#                 done = True
        elif focus in det_p:
            nextwordN,nextwordN_lemma = find_nextword(entails_sent,target[-1],'J')
            if nextwordN == 'certain':
                output.append("Do not use a determiner (e.g. some, the, their) before certain when it means ‘particular.")
                output.append(dictDet[focus])
                done = True
        elif focus != 'that':
            output.append(dictDet[focus])
            done = True
    if not done:
        gps = find_patterns(geniatag(' '.join(entails_sent)),target)
        if gps:
            gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
            isTo = focus=='to'
            if not any(p>0 and isTo  for _,_,part,_,p in gps):
                gps = gps[::-1]
                gps = sorted(gps,key = lambda x: pw_ratio[x[1]][(focus,'')][x[4]],reverse = True)
            else:
                headhalf = sorted([g for g in gps if g[4]>0],key = lambda x: pw_ratio[x[1]][(focus,'')][x[4]],reverse = True)
                tailhalf = [g for g in gps[::-1] if g[4]<1]
                gps = headhalf + tailhalf
            for pattern , head , part , _,_ in gps:
                if head in  dictWord[part]:
                    examples = select_examples(pattern,head,part)
                    if examples:
                        for ex in examples:
                            last_pat = pattern.split()[-1]
                            if part == 'V':
                                if isTo and last_pat == '-ing':
                                    output.append(explain_ING())
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    if type(tmp) == list:
                                        output.extend(tmp)
                                    else:
                                        output.append(tmp)
                                elif focus in allreserved:
                                    output.append(explain_VT_error(head,correction,pattern,ex))
                                else:
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    if type(tmp) == list:
                                        output.extend(tmp)
                                    else:
                                        output.append(tmp)
                            else:
                                tmp = explain_pattern(ex,head,part,pattern)
                                if type(tmp) == list:
                                    output.extend(tmp)
                                else:
                                    output.append(tmp)
                        done = True
                        break
                else:
                    ini = ['V','N','ADJ']
                    ini.remove(part)
                    for pos in ini:
                        examples = select_examples(pattern.replace(part,pos),head,pos)
                        if examples:
                            for ex in examples:
                                tmp = explain_pattern(ex,head,pos,pattern.replace(part,pos))
                                if type(tmp) == list:
                                    output.extend(tmp)
                                else:
                                    output.append(tmp)
                                last_pat = pattern.split()[-1]
                                if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                    output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                            done = True
                            break
                        if done:
                            break
            if not done:
                output.append(find_idioms_from_gps(gps))
        else:
            
            output.append('grammar error : missing prepositions or conjunctions')
    return output
            
def explain_missing(correction,entails_sent,correction_split,threshold,done=False):
    output = []
#     output.append('[ Missing type]')
    focus = addition.search(correction).group(1)
    nextwordN,nextwordN_lemma = find_nextword(entails_sent,focus,'N')
    nextwordV,nextwordV_lemma = find_nextword(entails_sent,focus,'V')
    nextdigit,nextdigit_lemma = find_nextword(entails_sent,focus,'C')
    if focus.lower() in det_s.union(det_s):
        if nextwordN.lower() in TIME or nextdigit.isdigit():
            if focus.lower() =='the' or focus.lower() in det_s or focus.lower() in allreserved:
                time_error = explain_time_error(nextwordN.lower())
                if time_error:
                    output.append(time_error)
                    done = True
        elif focus.lower() == 'the':
            nextwordJ,nextwordJ_lemma = find_nextword(entails_sent,focus,'J')
            if entails_sent.index(nextwordJ) >= entails_sent.index(nextwordN):
    #             only N after the
                if nextwordN[0].isupper():
                    output.append(dictDet[focus.lower()])
                    output.append("Always use <b>the</b> when you know that the person you are talking or writing to will understand which person, thing, or group you are referring to.")
                    tmp = []
                    rule = "Always use <b>the</b> with the name of"
                    tmp.append("canals (e.g. the Suez Canal),")
                    tmp.append("rivers (e.g. the River Thames),")
                    tmp.append("oceans (e.g. the Atlantic Ocean),")
                    tmp.append("plural names (e.g. the Philippines),")
                    tmp.append("any country whose name includes ‘state’, ‘union’, ‘republic’, ‘kingdom’ etc (e.g. the U.K, the United Kingdom),")
                    tmp.append("hotels,")
                    tmp.append("and restaurants (Note that names with a possessive form are exceptions: Tiffany's)")
                    output.append(rule + str_example%('</p><p>'.join(tmp)))
                    done = True
            else:
    #             J after the
                rule = "To refer to a group of people or stuff, use 'the + adjective'"
                tmp = []
                rule += "<br>[people]</br>"
                tmp.append("the elderly") 
                tmp.append("the British")
                rule += str_example%('</p><p>'.join(tmp))

                tmp = []
                rule += "<br>[stuff]</br>"
                tmp.append("the mysterious")
                tmp.append("the beautiful")
                output.append(rule+str_example%('</p><p>'.join(tmp)))
                done = True
        elif focus in det_p:
            output.append("Use a determiner before a plural countable noun such as %s"%(nextwordN))
            output.append(dictDet[focus.lower()])
            output.append(find_N_meaning(nextwordN))
            done = True
        elif focus in det_s:
            print('1324')
            if focus != 'that':
                output.append("Use a determiner before a singular countable noun such as %s"%(nextwordN))
                output.append(find_N_meaning(nextwordN))
                done = True
            else:
                if  nextwordV!= nextwordN and entails_sent.index(nextwordV) - entails_sent.index(nextwordN)>2:
                    output.append("Use a determiner before a singular countable noun such as %s"%(nextwordN))
                    output.append(find_N_meaning(nextwordN))
                    done = True
                else:
                    output.append("Do not omit <b>that</b> before a clause.")
                    done = True
        
    if not done:
        idx = [id for id,seg in enumerate(correction_split) if addition.search(correction).group(0) in seg][0]
        target = []
        if idx > 0:
            target.append(' '.join([correction_split[idx-1],focus]))
        if idx+1 < len(correction_split):
            target.append(' '.join([focus,correction_split[idx+1]]))
        gps = find_patterns(geniatag(' '.join(entails_sent)),target)
        if focus in allreserved:
            if gps:
                gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
                isTo = target[0]=='to'
                if not any(p>0 and isTo for _,_,part,_,p in gps):
                    gps = gps[::-1]
                    gps = sorted(gps,key = lambda x: pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                for pattern , head , part , _,_ in gps:
                    if head in  dictWord[part]:
                        if dictWord[part][head]: 
                            examples = select_examples(pattern,head,part)
                            if examples:
                                for ex in examples:
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    if type(tmp) == list:
                                        output.extend(tmp)
                                    else:
                                        output.append(tmp)
                                    last_pat = pattern.split()[-1]
                                    if part == 'V':
                                        if isTo and last_pat == 'inf':
                                            output.append(explain_INF())
                                        else:
                                            output.append(explain_VI_error(head,correction,pattern,ex))
                                done = True
                                break
                        else:
                            ini = ['V','N','ADJ']
                            ini.remove(part)
                            for pos in ini:
                                examples = select_examples(pattern.replace(part,pos),head,pos)
                                if examples:
                                    for ex in examples:
                                        tmp = explain_pattern(ex,head,pos,pattern.replace(part,pos))
                                        if type(tmp) == list:
                                            output.extend(tmp)
                                        else:
                                            output.append(tmp)
                                        last_pat = pattern.split()[-1]
                                        if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                            output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                    done = True
                                    break
                    else:
                        output.append(find_voc_meaning(head,part))
                        done = True
                        break
                if not done:
                    output.append(find_idioms_from_gps(gps))
            else:
                phrase,head = find_idioms(entails_sent,target)
                if phrase and head:
                    done = True
                    output.append('<b>%s</b> is a phrase. Its definition is listed in the below. <ol><li>%s</li></ol>'%(phrase,'</li><li>'.join(['\t'.join(d).strip() for d in list(dictPhrase[phrase].values())[0][:2]])))
                    for p in phraseV[head].keys():
                        if phrase in p:
                            output.append(str_example%('For example: %s'%('  '.join([' '.join(phraseV[head][p][0][2][:2]) for p in phraseV[head].keys() if phrase in p ]))))               
        else:
            if gps:
                gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
                gps = sorted(gps,key = lambda x: pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                for pattern , head , part , _,_ in gps:
                    if head in  dictWord[part]:
                        examples = select_examples(pattern,head,part)
                        if examples:
                            for ex in examples:
                                tmp = explain_pattern(ex,head,part,pattern)
                                if type(tmp) == list:
                                    output.extend(tmp)
                                else:
                                    output.append(tmp)
                            done = True
                            break
                    else:
                            ini = ['V','N','ADJ']
                            ini.remove(part)
                            for pos in ini:
                                examples = select_examples(pattern.replace(part,pos),head,pos)
                                if examples:
                                    for ex in examples:
                                        tmp = explain_pattern(ex,head,pos,pattern.replace(part,pos))
                                        if type(tmp) == list:
                                            output.extend(tmp)
                                        else:
                                            output.append(tmp)
                                        last_pat = pattern.split()[-1]
                                        if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                            output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                    done = True
                                    break
                if not done:
                    output.append(find_idioms_from_gps(gps))
            else:
                delword,part_ = my_lemma(correction,entails_sent)
                if part_ in ['N','J','V']:
                    if part_ == 'J':
                        part = 'ADJ'
                    output.append(find_voc_meaning(delword,part_))
                else:
                    phrase,head = find_idioms(entails_sent,target)
                    if phrase and head:
                        done = True
                        output.append('<b>%s</b> is a phrase. Its definition is listed in the below. <ol><li>%s</li></ol>'%(phrase,'</li><li>'.join([' '.join(d) for d in list(dictPhrase[phrase].values())[0][:2]])))
                        output.append(str_example%('For example: %s'%('  '.join([' '.join(phraseV[head][p][0][2][:2]) for p in phraseV[head].keys() if phrase in p ]))))
    return output

def leave_error(correction,lists):
    head = lists[0]
    tail = lists[1]
    input_cor = ""
    input_split = []
    if head or tail:
        if head and tail:
            start = correction.find(head)
            idx = start + len(head)
        elif head:
            start = correction.find(head)
            idx = start + len(head)
        elif tail:
            start = correction.find(tail)
            idx = start + len(tail)
        if idx < len(correction):
            input_cor = correction[:idx+1]+ ' '.join(rephrase(correction[idx:]))
            input_split = input_cor.split()
        return input_cor,input_split,start
def grep_error(string,lists,error,base,mod_list):
    start = 0
    # for l in lists:
    #     idx = string.find(l,start)
    #     error.append((l,base+idx,base+idx+len(l)))
    #     start = idx+1
    # return
    for matchobj in lists:
        idx = string.find(matchobj, start)
        after = '<span class="edit explain edit{error_id}">{edits}</span>'.format(error_id = len(error),edits = matchobj)
        error.append((matchobj,base+idx,base+idx+len(matchobj)))
        string = myreplace(string,idx,matchobj, after)
        start = idx+1
    mod_list.append(string)

def myreplace(string,idx,before,after):
    if idx > -1:
        if len(string) > idx+len(before):
            string = string[:idx] + after + string[idx+len(before):]
        else:
            string = string[:idx] + after
        return string
    else:
        return

def grep_error_GEC(string,b_lists,lists,errors,mod_list):
    error_id = len(errors)
    start = 0
    for before, matchobj in zip(b_lists, lists):
        idx = string.find(before, start)
        if matchobj[0]:
            after = '<span class="edit deletion edit{error_id}">{delete}</span> <span class="edit addition edit{error_id}">{insert}</span>'.format(
                error_id=error_id, delete=matchobj[0], insert=matchobj[1])
        elif matchobj[2]:
            after = '<span class="edit deletion edit{error_id}">{delete}</span>'.format(error_id=error_id, delete=matchobj[2])
        else:
            after = '<span class="edit addition edit{error_id}">{insert}</span>'.format(error_id=error_id, insert=matchobj[3])
        string = myreplace(string,idx,before, after)
        error_id += 1
        start = idx+1
    mod_list.append(string)
    # print('in grep_error_GEC',mod_list)


def explain(corrections,result,mode):
    mod_list = []
    prevs = []
    error_count = 0
    error_list = []
    accumulate_len = 0
    final_list = []
    for correction in sent_tokenize(corrections):
        correction = beautify(correction)
        final_list.append(correction)
        entails_sent = rephrase(correction)
        if mode == 'GEC':
            grep_error_GEC(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',correction),re.findall(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}|\[- *([^\[\]]*?) *-\]|\{\+ *([^\[\]]*?) *\+\}',correction),error_list,mod_list) 
            grep_error(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',correction),error_list,accumulate_len,[])
        else:
            grep_error(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',correction),error_list,accumulate_len,mod_list)
            print(mod_list)
        accumulate_len += len(correction)+1
        while deletion.search(correction) or addition.search(correction):
            if prevs:
                if prevs[0] in allreserved or prevs[1] in allreserved:
                    if deletion.search(correction) and addition.search(correction):
                        a = deletion.search(correction).group(0)
                        b = addition.search(correction).group(0)
                        c = addition.search(correction).group(1)
                        if 'ing' in a or 'ing' in b:
                            correction = ' '.join(correction.replace(a,'').replace(b,c).split()) 
                            error_count += 1    
                            continue
            done = False
            
            case1 = 100000
            case2 = 100000
            case3 = 100000
            replacelist = [[],[],[]]
            if delandadd.search(correction):
                tmp = multi_delandadd.search(correction).group(0).strip()
                # before = ''.join(tmp.split())
                before = ' '.join(re.findall(addition, tmp))
#                 transform = ' '.join(re.findall(deletion, tmp)) + '\t->\t' + before
                transform = 'Replace ' + ' '.join(re.findall(deletion, tmp)) + ' with ' + before
                after = before
                case1 = correction.find(tmp)
                replacelist[0] = [tmp,after,transform] 
                prevs = ( ' '.join(re.findall(deletion, tmp)),before)
            if deletion.search(correction):
                tmp = deletion.search(correction).group(0)
                after = ''
                case2 = correction.find(tmp)
#                 transform = deletion.search(correction).group(1) + '\t->\t' + 'NONE'
                transform = 'Omit ' + deletion.search(correction).group(1) 
                replacelist[1] = [tmp,after,transform] 
                prevs = ( deletion.search(correction).group(1)  ,'')
            if addition.search(correction):
                tmp = addition.search(correction).group(0)
                after = addition.search(correction).group(1)
                case3 = correction.find(tmp)
#                 transform = 'NONE' + '\t->\t' + addition.search(correction).group(1)
                transform = 'Insert ' + addition.search(correction).group(1)
                replacelist[2] = [tmp,after,transform] 
                prev = ('',addition.search(correction).group(1))
            idx = min([case1, case2,case3])
            idx = [case1, case2,case3].index(idx)
            
            input_cor,input_split,threshold = leave_error(correction,replacelist[idx])
            # replace
            if idx == 0:
                tmp = explain_replace(input_cor,entails_sent,input_split,threshold,done)
            # deletion
            elif idx == 1:
                tmp = explain_unnecessary(input_cor,entails_sent,input_split,threshold,done)
            # addition
            elif idx == 2 :
                tmp = explain_missing(input_cor,entails_sent,input_split,threshold,done) 
            result[error_count]['header'] = replacelist[idx][2]
            result[error_count]['body'] = tmp
            # result[error_count]['pos'] = (error_list[error_count][1],error_list[error_count][2])
            error_count += 1
            correction = ' '.join(correction.replace(replacelist[idx][0],replacelist[idx][1]).split())
    # result[0]['beautify'] = ' '.join(final_list)
    result[0]['sent'] = ' '.join(mod_list)

def beautify(s):
    for a in re.findall(ab,s):
        if a.lower() in abbrs:
            s = s.replace(a,abbrs[a.lower()])
    tokens = [ss for ss in s.split() if ss.strip()]
    s = ' '.join(tokens)
    s_tmp = s
    while loss_add.search(s_tmp) or loss_del.search(s_tmp):
        if loss_del.search(s_tmp):
            head = loss_del.search(s_tmp).group(0)
            tail = loss_del.search(s_tmp).group(1)
            s = s.replace(head,'[-'+tail+'-]')
            s_tmp = s_tmp.replace(head,tail)
        if loss_add.search(s_tmp):
            head = loss_add.search(s_tmp).group(0)
            tail = loss_add.search(s_tmp).group(1)
            s = s.replace(head,'{+'+tail+'+}')
            s_tmp = s_tmp.replace(head,tail)
    return ' '.join([ss.strip() for ss in s.split()])
    
def init_DB():
    tmp_dictWord = eval(open('/home/nlplab/yeema/ErrorExplaination/GPs.linggle.extend.txt', 'r').read())
    tmp_phrase = eval(open('/home/nlplab/yeema/ErrorExplaination/phrase.txt', 'r').read())
    tmp_dictDef = eval(open('/home/nlplab/yeema/ErrorExplaination/cambridge.gps.semanticDict_word_v4.json').read())
    tmp_dictPhrase = eval(open('/home/nlplab/yeema/ErrorExplaination/cambridge.gps.semanticDict_phrase_v5.json').read())
    tmp_miniparCol = eval(open('/home/nlplab/yeema/grammarpat/minipar.collocation.json').read())
    tmp_pw = open('/home/nlplab/yeema/problemWords/problem.col.v2').readlines()
    for pos, values in tmp_dictWord.items():
        for head,value in values.items():
            dictWord[pos][head] = value
            
    for key,phrase in tmp_phrase.items():
        for p,pat in phrase.items():
            phraseV[key][p] = pat
            
    for head,values in tmp_dictPhrase.items():
        for attr,value in values.items():
            dictPhrase[head][attr] = value
            
    for head,values in tmp_dictDef.items():
        for pos,value in values.items():
            dictDef[head][pos] = value
    
    for head,values in tmp_miniparCol.items():
        for pat,tails in values.items():
            for tail, c in tails.items():
                miniparCol[head][pat][tail] = int(c)
    for line in tmp_pw:
        line = line.strip()
        line = line.split('\t')
        head, edit, p, c = line
        edit = eval(edit)
        p = int(p)
        c = int(c)
        pw[head][edit][p] = c
    for head,edits in pw.items():
        s = sum([j for i in pw[head].values() for j in i.values()])
        for edit,count in edits.items():
            for key,c in count.items():
                if key >0:
                    pw_ratio[head][edit][1] += c/s
                elif key < 0:
                    pw_ratio[head][edit][-1] += c/s
                
init_DB()
app.run(debug=True)