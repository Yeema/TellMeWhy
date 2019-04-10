from app import *
from nltk.tokenize import word_tokenize
from preprocess import *
import re
import grammarpat
import spacy
from linggle_api import Linggle

nlp = spacy.load('en_core_web_md')
ling = Linggle('www')

ab = re.compile(r"\w*'\w*|\w*’\w*")
loss_del = re.compile(r'\[ *- *([^\[\]]*?) *- *\]')
loss_add = re.compile(r'\{\ *\+ *([^\[\]]*?) *\+ *\}')
delandadd = re.compile(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}')
deletion = re.compile(r'\[- *([^\[\]]*?) *-\]')
addition = re.compile(r'\{\+ *([^\[\]]*?) *\+\}')
braces = re.compile(r'\[ *(.*?) *\]')
multi_delandadd = re.compile(r'(\[-([^\[\]]*?)-\] *\{\+([^\{\}]*?)\+\} *)+')

str_example = '<div class="px-2 py-1 mt-2 text-monospace"><p>%s</p></div>'

MONTH = set("january,february,march,april,may,june,july,august,september,october,november,december".split(','))
SEASONS = set("spring,summer,fall,autumn,winter".split(","))
DATES = set("monday,tuesday,wednesday,thursday,friday,saturday,sunnday".split(","))
HOLIDAY = set("christmas,easter,hannukkah,ramadan".split(","))
CLOCKTIME = set("midnight/noon/dawn/lunch".split('/'))
POD = set("morning/afternoon/evening".split("/"))
TIME = set(list(MONTH)+\
                list(SEASONS)+\
                list(DATES)+\
                list(HOLIDAY)+\
                list(CLOCKTIME)+\
                list(POD)+\
                ['weekend','weekends'])

def find_phrases(patterns,head,part):
    output_phrases = []
    head = head.lower()
    for pattern in patterns:
        words = word_tokenize(pattern)
        words = ' '.join([w for w in words if w in grammarpat.allreserved or w==part]).replace(part,head)
        output_phrases.extend([phrase for phrase in app.phraseV[head].keys() if phrase.split('%')[0] == words])
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
            eng = eng.replace(braces.search(eng).group(0),'')
    attra = eng+ch

    if len(listb[index%len(wordb)][2][0]) == 2:
        eng = listb[index%len(wordb)][2][0][0]
        ch = " ( "+ listb[index%len(wordb)][2][0][1]+" )"
    else:
        eng = listb[index%len(wordb)][2][0][1]
        ch = " ( "+ listb[index%len(wordb)][2][0][2]+" )"
    if braces.search(eng):
            eng = eng.replace(braces.search(eng).group(0),'')
    attrb = eng + ch
    return attra,attrb

def explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part):
    output = []
    d_lemma = d_lemma.lower()
    a_lemma = a_lemma.lower()
    output.append('It is a semantic error.')
    del_word,add_word = deletion.search(correction).group(1).lower(),addition.search(correction).group(1).lower()
    if (del_word,add_word) in app.dictSimilar:
        output.append(app.dictSimilar[(del_word,add_word)])
    elif (d_lemma,a_lemma) in app.dictSimilar:
        output.append(app.dictSimilar[(d_lemma,a_lemma)])
    else:
        listd = app.dictDef[d_lemma][d_part.upper()]
        lista = app.dictDef[a_lemma][a_part.upper()]
        if not listd:
            listd = app.dictDef[d_lemma]['']
        if not lista:
            lista = app.dictDef[a_lemma]['']
        if listd and lista:
            delmeaning,addmeaning = find_meaning(listd,lista,d_lemma,a_lemma)
            tmp = []
            if delmeaning:
                tmp.append('<b>%s</b> :\t%s.'%(d_lemma,delmeaning))
            if addmeaning:
                tmp.append("<b>%s</b> :\t%s."%(a_lemma,addmeaning))
            if tmp:
                output.append("<p>%s</p>"%('</p><p>'.join(tmp)))

    return '<p>'+'</p><p>'.join(output)+'</p>'

