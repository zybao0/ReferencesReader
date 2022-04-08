import sqlite3
import base64
class ReferencesSQL:
    def __init__(self):
        self.con=sqlite3.connect("ReferencesReader.db")
        self.cur=self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS Paper_to_References(paper TEXT,reference BLOB)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS Reference_to_Bibtex(reference BLOB PRIMARY KEY,bibtex BLOB)")
        self.con.commit()

    def query_references(self,paper_md5):
        self.cur.execute("SELECT reference FROM Paper_to_References WHERE paper=(?)",(paper_md5,))
        tmp=self.cur.fetchall()
        return [base64.b64decode(x[0]).decode() for x in tmp]

    def add_references(self,paper_md5,references):
        for x in references:
            #use base64 to avoid sql injection
            reference_base64=base64.b64encode(x.encode())
            self.cur.execute("INSERT INTO Paper_to_References VALUES(?,?)",(paper_md5,reference_base64))
        self.con.commit()

    def query_bibtex(self,reference):
        reference_base64=base64.b64encode(reference.encode())
        self.cur.execute("SELECT bibtex FROM Reference_to_Bibtex WHERE reference=(?)",(reference_base64,))
        tmp=self.cur.fetchone()
        return base64.b64decode(tmp[0]).decode() if tmp is not None else tmp

    def add_bibtex(self,reference,bibtex):
        reference_base64=base64.b64encode(reference.encode())
        bibtex_base64=base64.b64encode(bibtex.encode())
        self.cur.execute("INSERT or IGNORE INTO Reference_to_Bibtex VALUES(?,?)",(reference_base64,bibtex_base64))
        self.con.commit()
        
    def __del__(self):
        self.cur.close()
        self.con.close()