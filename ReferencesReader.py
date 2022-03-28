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
    def y_nest(cls,obj1,obj2):#判断两个box在y方向是否形成嵌套关系
        return (obj1.y0+0.001>=obj2.y0 and obj1.y1-0.001<=obj2.y1) or (obj1.y0-0.001<=obj2.y0 and obj1.y1+0.001>=obj2.y1)
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1)

class text_box(my_box):
    text=""
    def __init__(self,x0,x1,y0,y1,text):
        my_box.__init__(self,x0,x1,y0,y1)
        self.text=text.rstrip()
    @classmethod
    def mergeable(cls,obj1,obj2):
        return my_box.y_nest(obj1,obj2)
    def merge(self,obj):
        my_box.merge(self,obj)
        self.text=self.text.rstrip()+" "+obj.text.rstrip() if self.x0<obj.x0 else obj.text.rstrip()+" "+self.text.rstrip()
    def get_text(self):
        return self.text
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj.get_text())

class line_box(my_box):
    _lines=[]
    def __init__(self,x0,x1,y0,y1,lst):
        self._lines=[text_box.cast(x) for x in lst]
        my_box.__init__(self,x0,x1,y0,y1)
    def __len__(self):
        return len(self._lines)
    def __iter__(self):
        return iter(self._lines)
    def __getitem__(self,index):
        return self._lines[index]
    @classmethod
    def mergeable(cls,obj1,obj2):#判断两个box是否可以合并（是否是行在高度方向上重叠）
        if len(obj1)>len(obj2):
            obj1,obj2=obj2,obj1
        if len(obj1)==0:
            return True
        if not my_box.y_nest(obj1,obj2):
            return False
        start=-1
        for i in range(0,len(obj2)):
            if text_box.mergeable(obj1[0],obj2[i]):
                start=i
                break
        if start==-1 or start+len(obj1)>len(obj2):
            return False
        for i in range(1,len(obj1)):
            if not text_box.mergeable(obj1[i],obj2[i+start]):
                return False
        return True
    def merge(self,obj):#将两个box合并
        self._lines+=[x for x in obj]
        my_box.merge(self,obj)
    def sort(self):#对行按照y1从大到小排序（list里靠前的在pdf的上方（y1值较大））
        self._lines.sort(key=lambda x:x.y1,reverse=True)
    def merge_lines(self):#把一个box内的相同高度的行合并
        self.sort()
        tmp=[]
        for x in self._lines:
            if len(tmp)>0 and text_box.mergeable(tmp[-1],x):#pdfminer 有时会把空格当作换行，在这里修正
                tmp[-1].merge(x)
            else:
                tmp.append(x)
        self._lines=tmp
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
        page.sort(key=lambda x:x.y0)
        tmp=[]
        for x in page:
            if len(tmp)>0:
                t1=self._x_dict[(int(x.x0),int(x.x1))]
                t2=self._x_dict[(int(tmp[-1].x0),int(tmp[-1].x1))]
                t3=self._x_dict[(int(min(x.x0,tmp[-1].x0)),int(max(x.x1,tmp[-1].x1)))]
                if max(t1,t2)<t3:#如果两个box合并后更优（即合并后box左右的左右边界在全文中出现的次数更多[参考页眉部分]），则合并两个box
                    if line_box.mergeable(tmp[-1],x):
                        tmp[-1].merge(x)
                        continue
            tmp.append(x)
        return tmp


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
            page=self.merge_box(page)
            page.sort(key=cmp_to_key(sort_box))
            
            for box in page:
                box.merge_lines()
                for line in box:
                    lines.append(line)
                    if line.get_text().strip().lower().find("references")==0:
                        lines=[]
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
