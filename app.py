# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify
import spacy
import operator
from nltk.stem.lancaster import LancasterStemmer
from collections import Counter,defaultdict
import geniatagger
from geniatagger import GeniaTagger
from nltk import word_tokenize, pos_tag
from nltk.tokenize import sent_tokenize
import requests
import json
from linggle_api import Linggle
from classify_error_type import *

GEC_API = 'https://whisky.nlplab.cc/translate/?text={}'


app = Flask(__name__)
tagger = GeniaTagger('/home/nlplab/yeema/geniataggerPython/geniatagger-3.0.2/geniatagger')
ling = Linggle()

dictWord = defaultdict(lambda: defaultdict(list))
phraseV = defaultdict(lambda: defaultdict(list))
dictPhrase = defaultdict(lambda: defaultdict(list))
dictDef = defaultdict(lambda: defaultdict(list))
miniparCol = defaultdict(lambda: defaultdict(lambda: Counter()))
pw = defaultdict(lambda: defaultdict(lambda:Counter()))
pw_ratio = defaultdict(lambda: defaultdict(lambda:Counter()))
LCE = eval(open('/home/nlplab/yeema/ErrorExplaination/LCE.json').read())
dictSimilar = defaultdict()

@app.route('/')	
def index():
    return render_template('template.html')

@app.route('/query', methods=['POST'])
def query_entry():
    text = request.form['text_field']
    text = beautify(text)
    res = {'sent':text,'html':'<p class="default-intro">'+
                              '<p>Please submit your writings with edits! </p>'+
                              '<p>Usage1: Submit <b>a</b> problem causing word.</p>'+
                              '<p>Usage2: There are three types of edits. Enter them in the following formats.</p>'+
                              '<b>Replacement:</b> He <b>[-borrowed-]{+lent+}</b> me some of his books.<br>'+
                              '<b>Omission:</b> We discussed <b>[-about-]</b> the issue.<br>'+
                              '<b>Insertion:</b> School finishes at five in <b>{+the+}</b> afternoon.'+
                              '</p>'}
    if re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',text):
        result = defaultdict(lambda: defaultdict())
        explain(text,result,'Example')
        htmlize(result,res,'Example')
    else:
        if text.strip() in LCE:
            lookup_LCE(text.strip(),res)
    
    return jsonify(res)
        
    

@app.route('/GEC',methods=['POST'])
def query_GEC():
    string = request.form['sent']
    edits = requests.get(GEC_API.format(string))
    edits = eval(edits.text)
    # correction = edits['word_diff']
    correction = '\n'.join(edits['word_diff_by_sent'])
    res = {'sent': correction.replace('\n',''),'html':'<p class="default-intro">'+'Your writings are perfect without any errors!<br>Please submit another essays, thanks!'+'</p>'}
    if correction:
        if re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',correction):
            correction = beautify(correction)
            result = defaultdict(lambda: defaultdict())
            explain(correction,result,'GEC')
            htmlize(result,res,'GEC')
    return jsonify(res)

@app.route('/linggle_go',methods=['POST'])
def query_linggle():
    string = request.form['sent']
    edits = requests.get(GEC_API.format(string))
    edits = eval(edits.text)
    correction = '\n'.join(edits['word_diff_by_sent'])
    res = {'sent': correction.replace('\n','')}
    if correction:
        if re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',correction):
            correction = beautify(correction)
            result = defaultdict(lambda: defaultdict())
            explain(correction,result,'linggle')
            htmlize(result,res,'linggle')
    return jsonify(res)

@app.route('/linggle', methods=['POST'])
def linggle():
    query = request.form['sent']
    return jsonify(ling[query])

def htmlize(result,res,mode):
    myPanel = ''
    if mode != 'linggle':
        first = True
        for id,mod in result.items():
            # res['%d\tpos'%(id)] = '%d\t%d'%(mod['pos'][0],mod['pos'][1])
            if 'body' in mod:
                tmp = '<ul><li> %s </li></ul>'%('</li><li>'.join([r for r in mod['body'] if r.replace('<p></p>','').strip()]))
                res[str(id)] = mod['linggle']
                if first:
                    first = False
                    myPanel += '<div class="card shadow-sm rounded bg-white">'+'<div class="card-header" id="heading%d">'%(id)+'<h2 class="mb-0">'+'<button class="btn collapsed" type="button" data-toggle="collapse" data-target="#collapse%d" aria-expanded="false" aria-controls="collapse%d" data-edit="edit%d">'%(id,id,id)+'%s'%(mod['header'])+ '</button>'+'</h2>'+'</div>'+'<div id="collapse%d" class="collapse show" aria-labelledby="heading%d" data-parent="#accordion%s" data-edit="edit%d">'%(id,id,mode,id)+'<div class="card-body">'+'%s'%(tmp)+'</div>'+'</div>'+'</div>'
                else:
                    myPanel += '<div class="card shadow-sm rounded bg-white">'+'<div class="card-header" id="heading%d">'%(id)+'<h2 class="mb-0">'+'<button class="btn collapsed" type="button" data-toggle="collapse" data-target="#collapse%d" aria-expanded="false" aria-controls="collapse%d" data-edit="edit%d">'%(id,id,id)+'%s'%(mod['header'])+ '</button>'+'</h2>'+'</div>'+'<div id="collapse%d" class="collapse" aria-labelledby="heading%d" data-parent="#accordion%s" data-edit="edit%d">'%(id,id,mode,id)+'<div class="card-body">'+'%s'%(tmp)+'</div>'+'</div>'+'</div>'
        res['html'] = myPanel.replace('<li></li>','')
    else:
        for id, mod in result.items():
            res[str(id)] = mod['linggle']
    res['sent'] = result[0]['sent']    

def lookup_LCE(word,res):
    explanations = LCE[word]
    rows = ""
    for explanation in explanations:
        for ex in explanation:
            if ex[0] == 'Explain':
                rows+='<tr class = "table-info"><th scope="row">{category}</th><td>{example}</td></tr>'.format(category = ex[0],example = ex[1])
            else:
                rows+='<tr><th scope="row">{category}</th><td>{example}</td></tr>'.format(category = ex[0],example = ex[1])
    res['sent'] = word
    res['html'] = '<table class="table"><tbody>{row_info}</tbody></table>'.format(row_info = rows)


def init_DB():
    tmp_dictWord = eval(open('/home/nlplab/yeema/ErrorExplaination/GPs.linggle.extend.txt', 'r').read())
    tmp_phrase = eval(open('/home/nlplab/yeema/ErrorExplaination/phrase.txt', 'r').read())
    tmp_dictDef = eval(open('/home/nlplab/yeema/ErrorExplaination/cambridge.gps.semanticDict_word_v5.json').read())
    tmp_dictPhrase = eval(open('/home/nlplab/yeema/ErrorExplaination/cambridge.gps.semanticDict_phrase_v5.json').read())
    tmp_miniparCol = eval(open('/home/nlplab/yeema/grammarpat/minipar.collocation.v3.json').read())
    tmp_pw = open('/home/nlplab/yeema/problemWords/problem.col.v2').readlines()
    tmp_dictSimilar = eval(open('/home/nlplab/yeema/ErrorExplaination/evaluation/longman_similar_word_explanation.json').read())

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
    
    for key,val in tmp_dictSimilar.items():
        dictSimilar[tuple(key.split('\t'))] = val
                
init_DB()
app.run(debug=True)