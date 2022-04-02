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
import string
import math

class my_box:
    def __init__(self,x0,x1,y0,y1):
        self.set_size(x0,x1,y0,y1)

    def merge(self,obj):
        self.x0=min(self.x0,obj.x0)
        self.x1=max(self.x1,obj.x1)
        self.y0=min(self.y0,obj.y0)
        self.y1=max(self.y1,obj.y1)
    
    def set_size(self,x0,x1,y0,y1):
        self.x0,self.x1,self.y0,self.y1=x0,x1,y0,y1
        
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

    @classmethod
    def _join(cls,obj1,obj2):
        return obj1.get_text().rstrip()+" "+obj2.get_text().rstrip()

    def merge(self,obj):#直接将第二个文本添加在第一个文本后
        self.text=text_box._join(self,obj)
        my_box.merge(self,obj)

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

    def merge_lines(self):#pdfminer 有时会把空格当作换行，在这里修正,把一个box内的相同高度的行合并
        self.sort()
        tmp=[]
        merged_lines=[]
        for i,x in enumerate(self._lines):
            tmp.append(x)
            if i==len(self._lines)-1 or not text_box.mergeable(tmp[0],self._lines[i+1]):
                tmp.sort(key=lambda x:x.x0)
                for i in range(1,len(tmp)):
                    tmp[0].merge(tmp[i])
                merged_lines.append(tmp[0])
                tmp=[]
        self._lines=merged_lines

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
    _x_dict=defaultdict(float)#key:box的左右边界,value:box面积
    _most_common_bound=[]#全文中最有可能出现的左右边界对  
    tol_size=0    #box总面积
    min_y=0xEAB0  #y值下界
    max_y=-0xEAB0 #y值上界

    _references_list=[]#最终获得的references的列表

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
            self._get_body()
            self._find_references()
            self._split_references()


    def __len__(self):
        return len(self._references_list)
    def __iter__(self):
        return iter(self._references_list)
    def __getitem__(self,index):
        return self._references_list[index]
    def __repr__(self):
        return "\n".join(["["+str(i)+"]: "+x for i,x in enumerate(self._references_list)])


    def _get_body(self):#获取文章主体部分边界值（获得页眉和页脚的边界值）
        for page in self._pdf_pages:
            for bx in page:
                size=(bx.x1-bx.x0)*(bx.y1-bx.y0)
                self.tol_size+=size
                self._x_dict[(int(bx.x0),int(bx.x1))]+=size

        self._most_common_bound=sorted(self._x_dict.items(),key=lambda x:x[1],reverse=True)
        
        now_size=0
        for i,x in enumerate(self._most_common_bound):#获得占比最高的若干个边界值，使得以这些边界值为左右边界的box占到全文的绝大部分
            now_size+=x[1]
            threshold_size=x[1]
            if now_size*2>self.tol_size and (i==len(self._most_common_bound)-1 or x[1]>self._most_common_bound[i+1][1]):
                self._most_common_bound=self._most_common_bound[0:i+1]
                break

        for page in self._pdf_pages:
            for bx in page:
                if self._x_dict[(int(bx.x0),int(bx.x1))]>=threshold_size:
                    self.min_y=min(self.min_y,bx.y0)
                    self.max_y=max(self.max_y,bx.y1)
        
        if self.min_y==0xEAB0:#如果仍未初始值，认为出现异常，将min_y置为负无穷，max_y置为正无穷防止影响之后的操作
            self.min_y=-0xEAB0
        if self.max_y==-0xEAB0:
            self.max_y=0xEAB0 


    def _find_references(self):
        for page in self._pdf_pages:
            tmp=[line_box.cast(bx) for bx in page if bx.y1>=self.min_y and bx.y0<=self.max_y]
            for bx in page:
                if bx.get_text().strip().lower().find("references")==0:
                    self._references_page=[]
                    break
            self._references_page.append(tmp)


    def _merge_box(self,page):
        page.sort(key=lambda x:x.y0)
        tmp=[]
        for x in page:
            flag=False
            for y in tmp:
                if my_box.y_nest(y,x):
                    t1=self._x_dict[(int(x.x0),int(x.x1))]
                    t2=self._x_dict[(int(y.x0),int(y.x1))]
                    t3=self._x_dict[(int(min(x.x0,y.x0)),int(max(x.x1,y.x1)))]
                    if max(t1,t2)<t3 and line_box.mergeable(y,x):#如果两个box合并后更优（即合并后box左右的左右边界在全文中出现的次数更多[参考页眉部分]），则尝试合并两个box
                        y.merge(x)
                        flag=True
                        break
            if flag==False:
                tmp.append(x)
        return tmp


    def _split_references(self):
        line_list=[]
        
        def sort_box(x,y):
            if(x.x1<y.x0):
                return -1
            elif (x.x0>y.x1):
                return 1
            else:
                return y.y1-x.y1#右下角是原点，右向是x轴，向上是y轴

        for i,page in enumerate(self._references_page):
            column=0
            page=self._merge_box(page)

            for box in page:#使用拓展盒子边界机制，将不是常见的box左右边界拓展为常见的box左右边界（即本来宽度不到一整行的box变为一整行），防止孤立的box对接下来的排序造成影响（产考论文[ACM 2008] Real-Time, All-Frequency Shadows in Dynamic Scenes，references上方的公式对排序的影响）
                for bound in self._most_common_bound:
                    if bound[0][0]-3<box.x0 and bound[0][1]+3>box.x1:
                        box.set_size(bound[0][0],bound[0][1],box.y0,box.y1)
                        break

            page.sort(key=cmp_to_key(sort_box))#将box按照阅读顺序排序
            
            for j,box in enumerate(page):
                box.merge_lines()
                if j>0 and page[j-1].x1<box.x0:#如果两个box发生了错位，认为另起了一列
                    column+=1
                for line in box:
                    line_list.append((line,(i,column)))
                    if line.get_text().strip().lower().find("references")==0:
                        line_list=[]
        
        def period_prize(s):
            tmp=s.rstrip()
            if len(tmp)==0 or tmp[-1]!='.':
                return -1#如果不是以'.'给予惩罚
            cnt=0
            for x in range(2,min(len(tmp),4)):#'.'前面的非空字符越多，奖励越多（防止人名中的无效'.'）
                if tmp[-x] in string.whitespace:
                    break
                cnt+=1
            return max(cnt-1,0)
        
        def cal_s2(sum_x,sum_x2,n):
            if n==0:
                return 0
            tmp=sum_x/n
            s2=sum_x2/n-tmp*tmp
            return s2 if abs(s2)>1e-9 else 0

        def cal_min_s2(l):#将有序列表一分为二使得两部分的方差和最小
            sum_x,sum_x2=0,0
            sum_y,sum_y2=sum(l),sum([x*x for x in l])
            split_pos=0#方差和最小时对应的切割位置(x:l[0:split_pos],y:l[split_pos:])
            min_sum_x,min_sum_y=0,sum_y2#方差和最小时两部分的和
            min_x_s2,min_y_s2=0,cal_s2(sum_y,sum_y2,len(l))#方差和最小时两部分的方差
            for j,x in enumerate(l):#将l[j]加入左边后计算方差和
                tmp=l[j]*l[j]
                sum_x+=l[j]
                sum_x2+=tmp
                sum_y-=l[j]
                sum_y2-=tmp
                x_s2=cal_s2(sum_x,sum_x2,j+1)
                y_s2=cal_s2(sum_y,sum_y2,len(l)-j-1)
                if x_s2+y_s2<min_x_s2+min_y_s2:
                    min_sum_x,min_x_s2,min_sum_y,min_y_s2,split_pos=sum_x,x_s2,sum_y,y_s2,j+1
            return split_pos,min_sum_x/split_pos if split_pos>0 else 0,math.sqrt(min_x_s2),min_sum_y/(len(l)-split_pos) if len(l)-split_pos>0 else 0,math.sqrt(min_y_s2)#返回分割位置，x部分的平均数，x部分的标准差，y部分的平均数，y部分的表准差

        sum_line_space,sum_line_space2,num_line_space=0,0,0#统计所有的行间距，用于判断references是否达到结尾
        tmp=[]
        references_end=False
        for i,line in enumerate(line_list):
            tmp.append(line)
            if i==0 or line_list[i-1][1]!=line[1]:#如果另起了一列，则统计该列文本的行间隔
                line_space=[]
                for j in range(i+1,len(line_list)):
                    if line_list[j][1]!=line_list[j-1][1]:
                        break
                    line_space.append(line_list[j-1][0].y0-line_list[j][0].y1)
                if len(line_space)<6:#样本太小，不具有统计学意义
                    line_space_prize=False#不对行间隔的差异给予奖励
                else:
                    line_space=sorted(line_space)[1:len(line_space)-1]#剔除最大和最小的两个数
                    split_pos,avg_x,sig_x,avg_y,sig_y=cal_min_s2(line_space)#将列表一分为二，x表示同一个reference之间两行的间隔，y表示两个reference之间的间隔（估计）
                    line_space_prize=False if split_pos<=1 or split_pos>=len(line_space)-1 or avg_y-avg_x<3*max(sig_x,sig_y) else True
    
            value=0
            if(i!=len(line_list)-1):#如果是全文最后一行就没有讨论的必要了
                if i!=0 and line_list[i-1][1]==line[1]:#如果本行和上一行在同一页同一列
                    value+=3 if line_list[i-1][0].x1>line[0].x1 and int(len(line_list[i-1][0].get_text())*(line_list[i-1][0].x1-line[0].x1)/(line_list[i-1][0].x1-line_list[i-1][0].x0))>2 else 0#如果本行的右端在上面那行的右端的左边，给予奖励
                if line_list[i+1][1]==line[1]:#如果本行和下一行在同一页同一列
                    if line_space_prize==True:
                        #如果它跟下一行的间隔更加接近avg_y（两个reference之间的间隔），则给予奖励，否则给予惩罚，本来为abs(line[0].y0-line_list[i+1][0].y1-avg_x)/sig_x>abs(line[0].y0-line_list[i+1][0].y1-avg_y)/sig_y通过移项防止除以零
                        value+=5 if abs(line[0].y0-line_list[i+1][0].y1-avg_x)*sig_y>abs(line[0].y0-line_list[i+1][0].y1-avg_y)*sig_x else -5
                    value+= 3 if line_list[i+1][0].x1>line[0].x1 and int(len(line_list[i+1][0].get_text())*(line_list[i+1][0].x1-line[0].x1)/(line_list[i+1][0].x1-line_list[i+1][0].x0))>2 else 0#如果本行的右端在下面那行的右端的左边，给予奖励
                    value-=10 if line_list[i+1][1]==tmp[0][1] and int(len(tmp[0][0].get_text())*(line_list[i+1][0].x0-tmp[0][0].x0)/(tmp[0][0].x1-tmp[0][0].x0))>0 else 0#如果下一行与本reference的第一行在同一列(即没有发生错位)，且如果下一行的左端与上一条reference的左端不同，给予惩罚
                    if num_line_space>=6:
                        avg_line_space=sum_line_space/num_line_space
                        sig_line_space=math.sqrt(cal_s2(sum_line_space,sum_line_space2,num_line_space))
                        if line[0].y0-line_list[i+1][0].y1>2*(avg_line_space+3*sig_line_space):#如果下一部分过长，认为reference结束，论文进入下一个部分
                            references_end=True
                    sum_line_space+=line[0].y0-line_list[i+1][0].y1
                    sum_line_space2+=(line[0].y0-line_list[i+1][0].y1)**2
                    num_line_space+=1
                elif num_line_space>=6 and line[0].y0-self.min_y>5*(avg_line_space+3*sig_line_space):
                    references_end=True

                value+=period_prize(line[0].get_text())
                if value<=0 and references_end==False:
                    continue
            for i in range(1,len(tmp)):
                tmp[0][0].merge(tmp[i][0])
            self._references_list.append(tmp[0][0].get_text())
            tmp=[]
            if references_end==True:
                break