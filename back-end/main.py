#!/usr/bin/env python3
from ReferencesReader import ReferencesReader
from ReferencesReader_sql import ReferencesSQL
import crawler
import time
import json
import hashlib
from flask import Flask,request,render_template
from werkzeug.utils import secure_filename
app = Flask(__name__)

@app.route('/api/upload',methods=['POST'])
def upload():
    f=request.files['file']
    data=f.read()
    file_md5=hashlib.md5(data).hexdigest()

    sql=ReferencesSQL()
    res=sql.query_references(file_md5)
    if len(res)==0:
        f.seek(0)
        reader=ReferencesReader(f)
        sql.add_references(file_md5,reader)
        res=[x for x in reader]
    return json.dumps(res)


@app.route('/api/querybib',methods=['POST'])
def querybib():
    sql=ReferencesSQL()
    data=json.loads(request.data)
    res=[]
    for x in data["querylist"]:
        bib=sql.query_bibtex(x)
        if bib is None :
            bib=crawler.get_bib_from_baiduxueshu(x)
            sql.add_bibtex(x,bib)
            time.sleep(1)
        res.append({"RawReference":x,"Bib":bib})
    return json.dumps(res)

@app.route("/")
def index():
   return app.send_static_file('index.html')

@app.route('/<path:fallback>')
def fallback(fallback):
    if fallback.startswith('css/') or fallback.startswith('js/') or fallback.startswith('img/') or fallback == 'favicon.ico':
        return app.send_static_file(fallback)
    else:
        return app.send_static_file('index.html')

if __name__=='__main__':
    app.run(debug=True)