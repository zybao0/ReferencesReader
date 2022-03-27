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

class my_line:
    text=""
    def __init__(self,x0,x1,y0,y1,text):
        self.text=text
        self.x0,self.x1,self.y0,self.y1=x0,x1,y0,y1
    def merge(self,obj):
        self.x0=min(self.x0,obj.x0)
        self.x1=max(self.x1,obj.x1)
        self.y0=min(self.y0,obj.y0)
        self.y1=max(self.y1,obj.y1)
        self.text=self.text.rstrip('\n')+" "+obj.text
    def get_text(self):
        return self.text
    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj.get_text())



os.chdir(r'./PDF_data')
fp = open('Liu_Invertible_Denoising_Network_A_Light_Solution_for_Real_Noise_Removal_CVPR_2021_paper.pdf', 'rb')

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
    page_list=[]#储存references以后的页面
    for i,page in enumerate(document.get_pages()):
        interpreter.process_page(page)
        # 接受该页面的LTPage对象
        LTlayout=device.get_result()

        tmp=[x for x in LTlayout if isinstance(x, LTTextBoxHorizontal) and len(x)>0]
        for x in tmp:
            if x.get_text().lower().find("references")!=-1:
                page_list=[]
                break
        page_list.append(tmp)
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
            for line in box:
                tmp=my_line.cast(line)
                if len(lines)==0:
                    lines.append(tmp)
                else:
                    if lines[-1].y0-0.001<=line.y0 and lines[-1].y1+0.001>=line.y1:#pdfminer 有时会把空格当作换行，在这里修正
                        lines[-1].merge(tmp)
                    else:
                        # if not (first_line_in_page!=True and "".join(tmp.get_text().split()).isdigit() and lines[-1].y1-tmp.y0>2*(tmp.y1-tmp.y0)):#这种情况很可能是页数，这样的话就跳过这以后
                            lines.append(tmp)
                if line.get_text().lower().find("references")!=-1:
                    lines=[]
                first_line_in_page=False
    for line in lines:
        print(line.get_text())
        