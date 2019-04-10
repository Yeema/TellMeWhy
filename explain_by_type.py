import re
from search_explanations import *
from grammarpat import find_patterns
from app import *
import grammarpat
import search_explanations
ab = re.compile(r"\w*'\w*|\w*’\w*")
loss_del = re.compile(r'\[ *- *([^\[\]]*?) *- *\]')
loss_add = re.compile(r'\{\ *\+ *([^\[\]]*?) *\+ *\}')
delandadd = re.compile(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}')
deletion = re.compile(r'\[- *([^\[\]]*?) *-\]')
addition = re.compile(r'\{\+ *([^\[\]]*?) *\+\}')
braces = re.compile(r'\[ *(.*?) *\]')
multi_delandadd = re.compile(r'(\[-([^\[\]]*?)-\] *\{\+([^\{\}]*?)\+\} *)+')

tmp_abbrs = {'it’s':'it is','what’s':'what is','how’s':'how is','they’re':'they are','we’re':'we are','i’m':'I am','don’t':'do not','doesn’t':'does not','didn’t':'did not','won’t':'will not','hadn’t':'had not','haven’t':'have not','wouldn’t':'would not','couldn’t':'could not','can’t':'can not','shouldn’t':'should not'}
abbrs = defaultdict()
for key,val in tmp_abbrs.items():
    abbrs[key.replace("’","'")] = val
    abbrs[key] = val
aux = set([('will','would'),('can','could'),('shall','should'),('may','might')])
pos_map = {'N':'N','J':'ADJ','V':'V','A':'ADJ'}
det_s = set("a,an,this,that,each,every,either,another,the,no".split(','))
det_p = set("the,some,these,those,much,many,any,all,most,enough,several,other,few,both".split(','))
vowel = set([i for i in 'aeiouh'])
vowelMap = {'a':['apple','apartment'],'e':['elephant','element'],'i':['igloo','island'],'o':['oven','octopus'],'u':['umbrella','unexpected error'],'h':['hour','honour']}

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

def explain_replace(correction,entails_sent,correction_split,threshold,done = False):
    output = []
#     output.append('[ replace type ]')
    if deletion.search(correction).group(1).lower() in grammarpat.allreserved:
        a_lemma = delandadd.search(correction).group(2)
        nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
        nextdigit,nextdigit_lemma = find_nextword(entails_sent,a_lemma,'C')
        if nextword.lower() in search_explanations.TIME or nextdigit.isdigit():
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
                    if all( pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in app.dictWord[part][head]] for pattern,head,part,_,p in gps):
                        gps = gps[::-1]
                        gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                    elif any( pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in app.dictWord[part][head]] for pattern,head,part,_,p in gps):
                        gps = [(pattern,head,part,ex,p) for pattern,head,part,ex,p in gps if pattern.replace(target[0],wedit) in [key[0].split('%')[0].strip() for key in app.dictWord[part][head]]]
                    else:
                        gps = gps[::-1]
                        gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                else:
                    headhalf = sorted([g for g in gps if g[4]>0],key = lambda x: app.pw_ratio[x[1]][(delandadd.search(correction).group(1),target[0])][x[4]],reverse = True)
                    tailhalf = [g for g in gps[::-1] if g[4]<1]
                    gps = headhalf + tailhalf
                for  pattern , head , part , _,_ in gps:
                    if head in app.dictWord[part]:
                        examples = select_examples(pattern,head,part)
                        if examples:
                            for ex in examples:
                                tmp = explain_pattern(ex,head,part,pattern)
                                output.append(tmp)
                                tmp = collocation_witout_compare(head,part,ex)
                                if tmp:
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
                                    output.append(tmp)
                                    last_pat = pattern.split()[-1]
                                    if part == 'V':
                                        if isTo and last_pat == 'inf':
                                            output.append(explain_INF())
                                        elif isTo and last_pat == '-ing':
                                            output.append(explain_ING())
                                        else:
                                            output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                        tmp = collocation_witout_compare(head,pos,ex)
                                    if tmp:
                                        output.append(tmp)

                                done = True
                                break
                if not done:
                    idioms_result = find_idioms_from_gps(gps)
                    if idioms_result:
                        output.append(idioms_result)
                    else:
                        output.append("<p>The usage of %s: %s</p>"%(gps[0][1],gps[0][0]))
            else:
                idioms = find_idioms(entails_sent,target)
                if idioms[0] and idioms[1]:
                    tmp = []
                    tmp.append('"<b>%s</b>" is a phrase.'%(idioms[0]))
                    tmp.append("This means that %s."%('\t'.join(list(app.dictPhrase[idioms[0]].values())[0][0]).strip()))
                    output.append("<p>%s</p>"%('</p><p>'.join(tmp)))
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
                    output.append('Verb Form Error!')
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
            output.append("<p>%s: %s</p><p>vs</p><p>%s: %s</p>"%(d_word,d_part,a_word,a_part))
        elif d_lemma in det_s.union(det_p) and a_lemma in det_s.union(det_p):