def explain_VT_error(head,correction,pattern,ex):
    output = []
    head = head.lower()
    if app.dictDef[head]:
        Ts = []
        Is = []
        emp = []
        for  df in app.dictDef[head]['V']:
            if 'T' in df[0]:
                Ts.append(merge_def(df))
            elif 'I' in df[0]:
                Is.append(merge_def(df))
            elif not df[0]:
                emp.append(merge_def(df))
        if Ts and not Is and not emp:
            output.append("%s is a transitive verb and needs an object instead of a preposition (e.g. %s)."%(head[0].upper()+head[1:],deletion.search(correction).group(1)))
        elif Ts and Is:
            output.append("<b>%s</b> is both transitive and intransitive verb. When it means %s, it is a transitive verb. However, when it describes that %s, it represents a intransitive verb."%(head[0].upper()+head[1:],' or '.join(Ts[:2]),' or '.join(Is[:2])))
        elif Ts:
            output.append("<b>%s</b> is a transitive verb and needs an object instead of a preposition (e.g. %s) when it means %s."%(head[0].upper()+head[1:],deletion.search(correction).group(1),Ts[0]))
        elif emp:
            output.append("<b>%s</b> is a transitive verb and needs an object instead of a preposition (e.g. %s) when it means %s."%(head[0].upper()+head[1:],deletion.search(correction).group(1),emp[0]))

        tmp = explain_pattern(ex,head,'V',pattern)
        if type(tmp) == list:
            output.extend(tmp)
        else:
            output.append(tmp)
    else:
        output.append("<b>%s</b> is a transitive verb and needs an object instead of a preposition (e.g. %s)."%(head[0].upper()+head[1:],deletion.search(correction).group(1)))
        tmp = explain_pattern(ex,head,'V',pattern)
        if type(tmp) == list:
            output.extend(tmp)
        else:
            output.append(tmp)
    return '<br>'.join(output)

def explain_VI_error(head,correction,pattern,ex):
    output = []
    head = head.lower()
    if app.dictDef[head]:
        Ts = []
        Is = []
        emp = []
        for  df in app.dictDef[head]['V']:
            if 'I' in df[0]:
                Is.append(merge_def(df))
            if 'T' in df[0]:
                Ts.append(merge_def(df))

        if Is and not Ts:
            output.append("<b>%s</b> is an intransitive verb and it means %s."%(head[0].upper()+head[1:],' or '.join(Is[:2])))
        elif Ts:
            output.append("<b>%s</b> is an intransitive verb here which means %s. However, it can be transitive sometimes depending on the scenerio."%(head[0].upper()+head[1:],' or '.join(Is[:2])))
        else:
            output.append("<b>%s</b> is a intransitive verb and needs a preposition (e.g. %s)."%(head[0].upper()+head[0][1:],addition.search(correction).group(1)))
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
    if app.dictDef[head]:
        Cs = []
        Us = []
        emp = []
        for  df in app.dictDef[head]['N']:
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
                output.append("The noun <b>%s</b> is uncountable. It means %s which describes relatively abstract concept."%(head,' or '.join(Us[:2])))
            elif Us and Cs:
                output.append("The noun <b>%s</b> can be both countable and uncountable depending on its usage. When it means %s, it expresses an abstract concept so it is uncountable. However, when it explians %s, it is a countable noun."%(head,' or '.join(Us),' or '.join(Cs)))
            elif emp:
                output.append("The noun <b>%s</b> is uncountable because it descibes relatively abstract concept that %s."%(head,' or '.join(emp[:2])))
        else:
            if Cs and not Us:
                output.append("The noun <b>%s</b> is countable. It means %s which describes relatively abstract concept."%(head,' or '.join(Cs[:2])))
            elif Us and Cs:
                output.append("The noun <b>%s</b> can be both countable and uncountable depending on its usage. When it means %s, it expresses an abstract concept so it is uncountable. However, when it explians %s, it is a countable noun."%(head,' or '.join(Us),' or '.join(Cs)))
            elif emp:
                output.append("The noun <b>%s</b> is countable when it means %s."%(head,' or '.join(emp[:2])))
    return '<p>'+'</p><p>'.join(output)+'</p>'

def check_uncountable(head):
    head = head.lower()
    if app.dictDef[head]:
        for  df in app.dictDef[head]['N']:
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
    head = head.lower()
    mapp_ = {'V':'verb','N':'noun','ADJ':'adjective','C':'countable','U':'uncountable','PLURAL':'usually in plural format','I':'intransitive','T':'transitive'}
    head = head.lower()
    if app.dictDef[head] and app.dictDef[head][part]:
#         find alternative part description
        is_mapp_ = set([mapp_[ex] for exs in app.dictDef[head][part] for ex in exs[0] if ex in mapp_])
