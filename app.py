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
@app.route('/')	
def index():
    return render_template('template.html')

@app.route('/query', methods=['POST'])
def query_entry():
    text = request.form['text_field']
    text = beautify(text)
    res = {}
    if re.findall(r'\[- *[^\[\]]* *-\] *\{\+ *[^\[\]]* *\+\}|\[- *[^\[\]]* *-\]|\{\+ *[^\[\]]* *\+\}',text):
        result = defaultdict(lambda: defaultdict())
        explain(text,result,'explain')
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
    correction = edits['word_diff_by_sent']
    res = {}
    if correction:
        correction = beautify(correction[0])
        result = defaultdict(lambda: defaultdict())
        explain(correction,result,'GEC')
        htmlize(result,res,'GEC')
    return jsonify(res)

@app.route('/linggle_go',methods=['POST'])
def query_linggle():
    string = request.form['sent']
    edits = requests.get(GEC_API.format(string))
    edits = eval(edits.text)
    correction = edits['word_diff_by_sent']
    res = {}
    if correction:
        correction = beautify(correction[0])
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
#     {'a':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','b':'<ul><li>'+'</li><li>'.join(['bbb','bbbb']),'c':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','d':'<ul><li>'+'</li><li>'.join(['bbb','bbbb']),'e':'<ul><li>'+'</li><li>'.join(['aaa','aaaa'])+'</li></ul>','f':'<ul><li>'+'</li><li>'.join(['bbb','bbbb'])}
    if mode != 'linggle':
        for id,mod in result.items():
            # res['%d\tpos'%(id)] = '%d\t%d'%(mod['pos'][0],mod['pos'][1])
            tmp = '<ul><li> %s </li></ul>'%('</li><li>'.join([r for r in mod['body'] if r.replace('<p></p>','').strip()]))
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