#             an -> a
            if d_lemma.lower() == 'an' and a_lemma.lower() == 'a':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma)
                if nextword[0] == 'h':
                    tmp = []
                    tmp.append("Before a word beginning with h, use a if the h is pronounced: <b>a house</b>, <b>a half</b>, <b>a horrible day</b>.")
                    tmp.append("Use an if the h is silent: <b>an hour</b>, <b>an honour</b>.")
                    tmp.append("If the h is pronounced but the syllable is unstressed, it is possible to use a or an (<b>a/an hotel</b>).")
                    tmp.append("However, the use of an here is considered old fashioned and most people use a.")
                    output.append('<p>%s</p>'%('</p><p>'.join(tmp)))
                else:
                    if nextword[0].lower() in ['u','o']:
                        output.append("In this case, %s is pronounced as y which is a consonant sound, use a (NOT an)."%(nextword[0].lower()))
                    else:
                        output.append("Always use a (NOT an) before a word beginning with a consonant sound.")
#             a -> an
            elif d_lemma.lower() == 'a' and a_lemma.lower() == 'an':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma)
                if nextword[0].lower() in vowel:
                    if nextword[0] == 'h':
                        output.append("Use an (NOT a) before words beginning with h when the h is not pronounced: <b>an honour</b> , <b>an hour</b>.")
                    else:
                        output.append("Always use an (NOT a) before a word beginning with a vowel sound: <b>an %s</b> or <b>an %s</b>."%(vowelMap[nextword[0].lower()][0],vowelMap[nextword[0].lower()][1]))
                elif nextword[0].isupper():
                    output.append("Use an (NOT a) before an abbreviation that begins with a vowel sound")
            elif d_lemma.lower() == 'the' or a_lemma.lower() == 'the':
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                nextdigit,nextdigit_lemma = find_nextword(entails_sent,a_lemma,'C')
                if nextword.lower() in search_explanations.TIME or nextdigit.isdigit():
                    time_error = explain_time_error(nextword.lower())
                    if time_error:
                        output.append(time_error)
                        done = True
                else:
                    output.append(dictDet[d_lemma])
                    output.append(dictDet[a_lemma])
            elif d_lemma.lower()=='any' and a_lemma.lower() in det_s.union(det_p):
                if a_lemma in ['each','every','all'] :
                    output.append('To refer to all the people or things in a group or category, use "each/every + singular countable noun" OR "all + plural countable noun".')
                    tmp = []
                    tmp.append('For example:')
                    tmp.append('Every house in the street had one or two broken windows.')
                    tmp.append('All students are required to register during the first week.')
                    output.append('<p>%s</p>'%('</p><p>'.join(tmp)))
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
            elif d_lemma.lower() in det_p and a_lemma.lower() in det_s:
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                if check_S(nextword,nextword_lemma):
                    output.append('<b>%s</b> is usually used in singular countable form.'%(a_lemma))
                    output.append(find_N_meaning(nextword))
                else:
                    output.append("%s -> %s :  this case hasn't handled yet."%(d_lemma,a_lemma))
            elif d_lemma.lower() in ['no','some'] and a_lemma.lower() == 'any':
                output.append('After negative words, you usaully use "any, anyone, anything, etc (Not some, someone, something, etc)".')
            elif 'at that moment' in ' '.join(entails_sent).lower():
                output.append(" When you are telling a story or reporting what happened, use <b>at that moment</b>\t:\tAt that moment the car skidded on the ice and went off the road.")
            elif d_lemma.lower() in det_s and a_lemma.lower() in det_p:
                nextword,nextword_lemma = find_nextword(entails_sent,a_lemma,'N')
                if check_S(nextword,nextword_lemma):
                    output.append('<b>%s</b> is usually used in singular countable form. Besides, <b>%s</b> is usually used in uncountable form or plural countables (NOT with singular countable form)'%(d_lemma,a_lemma))
                else:
                    output.append('<b>%s</b> is usually used in <b>uncountable form</b> such as %s.'%(a_lemma,nextword))
                    output.append(find_N_meaning(nextword,'U'))
            elif d_lemma.lower() in det_p and a_lemma.lower() in det_s:
                output.append('<b>%s</b> is usually used in plural countable form. Besides, <b>%s</b> is usually used in singular countable form.'%(d_lemma,a_lemma))
            else:
                output.append(dictDet[d_lemma.lower()])
                output.append(dictDet[a_lemma.lower()])

        elif not parts[0][0].upper() in pos_map or not any([part for part in ['v','a','n'] if d_lemma in app.dictWord[pos_map[part.upper()]]]):
            if tuple(sorted([d_lemma,a_lemma])) in aux:
                output.append('Tense error!')
            else:
                output.append('It is a spelling error. To be more precisely, the spelling of <b>%s</b> is correct!'%(delandadd.search(correction).group(2)))
        else:
            output.append(explain_voc_semantic_error(correction,d_lemma,d_part,a_lemma,a_part))
