from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal,LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
import pdfminer.layout as layout

import os
import re
from functools import cmp_to_key
import bisect
from collections import defaultdict

class my_box:
    def __init__(self,x0,x1,y0,y1):
        self.x0,self.x1,self.y0,self.y1=x0,x1,y0,y1
    def merge(self,obj):
        self.x0=min(self.x0,obj.x0)
        self.x1=max(self.x1,obj.x1)
        self.y0=min(self.y0,obj.y0)
        self.y1=max(self.y1,obj.y1)
    @classmethod
    def y_nest(cls,obj1,obj2):
        return (obj1.y0+0.001>=obj2.y0 and obj1.y1-0.001<=obj2.y1) or (obj1.y0-0.001<=obj2.y0 and obj1.y1+0.001>=obj2.y1)
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1)

class text_box(my_box):
    text=""
    def __init__(self,x0,x1,y0,y1,text):
        my_box.__init__(self,x0,x1,y0,y1)
        self.text=text.rstrip()
    def mergeable(self,obj):
        return my_box.y_nest(self,obj)
    def merge(self,obj):
        my_box.merge(self,obj)
        self.text=self.text.rstrip()+" "+obj.text.rstrip() if self.x0<obj.x0 else obj.text.rstrip()+" "+self.text.rstrip()
    def get_text(self):
        return self.text
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj.get_text())

class line_box(text_box):
    _line=[]
    def __init__(self,x0,x1,y0,y1,lst):
        self._line=[text_box.cast(x) for x in lst]
        text_box.__init__(self,x0,x1,y0,y1,"\n".join([x.get_text() for x in self._line]))
    def __len__(self):
        return len(self._line)
    def __iter__(self):
        return iter(self._line)
    def __getitem__(self,index):
        return self._line[index]
    def mergeable(self,obj):
        if len(self)<len(obj):
            x=self
            y=obj
        else :
            y=self
            x=obj
        if len(x)==0:
            return 0
        if not my_box.y_nest(self,obj):
            return -1
        start=0
        for i in range(0,len(y)):
            if x[0].mergeable(y[i]):
                start=i
                break
        if start+len(x)>len(y):
            return -1
        for i in range(1,len(x)):
            if not y[i+start].mergeable(x[i]):
                return -1
        return start
    def merge(self,obj,idx):
        if len(self)<len(obj):
            x=self
            self=line_box.cast(obj)
        else:
            x=obj
        for i in range(1,len(x)):
            self[i+idx].merge(x[i])
        my_box.merge(self,obj)
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj)

