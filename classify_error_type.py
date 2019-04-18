from explain_by_type import *
from preprocess import *
from app import *
import re
import grammarpat
from nltk.tokenize import word_tokenize

ab = re.compile(r"\w*'\w*|\w*’\w*")
loss_del = re.compile(r'\[ *- *([^\[\]]*?) *- *\]')
loss_add = re.compile(r'\{\ *\+ *([^\{\}]*?) *\+ *\}')
delandadd = re.compile(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\{\}]*?) *\+\}')
deletion = re.compile(r'\[- *([^\[\]]*?) *-\]')
addition = re.compile(r'\{\+ *([^\[\]]*?) *\+\}')
braces = re.compile(r'\[ *(.*?) *\]')
multi_delandadd = re.compile(r'(\[-([^\[\]]*?)-\] *\{\+([^\{\}]*?)\+\} *)+')

def leave_error(correction,lists):
    head = lists[0]
    tail = lists[1]
    input_cor = ""
    input_split = []
    if head or tail:
        if head and tail:
            head = head
            tail = tail
            start = correction.find(head)
            idx = start + len(head)
        elif head:
            head = head
            start = correction.find(head)
            idx = start + len(head)
        elif tail:
            tail = tail
            start = correction.find(tail)
            idx = start + len(tail)
        if idx < len(correction):
            input_cor = correction[:idx+1]+ ' '.join(rephrase(correction[idx:]))
            input_split = input_cor.split()
        return input_cor,input_split,start

def myreplace(string,idx,before,after):
    if idx > -1:
        if len(string) > idx+len(before):
            string = string[:idx] + after + string[idx+len(before):]
        else:
            string = string[:idx] + after
        return string
    else:
        return
    
def find_linggle(sent,key):
    sent = sent.split()
    idx = sent.index(key)
    prev = ""
    sub = ""
    i = idx-1
    while i >= 0 :
        if sent[i][:2] != '[-':
            prev = sent[i].replace('{+','').replace('+}','').strip()
            break
        elif sent[i][-2:]!='-]':
            prev = addition.search(sent[i]).group(1)
            break
        i -= 1

    i = idx+1
    while i < len(sent):
        if sent[i][:2]!='[-':
            sub = sent[i].replace('{+','').replace('+}','').strip()
            break
        elif sent[i][-2:]!='-]':
            sub = addition.search(sent[i]).group(1)
            break
        i += 1
    return prev,sub

def only_alpha(word):
    return ' '.join([w for w in word_tokenize(word) if w.isalpha()]).strip()

def grep_error(string,b_lists,lists,errors,mod_list,result,mode):
    error_id = len(errors)
    start = 0
    sent = string
    for before, matchobj in zip(b_lists, lists):
        idx = string.find(before, start)
        if matchobj[0]:
            if mode != 'linggle' and error_id>0:
                after = '<span class="edit deletion edit{error_id} {mode}" data-edit="{error_id}">{delete}</span> <span class="edit addition edit{error_id} {mode}" data-edit="{error_id}">{insert}</span>'.format(
                error_id=error_id, delete=matchobj[0], insert=matchobj[1],mode = mode)
            else:
                after = '<span class="edit deletion edit{error_id} {mode} active" data-edit="{error_id}" >{delete}</span> <span class="edit addition edit{error_id} {mode} active" data-edit="{error_id}">{insert}</span>'.format(
                    error_id=error_id, delete=matchobj[0], insert=matchobj[1],mode=mode)
            prev,sub = find_linggle(sent,'[-%s-]{+%s+}'%(matchobj[0],matchobj[1]))
            prev = only_alpha(prev)
            sub = only_alpha(sub)
            result[error_id]['linggle'] = ' '.join([word for word in [prev,matchobj[0]+'/'+matchobj[1],sub] if word.strip()])
        elif matchobj[2]:         
            if mode != 'linggle' and error_id>0:
                    after = '<span class="edit deletion edit{error_id} {mode}" data-edit="{error_id}">{delete}</span>'.format(error_id=error_id, delete=matchobj[2],mode = mode)
            else:
                after = '<span class="edit deletion edit{error_id} {mode} active" data-edit="{error_id}">{delete}</span>'.format(error_id=error_id, delete=matchobj[2],mode = mode)
            
            prev,sub = find_linggle(sent,'[-{delete}-]'.format(delete = matchobj[2]))
            prev = only_alpha(prev)
            sub = only_alpha(sub)
            result[error_id]['linggle'] = (prev+' ?'+matchobj[2]+' '+sub).strip()
        else:
            if mode != 'linggle' and error_id>0:
                after = '<span class="edit addition edit{error_id} {mode}" data-edit="{error_id}">{insert}</span>'.format(error_id=error_id, insert=matchobj[3],mode = mode)
            else:
                after = '<span class="edit addition edit{error_id} {mode} active" data-edit="{error_id}">{insert}</span>'.format(error_id=error_id, insert=matchobj[3],mode = mode)
            prev,sub = find_linggle(sent,'{+%s+}'%(matchobj[3]))
            prev = only_alpha(prev)
            sub = only_alpha(sub)
            result[error_id]['linggle'] = (prev+' ?'+matchobj[3]+' '+sub).strip()
        string = myreplace(string,idx,before, after)
        errors.append(before)
        error_id = len(errors)
        start = idx+1
    mod_list.append(string)

