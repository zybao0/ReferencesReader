# -*- coding: utf-8 -*-
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

class my_box:
    def __init__(self,x0,x1,y0,y1):
        self.x0,self.x1,self.y0,self.y1=x0,x1,y0,y1
    def merge(self,obj):
        self.x0=min(self.x0,obj.x0)
        self.x1=max(self.x1,obj.x1)
        self.y0=min(self.y0,obj.y0)
        self.y1=max(self.y1,obj.y1)
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1)

class text_box(my_box):
    text=""
    def __init__(self,x0,x1,y0,y1,text):
        my_box.__init__(self,x0,x1,y0,y1)
        self.text=text.rstrip()
    def merge(self,obj):
        my_box.merge(self,obj)
        self.text=self.text.rstrip()+" "+obj.text.rstrip()
    def get_text(self):
        return self.text
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj.get_text())
    


os.chdir(r'./PDF_data')
fp = open('[10] [HPG 2017] Improved Two-Level BVHs using Partial Re-Braiding.pdf', 'rb')

#来创建一个pdf文档分析器
parser = PDFParser(fp)
#创建一个PDF文档对象存储文档结构
document = PDFDocument(parser)

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
    # device=PDFDevice(rsrcmgr)
    device=PDFPageAggregator(rsrcmgr,laparams=laparams)
    # 创建一个PDF解释器对象
    interpreter=PDFPageInterpreter(rsrcmgr,device)
    # 处理每一页
    pdf_pages=[]#储存所有页面的box
    page_list=[]#储存references以后的页面

    #由于论文的特点，正文部分的box再竖直方向[x轴坐标]（几乎）是对齐的，
    #使用字典统计左边界为x0，右边界为x1的box的总面积有多大，
    #若该面积占所有box总面积的大部分，则认为左边界为x0，右边界为x1的box为正文box
    #取所有正文box的y值上界和y值下界得到正文部分的上界和下界
    #若y值超过上界或下界的box认为属于页眉或页脚内容
    x_dict={}     #key:box的左右边界,value:box面积
    tol_size=0    #box总面积
    min_y=0xEAB0  #y值下界
    max_y=-0xEAB0 #y值上界
    for page in document.get_pages():
        interpreter.process_page(page)
        # 接受该页面的LTPage对象
        LTlayout=device.get_result()

        bx_list=[x for x in LTlayout if isinstance(x, LTTextBoxHorizontal) and len(x)>0]#获得所有文本box
        if len(bx_list)==0:
            continue

        for bx in bx_list:
            size=(bx.x1-bx.x0)*(bx.y1-bx.y0)
            tol_size+=size
            if (int(bx.x0),int(bx.x1)) in x_dict:
                x_dict[(int(bx.x0),int(bx.x1))]+=size
            else:
                x_dict[(int(bx.x0),int(bx.x1))]=size

            if bx.get_text().lower().find("references")==0:
                page_list=[]

        page_list.append(bx_list)
        pdf_pages.append(bx_list)
    
    # print(page_list)

    rk=sorted([x/tol_size for x in x_dict.values()],reverse=True)
    now_size=0
    for x in rk:
        now_size+=x
        threshold_size=x
        if now_size>0.5:
            break


    for page in pdf_pages:
        for bx in page:
            if x_dict[(int(bx.x0),int(bx.x1))]/tol_size>threshold_size:
                min_y=min(min_y,bx.y0)
                max_y=max(max_y,bx.y1)
    print(min_y,max_y)

    lines=[]
    def sort_box(x,y):
        if(x.x1<y.x0):
            return -1
        elif (x.x0>y.x1):
            return 1
        else:
            return y.y0-x.y0#右下角是原点，右向是x轴，向上是y轴
    for page in page_list:
        first_line_in_page=True
        page.sort(key=cmp_to_key(sort_box))
        for box in page:
            #print(box)
            if box.y0<min_y or box.y1>max_y:
                continue
            for line in box:
                tmp=text_box.cast(line)
                if len(lines)==0:
                    lines.append(tmp)
                else:
                    if lines[-1].y0-0.001<=line.y0 and lines[-1].y1+0.001>=line.y1:#pdfminer 有时会把空格当作换行，在这里修正
                        lines[-1].merge(tmp)
                        
                    else:
                        # if not (first_line_in_page!=True and "".join(tmp.get_text().split()).isdigit() and lines[-1].y1-tmp.y0>2*(tmp.y1-tmp.y0)):#这种情况很可能是页数，这样的话就跳过这以后
                            lines.append(tmp)
                if line.get_text().lower().find("references")==0:
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