class ReferencesReader:
    _pdf_pages=[]#储存所有页面的box
    _references_page=[]#储存references页面的box

    #由于论文的特点，正文部分的box再竖直方向[x轴坐标]（几乎）是对齐的，
    #使用字典统计左边界为x0，右边界为x1的box的总面积有多大，
    #若该面积占所有box总面积的大部分，则认为左边界为x0，右边界为x1的box为正文box
    #取所有正文box的y值上界和y值下界得到正文部分的上界和下界
    #若y值超过上界或下界的box认为属于页眉或页脚内容
    _x_dict=defaultdict(float)     #key:box的左右边界,value:box面积
    tol_size=0    #box总面积
    min_y=0xEAB0  #y值下界
    max_y=-0xEAB0 #y值上界
    def __init__(self,pdf_path,pdf_name):
        os.chdir(pdf_path)
        fp=open(pdf_name,'rb')

        #来创建一个pdf文档分析器
        parser=PDFParser(fp)
        #创建一个PDF文档对象存储文档结构
        document=PDFDocument(parser)
        #连接分析器，与文档对象
        parser.set_document(document)
        document.set_parser(parser)
        #提供初始化密码，如果没有密码，就创建一个空的字符串
        document.initialize()

        # 检查文件是否允许文本提取
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            # 创建一个PDF资源管理器对象来存储共赏资源
            rsrcmgr=PDFResourceManager()
            # 设定参数进行分析
            laparams=LAParams()
            # 创建一个PDF设备对象
            device=PDFPageAggregator(rsrcmgr,laparams=laparams)
            # 创建一个PDF解释器对象
            interpreter=PDFPageInterpreter(rsrcmgr,device)
            # 处理每一页
            
            for page in document.get_pages():
                interpreter.process_page(page)
                # 接受该页面的LTPage对象
                LTlayout=device.get_result()

                box_list=[x for x in LTlayout if isinstance(x,LTTextBoxHorizontal) and len(x)>0]#获得所有文本box
                if len(box_list)==0:
                    continue
                self._pdf_pages.append(box_list)#将该页添加到_pdf_pages


    def get_body(self):#获取文章主体部分边界值（获得页眉和页脚的边界值）
        for page in self._pdf_pages:
            for bx in page:
                size=(bx.x1-bx.x0)*(bx.y1-bx.y0)
                self.tol_size+=size
                self._x_dict[(int(bx.x0),int(bx.x1))]+=size

        rk=sorted([x/self.tol_size for x in self._x_dict.values()],reverse=True)
        now_size=0
        for x in rk:
            now_size+=x
            threshold_size=x
            if now_size>0.5:
                break

        for page in self._pdf_pages:
            for bx in page:
                if self._x_dict[(int(bx.x0),int(bx.x1))]/self.tol_size>threshold_size:
                    self.min_y=min(self.min_y,bx.y0)
                    self.max_y=max(self.max_y,bx.y1)
        
        if self.min_y==0xEAB0:#如果仍未初始值，认为出现异常，将min_y置为负无穷，max_y置为正无穷防止影响之后的操作
            self.min_y=-0xEAB0
        if self.max_y==-0xEAB0:
            self.max_y==0xEAB0

    
    def find_references(self):
        for page in self._pdf_pages:
            tmp=[line_box.cast(bx) for bx in page if bx.y1>=self.min_y and bx.y0<=self.max_y]
            for bx in page:
                if bx.get_text().strip().lower().find("references")==0:
                    self._references_page=[]
                    break
            self._references_page.append(tmp)
    

    def merge_box(self,page):
        if len(page)==0:
            return
        tmp=sorted(page,key=lambda x:x.y0)
        page=[]
        for x in tmp:
            ch=False
            if len(page)>0:
                t1=self._x_dict[(int(x.x0),int(x.x1))]
                t2=self._x_dict[(int(page[-1].x0),int(page[-1].x1))]
                if max(t1,t2)<self._x_dict[(int(min(x.x0,page[-1].x0)),int(max(x.x1,page[-1].x1)))]:
                    i=page[-1].mergeable(x)
                    if i!=-1:
                        page[-1].merge(x,i)
                        print("merging.............")
                        ch=True
            if ch==False:
                page.append(x)


        

    
    def split_references(self):
        lines=[]
        
        def sort_box(x,y):
            if(x.x1<y.x0):
                return -1
            elif (x.x0>y.x1):
                return 1
            else:
                return y.y0-x.y0#右下角是原点，右向是x轴，向上是y轴

        for page in self._references_page:
            self.merge_box(page)
            first_line_in_page=True
            page.sort(key=cmp_to_key(sort_box))
            for box in page:
                for line in box:
                    tmp=text_box.cast(line)
                    if len(lines)==0:
                        lines.append(tmp)
                    else:
                        if lines[-1].mergeable(tmp):#pdfminer 有时会把空格当作换行，在这里修正
                            lines[-1].merge(tmp)              
                        else:
                            lines.append(tmp)
                    if line.get_text().strip().lower().find("references")==0:
                        lines=[]
                    first_line_in_page=False

        
        tmp=[]
        references_list=[]
        def end_with_period(s):
            tmp=s.rstrip()
            if s[-1]!='.':
                return False
            return s[-3:-1].isalnum()
        for i,line in enumerate(lines):
            tmp.append(line)
            if end_with_period(line.get_text()) or i==len(lines)-1:
                for i in range(1,len(tmp)):
                    tmp[0].merge(tmp[i])
                references_list.append(tmp[0])
                tmp=[]
        for x in references_list:
            print(x.get_text())