#         output.append(head,part,app.dictDef[head][part][0][2])
        eng = app.dictDef[head][part][0][2][0][0].strip()
        if braces.search(eng):
            eng = eng.replace(braces.search(eng)[0],'')
        ch = '( '+app.dictDef[head][part][0][2][0][1] + ' )'
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
    
    output = []
    if pattern == ex[0].split('%')[0]:
        if pattern[-1].isupper():
            tmp = []
            tmp.append('The usage of <b>%s</b>:\t<b>%s</b>'%(head,pattern))
            tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
            output.append('<br>'.join(tmp))
        else:
            tmp = []
            tmp.append('The usage of <b>%s</b>:\t<b>%s</b>'%(head,pattern))
            tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
            output.append('<br>'.join(tmp))
    else:
        tmp = []
        if ex[0].split('%')[0][:3] != '(v)':
            tmp.append('The usage of <b>%s</b>:\t<b>%s</b>'%(head,' or '.join([ex[0].split('%')[0],pattern])))
        else:
            tmp.append('The usage of <b>%s</b>:\t<b>%s</b>'%(head,ex[0].split('%')[0]))
        tmp.append(str_example%('For example:\t%s'%('\t'.join(ex[2][:-1]))))
        output.append('<br>'.join(tmp))
    # if app.miniparCol[head][ex[0].split('%')[0]]:
    #     _pos = {'ADJ':'adjective','V':'verb','N':'noun'}
    #     if output:
    #         output[-1] += "<li>Besides, it is often paired the %s <b>%s</b> with vocabularies such as <b>%s</b>.</li>"%(_pos[part],head,', '.join([v[0] for v in app.miniparCol[head][ex[0].split('%')[0]].most_common(3)]))
    #     else:
    #         output.append("Besides, it is often paired the %s <b>%s</b> with vocabularies such as <b>%s</b>."%(_pos[part],head,', '.join([v[0] for v in app.miniparCol[head][ex[0].split('%')[0]].most_common(3)])))
    #     return output
    return '<p>'+'</p><p>'.join(output)+'</p>'

def collocation_witout_compare(head,part,ex):
    if app.miniparCol[head][ex[0].split('%')[0]]:
        _pos = {'ADJ':'adjective','V':'verb','N':'noun'}
        return "<p>Besides, it is often paired %s <b>%s</b> with vocabularies such as <b>%s</b>.</p>"%(_pos[part],head,', '.join([v[0] for v in app.miniparCol[head][ex[0].split('%')[0]].most_common(3)]))
    
def select_examples(pattern,head,part):
    res = [item for item in app.dictWord[part][head] if pattern == item[0].split('%')[0]]
    if res:
        return res
    res = [item for item in app.dictWord[part][head] if pattern== item[0].split('%')[0].replace('(v)','').strip() or pattern.replace('-ing','n')== item[0].split('%')[0].replace('(v)','').strip() or pattern.replace('pron-refl','n') == item[0].split('%')[0]]
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
            if tags[idx][0] in ['V','N','J'] or lemmas[idx] in grammarpat.allreserved:
                head = lemmas[idx]
                phrase = head +' '+ phrase
                if app.dictPhrase[phrase]:
                    done = True
                    break
    else:
        for t in target:
            if not done:
                idx,words,lemmas,tags = find_idx(tagging,target[0].split()[0])
                phrase = t
            while idx >0 and not done:
                idx -= 1
                if tags[idx][0] in ['V','N','J'] or lemmas[idx] in grammarpat.allreserved:
                    head = lemmas[idx]
                    phrase = head +' '+ phrase
                    if app.dictPhrase[phrase]:
                        done = True
                        break
    if done:
        return phrase,head
    else:
        return '',''

