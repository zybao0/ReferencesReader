# -*- coding: utf-8 -*-
from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal,LAParams,LTLine
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
import os
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
    for page in document.get_pages():
        interpreter.process_page(page)
        # 接受该页面的LTPage对象
        layout=device.get_result()
        for x in layout:
            if isinstance(x, LTTextBoxHorizontal):
                # print(x.get_text())
                for y in x:
                    print(type(y.get_text()))
                    print(y.get_text())
        break