#             find collocation according to minipar
            tagging = geniatag(' '.join(entails_sent))
            gps = find_patterns(tagging,[a_word])
            tmp = find_collocations(gps,tagging,a_lemma,d_lemma)
            if tmp:
                output.append(tmp)
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
    if focus in det_p.union(det_s) or focus in grammarpat.allreserved:
        if any(t in search_explanations.MONTH for t in target) and focus.lower() in ['the','of']:
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
        elif any(t.lower() in search_explanations.TIME for t in target) and (focus.lower() in det_s or focus.lower() in grammarpat.allreserved):
            for t in target:
                if t.lower() in search_explanations.TIME or t.isdigit():
                    time_error = explain_time_error(t.lower())
                    if time_error:
                        output.append(time_error)
                        done = True
                        break
        elif focus in det_s:
            nextwordN,nextwordN_lemma = find_nextword(entails_sent,target[-1],'N')
            nextwordJ,nextwordJ_lemma = find_nextword(entails_sent,target[-1],'J')
    #             uncountable
            if check_uncountable(nextwordN):
                output.append('<b>%s</b> is uncountable so it must not be used with <b>%s</b>, whcih is usually paired with singular countable nouns.'%(nextwordN,focus))
                done = True
            elif check_P(nextwordN,nextwordN_lemma):
                output.append('<b>%s</b> is usually used in singular countable form.'%(focus))
                done = True
        elif focus in det_p:
            nextwordN,nextwordN_lemma = find_nextword(entails_sent,target[-1],'J')
            if nextwordN == 'certain':
                output.append("Do not use a determiner (e.g. some, the, their) before certain when it means ‘particular.")
                output.append(dictDet[focus])
                done = True
        elif focus != 'that' and not focus in grammarpat.allreserved:
            output.append(dictDet[focus])
            done = True
    if not done:
        gps = find_patterns(geniatag(' '.join(entails_sent)),target)
        if gps:
            gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
            isTo = focus=='to'
            if not any(p>0 and isTo  for _,_,part,_,p in gps):
                tmp = check_both(target,gps)
                if tmp:
                    gps = [tmp]
                else:
                    gps = gps[::-1]
                    gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][(focus,'')][x[4]],reverse = True)
            else:
                headhalf = sorted([g for g in gps if g[4]>0],key = lambda x: app.pw_ratio[x[1]][(focus,'')][x[4]],reverse = True)
                tailhalf = [g for g in gps[::-1] if g[4]<1]
                gps = headhalf + tailhalf
            for pattern , head , part , _,_ in gps:
                if head in  app.dictWord[part]:
                    examples = select_examples(pattern,head,part)
                    if examples:
                        for ex in examples:
                            last_pat = pattern.split()[-1]
                            if part == 'V':
                                if isTo and last_pat == '-ing':
                                    output.append(explain_ING())
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    output.append(tmp)
                                 
                                elif focus in grammarpat.allreserved:
                                    output.append(explain_VT_error(head,correction,pattern,ex))
                                else:
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    output.append(tmp)
                            else:
                                tmp = explain_pattern(ex,head,part,pattern)
                                output.append(tmp)
                            tmp = collocation_witout_compare(head,part,ex)
                            if tmp:
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
                                output.append(tmp)
                                last_pat = pattern.split()[-1]
                                if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                    output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                tmp = collocation_witout_compare(head,pos,ex)
                                if tmp:
                                    output.append(tmp)
                            done = True
                            break
                        if done:
                            break
            if not done:
                idioms_result = find_idioms_from_gps(gps)
                if idioms_result:
                    output.append(idioms_result)
                else:
                    output.append("<p>The usage of %s: %s</p>"%(gps[0][1],gps[0][0]))
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
        if nextwordN.lower() in search_explanations.TIME or nextdigit.isdigit():
            if focus.lower() =='the' or focus.lower() in det_s or focus.lower() in grammarpat.allreserved:
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
                rule += "<p>[people]</p>"
                tmp.append("the elderly")
                tmp.append("the British")
                rule += str_example%('</p><p>'.join(tmp))

                tmp = []
                rule += "<p>[stuff]</p>"
                tmp.append("the mysterious")
                tmp.append("the beautiful")
                output.append(rule+str_example%('</p><p>'.join(tmp)))
                done = True
        elif focus.lower() in det_p:
            output.append("Use a determiner before a plural countable noun such as %s"%(nextwordN))
            output.append(dictDet[focus.lower()])
            output.append(find_N_meaning(nextwordN))
            done = True
        elif focus.lower() in det_s:
            if focus.lower() != 'that':
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
        if focus.lower() in grammarpat.allreserved:
            if gps:
                gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
                isTo = target[0]=='to'
                if not any(p>0 for _,_,part,_,p in gps):
                    gps = gps[::-1]
                    gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                elif all(p>0 for _,_,part,_,p in gps):
                    gps = gps[::-1]
                    gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                else:
                    headhalf = sorted([g for g in gps if g[4]>0],key = lambda x: app.pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                    tailhalf = [g for g in gps[::-1] if g[4]<1]
                    gps = headhalf + tailhalf
                    
                for pattern , head , part , _,_ in gps:
                    if head in  app.dictWord[part]:
                        if app.dictWord[part][head]:
                            examples = select_examples(pattern,head,part)
                            if examples:
                                for ex in examples:
                                    tmp = explain_pattern(ex,head,part,pattern)
                                    output.append(tmp)
                                    last_pat = pattern.split()[-1]
                                    if part == 'V':
                                        if isTo and last_pat == 'inf':
                                            output.append(explain_INF())
                                        else:
                                            output.append(explain_VI_error(head,correction,pattern,ex))
                                    tmp = collocation_witout_compare(head,part,ex)
                                    if tmp:
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
                                        output.append(tmp)
                                        last_pat = pattern.split()[-1]
                                        if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                            output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                        tmp = collocation_witout_compare(head,pos,ex)
                                        if tmp:
                                            output.append(tmp)
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
                    output.append('<b>%s</b> is a phrase. Its definition is listed below. <ol><li>%s</li></ol>'%(phrase,'</li><li>'.join(['\t'.join(d).strip() for d in list(app.dictPhrase[phrase].values())[0][:2]])))
                    for p in app.phraseV[head].keys():
                        if phrase in p:
                            output.append(str_example%('For example: %s'%('  '.join([' '.join(app.phraseV[head][p][0][2][:2]) for p in app.phraseV[head].keys() if phrase in p ]))))
        else:
            if gps:
                gps = [(pattern,head,part,ex,1) if correction.find(ex) < threshold else (pattern,head,part,ex,-1) for pattern,head,part,ex in gps]
                if all(p>0 for _,_,part,_,p in gps):
                    gps = gps[::-1]
                elif all(p<0 for _,_,part,_,p in gps):
                    gps = gps[::-1]
                gps = sorted(gps,key = lambda x: app.pw_ratio[x[1]][('',focus)][x[4]],reverse = True)
                
                for pattern , head , part , _,_ in gps:
                    if head in  app.dictWord[part]:
                        examples = select_examples(pattern,head,part)
                        if examples:
                            for ex in examples:
                                tmp = explain_pattern(ex,head,part,pattern)
                                output.append(tmp)
                                tmp = collocation_witout_compare(head,part,ex)
                                if tmp:
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
                                        output.append(tmp)
                                        last_pat = pattern.split()[-1]
                                        if part == 'V' and last_pat != 'inf' and last_pat != '-ing':
                                            output.append(explain_VI_error(head,correction,pattern.replace(part,pos),ex))
                                        tmp = collocation_witout_compare(head,part,ex)
                                        if tmp:
                                            output.append(tmp)
                                    done = True
                                    break
                if not done:
                    idioms_result = find_idioms_from_gps(gps)
                    if idioms_result:
                        output.append(idioms_result)
                    else:
                        output.append("<p>The usage of %s: %s</p>"%(gps[0][1],gps[0][0]))
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
                        output.append('<b>%s</b> is a phrase. Its definition is listed below. <ol><li>%s</li></ol>'%(phrase,'</li><li>'.join([' '.join(d) for d in list(app.dictPhrase[phrase].values())[0][:2]])))
                        output.append(str_example%('For example: %s'%('  '.join([' '.join(app.phraseV[head][p][0][2][:2]) for p in app.phraseV[head].keys() if phrase in p ]))))
    return output