def find_idioms_from_gps(gps):
    output = []
    done = False
    for  pattern , head , part , _,_ in gps[::-1]:
        if not done:
            if app.phraseV[head]:
                phrases = find_phrases([pattern],head,part)
                if phrases:
                    for phrase in phrases:
                        if phrase.split('%')[0] in app.dictPhrase:
                            output.append('<b>%s</b> is a phrase which means <b>%s</b>.'%(phrase.split('%')[0],' '.join(list(app.dictPhrase[phrase.split('%')[0]].values())[0][0])))
                        if  '  '.join(app.phraseV[head][phrase][0][2][:2]):
                            output.append(str_example%("For example: %s"%('  '.join(app.phraseV[head][phrase][0][2][:2]))))
                        if output:
                            done = True
    if output:
        return '<p>'+'</p><p>'.join(output)+'</p>'
    else:
        return

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
    a_lemma = a_lemma.lower()
    d_lemma = d_lemma.lower()
    for gp in gps[::-1]:
        pattern = ' '.join([g for g in gp[0].replace('(v)','').split() if g.strip()])
        if len(pattern.split()) == 3 or pattern == 'V n':
            headword, pos, sent = gp[1:]
            headword = headword.lower()
            idx,words,lemmas,tags = find_idx(tagging,sent.split()[-1])
            tail = lemmas[idx]
      
            if headword == a_lemma:
                if app.miniparCol[a_lemma][pattern][lemmas[idx]] or app.miniparCol[d_lemma][pattern][lemmas[idx]]:
                    if pattern == 'V n':
                        col = ' '.join([a_lemma,tail])
                        wcol = ' '.join([d_lemma,tail])
                        result = ling.search("{correct}/{wrong} {tail}".format(correct = a_lemma, wrong = d_lemma,tail = tail))
                    else:
                        prep = pattern.split()[1]
                        col = ' '.join([a_lemma,prep,tail])
                        wcol = ' '.join([d_lemma,prep,tail])
                        result = ling.search("{correct}/{wrong} {prep} {tail}".format(correct = a_lemma, wrong = d_lemma,prep = prep,tail = tail))
                    if len(result['ngrams'])>1:
                        percentage = int(result['ngrams'][0][1])/sum([int(r[1]) for r in result['ngrams']])
                    else:
                        percentage = 1
                    output.append('<b>%s</b> is a more common collocation than <b>%s</b>.'%(col,wcol))
                    output.append('The probability of using <b>%s</b> is %s%s.'%(col,"{:3.2f}".format(percentage*100),'%'))
            else:
                if app.miniparCol[headword][pattern][a_lemma] or app.miniparCol[headword][pattern][d_lemma]:
                    if pattern == 'V n':
                        col = ' '.join([headword,a_lemma])
                        wcol = ' '.join([headword,d_lemma])
                        result = ling.search("{correct}/{wrong} {tail}".format(correct = a_lemma, wrong = d_lemma,tail = tail))
                    else:
                        col = ' '.join([headword,pattern.split()[1],a_lemma])
                        wcol = ' '.join([headword,pattern.split()[1],d_lemma])
                        result = ling.search("{correct}/{wrong} {prep} {tail}".format(correct = a_lemma, wrong = d_lemma,prep = prep,tail = tail))
                    if len(result['ngrams'])>1:
                        percentage = int(result['ngrams'][0][1])/sum([int(r[1]) for r in result['ngrams']])
                    else:
                        percentage = 1
                    output.append('<b>%s</b> is a more common collocation than <b>%s</b>.'%(col,wcol))
                    output.append('The probability of using <b>%s</b> is %s%s.'%(col,"{:3.2f}".format(percentage*100),'%'))
        if output:
            return '<p>'+'</p><p>'.join(output)+'</p>'
        
    if output:
        return '<p>'+'</p><p>'.join(output)+'</p>'
    else:
        return
    
def explain_INF():
    inf = "When verbs followed by a to-infinitive often indicate the intention of an action or a future event."
    ing = "Compare: Verbs followed by an <b>-ing</b> form often emphasize on a status, fact, or activity."
    return "<p>"+inf+"</p><p>"+ing+"</p>"
def explain_ING():
    ing = "When verbs followed by an <b>-ing</b> form often emphasize on a status, fact, or activity."
    inf = "Compare: Verbs followed by a to-infinitive often indicate the intention of an action or a future event."
    return "<p>"+ing+"</p><p>"+inf+"</p>"
def check_P(word,lemma):
    word = word.strip()
    if word!= lemma:
        if word[-1] == 's':
            return True
        return False
    else:
        if any([True for item in app.dictDef[word.strip()]['N'] if 'PLURAL' in item[0] or 'PLURAL' in re.findall(braces,item[2][0][0])]):
            return True
        elif any([True for item in app.dictDef[word.strip()]['N'] for i in re.findall(braces,item[2][0][0]) if 'plural' in i.lower()]):
            return True
        else:
            return False
def check_U(word,lemma):
    return any([True for item in app.dictDef[word.strip()]['N'] if 'U' in item[0] or 'U' in re.findall(braces,item[2][0][0])])
def check_S(word,lemma):
    if word == lemma:
        return True
    else:
        return False

def check_both(target,gps):
    cp = ' '.join(target)
    for pattern,head,part,ex,pos in gps:
        if ex == cp:
            return [pattern,head,part,ex,pos]

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
        res.append(str_example%("For example:\tWe usually open our presents at %s."%(head)))
    elif head == 'weekend':
        res.append("When you refer to 'weekend', use at the weekend. BUT (American English) on the weekend")
        res.append(str_example%("For example:\tWhat are you doing at the weekend?"))
    elif head == 'weekends':
        res.append("When you refer to <b>weekends</b>, use at the weekends.")
        res.append(str_example%("For example:\tI never do any work at weekends."))
    return ''.join(res)