def explain(corrections,result,mode):
    mod_list = []
    prevs = []
    error_count = 0
    error_list = []
    final_list = []
    for correction in sent_tokenize(corrections):
        print(correction)
        correction = beautify(correction,mode)
        if not correction and mode == 'Example':
            result['except']['body'] = "We do not explain multiple words edit in a correction symbol!"
            return 
        final_list.append(correction)
        entails_sent = rephrase(correction)
        grep_error(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\{\}]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\{\}]* *\+\}',correction),re.findall(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}|\[- *([^\[\]]*?) *-\]|\{\+ *([^\[\]]*?) *\+\}',correction),error_list,mod_list,result,mode)
        print('edits1:\t',deletion.search(correction) or addition.search(correction),correction)
        while deletion.search(correction) or addition.search(correction):
            print('edits2:\t',deletion.search(correction) or addition.search(correction),correction)
            if prevs:
                if prevs[0] in grammarpat.allreserved or prevs[1] in grammarpat.allreserved:
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
                transform = 'Replace ' + ' '.join(re.findall(deletion, tmp)) + ' with ' + before
                after = before
                case1 = correction.find(tmp)
                replacelist[0] = [tmp,after,transform]
                prevs = ( ' '.join(re.findall(deletion, tmp)),before)
            if deletion.search(correction):
                tmp = deletion.search(correction).group(0)
                after = ''
                case2 = correction.find(tmp)
                transform = 'Omit ' + deletion.search(correction).group(1)
                replacelist[1] = [tmp,after,transform]
                prevs = ( deletion.search(correction).group(1)  ,'')
            if addition.search(correction):
                tmp = addition.search(correction).group(0)
                after = addition.search(correction).group(1)
                case3 = correction.find(tmp)
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
            correction = ' '.join(correction.replace(replacelist[idx][0],replacelist[idx][1],1).split())
    # result[0]['beautify'] = ' '.join(final_list)
    result[0]['sent'] = ' '.join(mod_list)
    print('197\tdone')

def beautify(s,mode):
#     lemmarize abbr.
    for a in re.findall(ab,s):
        if a.lower() in abbrs:
            s = s.replace(a,abbrs[a.lower()])
    #tokens = [ss for ss in word_tokenize(s) if ss.strip()]
    old_tokens = [ss for ss in s.split() if ss.strip()]
    tokens = []
    for old in old_tokens:
        if '[' in old or '{' in old:
            if '[' in old and '{' in old:
                tmp = multi_delandadd.search(old).group(0).strip()
                if old.replace(tmp,'').strip():
                    edit_idx = old.find(tmp)
                    symbol_idx = old.find(old.replace(tmp,'').strip())
                    old = old.replace(tmp,'').strip()
                    if edit_idx > symbol_idx:
                        tokens.append(old)
                        tokens.append(tmp)
                    else:
                        old = old.replace(tmp,'').strip()
                        tokens.append(tmp)
                        tokens.append(old)
                else:
                    tokens.append(old)
            elif '[' in old:
                tmp = deletion.search(old).group(0).strip()
                if old.replace(tmp,'').strip():
                    edit_idx = old.find(tmp)
                    symbol_idx = old.find(old.replace(tmp,'').strip())
                    old = old.replace(tmp,'').strip()
                    if edit_idx > symbol_idx:
                        tokens.append(old)
                        tokens.append(tmp)
                    else:
                        old = old.replace(tmp,'').strip()
                        tokens.append(tmp)
                        tokens.append(old)
                else:
                    tokens.append(old)
            else:
                tmp = addition.search(old).group(0).strip()
                if old.replace(tmp,'').strip():
                    edit_idx = old.find(tmp)
                    symbol_idx = old.find(old.replace(tmp,'').strip())
                    old = old.replace(tmp,'').strip()
                    if edit_idx > symbol_idx:
                        tokens.append(old)
                        tokens.append(tmp)
                    else:
                        old = old.replace(tmp,'').strip()
                        tokens.append(tmp)
                        tokens.append(old)
                else:
                    tokens.append(old)
        else:
            tokens.append(old)
            
    s = ' '.join(tokens)
    s_tmp = s
    while loss_add.search(s_tmp) or loss_del.search(s_tmp):
        if loss_del.search(s_tmp):
            head = loss_del.search(s_tmp).group(0)
            tail = loss_del.search(s_tmp).group(1)
            if len(tail.split())>1:
                if mode != 'Example':
                    s = s.replace(head,tail) 
                else:
                    return
            else:
                s = s.replace(head,'[-'+tail+'-]')
                s_tmp = s_tmp.replace(head,tail)
        if loss_add.search(s_tmp):
            head = loss_add.search(s_tmp).group(0)
            tail = loss_add.search(s_tmp).group(1)
            if len(tail.split())>1:
                if mode != 'Example':
                    s = s.replace(head,'') 
                else:
                    return
            else:
                s = s.replace(head,'{+'+tail+'+}')
                s_tmp = s_tmp.replace(head,tail)
        
        if delandadd.search(s):
            d_head = loss_del.search(s).group(0)
            d_tail = loss_del.search(s).group(1)
            a_head = loss_add.search(s).group(0)
            a_tail = loss_add.search(s).group(1)
            if len(d_tail.split())>1 or len(a_tail.split())>1:
                if mode!='Example':
                    s = s.replace(delandadd.search(s).group(0),d_tail) 
                else:
                    return
            else:
                s = s.replace(delandadd.search(s).group(0),'[-%s-]{+%s+}'%(d_tail,a_tail))
    return ' '.join([ss.strip() for ss in s.split()])

