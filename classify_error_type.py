from explain_by_type import *
from preprocess import *
from app import *
import re
import grammarpat

ab = re.compile(r"\w*'\w*|\w*’\w*")
loss_del = re.compile(r'\[ *- *([^\[\]]*?) *- *\]')
loss_add = re.compile(r'\{\ *\+ *([^\[\]]*?) *\+ *\}')
delandadd = re.compile(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}')
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

def grep_error_GEC(string,b_lists,lists,errors,mod_list,result,mode):
    error_id = len(errors)
    start = 0
    sent = string
    for before, matchobj in zip(b_lists, lists):
        idx = string.find(before, start)
        if matchobj[0]:
            if mode == 'GEC':
                after = '<span class="edit deletion edit{error_id}">{delete}</span> <span class="edit addition edit{error_id}">{insert}</span>'.format(
                    error_id=error_id, delete=matchobj[0], insert=matchobj[1])
            else:
                after = '<span class="edit deletion edit{error_id} active" data-edit="{error_id}" >{delete}</span> <span class="edit addition edit{error_id} active" data-edit="{error_id}">{insert}</span>'.format(
                    error_id=error_id, delete=matchobj[0], insert=matchobj[1])
                prev,sub = find_linggle(sent,'[-%s-]{+%s+}'%(matchobj[0],matchobj[1]))
                result[error_id]['linggle'] = ' '.join([word for word in [prev,matchobj[0]+'/'+matchobj[1],sub] if word.strip()])
        elif matchobj[2]:
            if mode == 'GEC':
                after = '<span class="edit deletion edit{error_id}">{delete}</span>'.format(error_id=error_id, delete=matchobj[2])
            else:
                after = '<span class="edit deletion edit{error_id} active" data-edit="{error_id}">{delete}</span>'.format(error_id=error_id, delete=matchobj[2])
                prev,sub = find_linggle(sent,'[-{delete}-]'.format(delete = matchobj[2]))
                result[error_id]['linggle'] = (prev+' ?'+matchobj[2]+' '+sub).strip()
        else:
            if mode == 'GEC':
                after = '<span class="edit addition edit{error_id}">{insert}</span>'.format(error_id=error_id, insert=matchobj[3])
            else:
                after = '<span class="edit addition edit{error_id} active" data-edit="{error_id}">{insert}</span>'.format(error_id=error_id, insert=matchobj[3])
                prev,sub = find_linggle(sent,'{+%s+}'%(matchobj[3]))
                result[error_id]['linggle'] = (prev+' ?'+matchobj[3]+' '+sub).strip()
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
        if mode != 'explain':
            grep_error_GEC(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\{\}]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\{\}]* *\+\}',correction),re.findall(r'\[- *([^\[\]]*?) *-\] *\{\+ *([^\[\]]*?) *\+\}|\[- *([^\[\]]*?) *-\]|\{\+ *([^\[\]]*?) *\+\}',correction),error_list,mod_list,result,mode)
            grep_error(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\{\}]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\{\}]* *\+\}',correction),error_list,accumulate_len,[])
        else:
            grep_error(correction,re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\{\}]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\{\}]* *\+\}',correction),error_list,accumulate_len,mod_list)
        accumulate_len += len(correction)+1
        while deletion.search(correction) or addition.search(correction):
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

