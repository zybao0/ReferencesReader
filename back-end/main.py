#!/usr/bin/env python3
from ReferencesReader import ReferencesReader
from ReferencesReader_sql import ReferencesSQL
import crawler
import time
import json
import hashlib
from flask import Flask,request
from werkzeug.utils import secure_filename
app = Flask(__name__)

@app.route('/upload',methods=['POST'])
def upload():
    f=request.files['file']
    data=f.read()
    file_md5=hashlib.md5(data).hexdigest()

    sql=ReferencesSQL()
    res=sql.query_references(file_md5)
    print("SQL",res)
    if len(res)==0:
        f.seek(0)
        reader=ReferencesReader(f)
        sql.add_references(file_md5,reader)
        res=[x for x in reader]
        print("analyse",reader)
    return json.dumps(res)


@app.route('/querybib',methods=['POST'])
def querybib():
    sql=ReferencesSQL()
    data=json.loads(request.data)
    print(data)
    res=[]
    for x in data["querylist"]:
        bib=sql.query_bibtex(x)
        print("SQL",bib)
        if bib is None :
            bib=crawler.get_bib_from_baiduxueshu(x)
            print("crawler",bib)
            sql.add_bibtex(x,bib)
            time.sleep(1)
        res.append({"RawReference":x,"Bib":bib})
    return json.dumps(res)

if __name__=='__main__':

    app.run(debug=True)



# for x in reader:
#     print(x)
#     bib=crawler.get_bib_from_baiduxueshu(x)
#     print(bib)
#     time.sleep(3)
#     print()