from app import *
import re

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
pgPreps = 'under|without|around|round|in_favor_of|_|about|after|against|among|as|at|between|behind|by|for|from|in|into|of|on|upon|over|through|to|toward|forward|off|on|across|towards|with|out|during'.split('|')
otherPreps ='out|off|down|up|across'.split('|')
reserveWord = {'for', 'over', 'at', 'about', 'up', 'by', 'under', 'among', 'on', 'out', 'that', 'against', 'of', 'in', 'amount', 'to', 'between', 'toward', 'towards', 'down', 'from', 'as', 'through', 'around', 'and', 'off', 'into', 'without', 'with', 'after', 'across', 'behind'}
allreserved = set()
allreserved = allreserved.union(set(pgPreps) , set(otherPreps) , reserveWord)
mapHead = dict( [('H-NP', 'N'), ('H-VP', 'V'), ('H-ADJP', 'ADJ'), ('H-ADVP', 'ADV'), ('H-VB', 'V')] )
mapRest = dict( [('VBG', '-ing'), ('VBD', 'v-ed'), ('VBN', 'v-ed'), ('VB', 'v'), ('NN', 'n'), ('NNS', 'n'), ('JJ', 'adj'), ('RB', 'adv'),('NP', 'n'), ('VP', 'v'), ('JP', 'adj'), ('ADJP', 'adj'), ('ADVP', 'adv'), ('SBAR', 'that')] )
modeMap = {'V':'V','J':'ADJ','N':'N'}
maxDegree = 9



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
        elif isverbpat(lemmas[head_pos][0],pat.replace('pron-refl','n').replace('adj n','n').replace('-ing','n')):
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
        elif isadjpat(lemmas[head_pos][0],pat.replace('pron-refl','n').replace('adj n','n')):
            mode = 'ADJ'
            return pat.replace('adj n','n'),head_pos,change_start
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
            if len(pat_example.split())>0 and pat_example.split()[-1] == 'the':
                continue
            whs = [wh for wh in ['how' , 'who' , 'what', 'when','why','where'] if wh in pat]
            if whs:
                for wh in whs:
                    tmp.append([pat.replace(wh,'wh'),head,mode,pat_example])
            if any([t for t in target if re.findall(r'\b' + re.escape(t)+r'\b', pat_example)]):
#                 if any([pat[0].split("%")[0] for pat in dictWord[mode][head]]):
                    tmp.append([pat,head,mode,pat_example])
    return tmp