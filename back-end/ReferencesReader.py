from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal,LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
import pdfminer.layout as layout

from ReferencesReader_box import *
from ReferencesReader_tools import *

import os
import re
from functools import cmp_to_key
import bisect
from collections import defaultdict



class ReferencesReader:
    def __init__(self,PDF_file):
        self._pdf_pages=[]#store all boxes in a page 
        self._references_page=[]#store boxes which contain references

        #due to the characteristics of the paper, the box in the text part is (almost) aligned in the vertical direction [x-axis coordinate],
        #we use a dictionary to calculate the total area of boxes which the coordinate of left border is x0 and the coordinate of right border is x1,
        #if the area accounts for most of the total area of all boxes, the box with the left border of x0 and the right border of x1 is considered to be the main body in the paper
        #take the upper and lower bounds of the y value of all main body boxes to get the upper and lower bounds of the main body
        #if the y value exceeds the upper or lower bound, the box is considered to belong to the header or footer content
        self._x_dict=defaultdict(float)#key:a tuple with value (left border,right border) of a box,value:the summation size of boxes with same (left border,right border)
        self._most_common_bound=[]#the most likely left and right boundary pairs in the full text
        self.tol_size=0    #total size of all box in paper
        self.min_y=0xEAB0  #lower bounds of main body
        self.max_y=-0xEAB0 #upper bounds of main body

        self._references_list=[]#the final list of references

        
        self._extract_text(PDF_file)
        self._get_body()
        self._find_references()
        self._merge_references()
        self._beautify_references()


    def __len__(self):
        return len(self._references_list)
    def __iter__(self):
        return iter(self._references_list)
    def __getitem__(self,index):
        return self._references_list[index]
    def __repr__(self):
        return "\n".join(["["+str(i)+"]: "+x for i,x in enumerate(self._references_list)])

    def _extract_text(self,PDF_file):
        #initialize pdfminer
        parser=PDFParser(PDF_file)
        document=PDFDocument(parser)
        parser.set_document(document)
        document.set_parser(parser)
        document.initialize()

        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            #extract content in pdf
            rsrcmgr=PDFResourceManager()
            laparams=LAParams()
            device=PDFPageAggregator(rsrcmgr,laparams=laparams)
            interpreter=PDFPageInterpreter(rsrcmgr,device)
            
            for page in document.get_pages():
                interpreter.process_page(page)
                LTlayout=device.get_result()

                box_list=[x for x in LTlayout if isinstance(x,LTTextBoxHorizontal) and len(x)>0]
                if len(box_list)==0:
                    continue
                self._pdf_pages.append(box_list)


    #Get the boundary value of the main part of the article (get the boundary value of the header and footer)
    def _get_body(self):
        for page in self._pdf_pages:
            for bx in page:
                size=(bx.x1-bx.x0)*(bx.y1-bx.y0)
                self.tol_size+=size
                self._x_dict[(int(bx.x0),int(bx.x1))]+=size

        self._most_common_bound=sorted(self._x_dict.items(),key=lambda x:x[1],reverse=True)
        
        now_size=0
        for i,x in enumerate(self._most_common_bound):#Obtain several boundary values with the highest proportion, so that the boxes with these boundary values on the left and right boundaries account for most
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
        
        #if min_y or max_y is still inf or -inf there may be something wrong or the paper is too strange to use this way to get the main body 
        #so we consider that the whole page is main body and there is no header or footer content
        #this may be wrong but we have no other way
        if self.min_y==0xEAB0:
            self.min_y=-0xEAB0
        if self.max_y==-0xEAB0:
            self.max_y=0xEAB0 


    #we find the last "references" in the paper and consider the following lines is the references of the paper
    def _find_references(self):
        for page in self._pdf_pages:
            tmp=[line_box.cast(bx) for bx in page if bx.y1>=self.min_y and bx.y0<=self.max_y]
            for bx in page:
                if bx.get_text().strip().lower().find("references")==0:
                    self._references_page=[]
                    break
            self._references_page.append(tmp)


    #because of the faulty analysis of pdfminer 
    #sometimes a paragraph will be aplit into two boxes in x axis 
    #If it is better after the two boxes are combined 
    #(the left and right borders of the combined box appear more often in the full text [refer to the header section])
    #try to combine the two boxes
    def _merge_box(self,page):
        page.sort(key=lambda x:x.y0)
        tmp=[]
        for x in page:
            flag=False
            for y in tmp:
                if box_base.y_nest(y,x):
                    t1=self._x_dict[(int(x.x0),int(x.x1))]
                    t2=self._x_dict[(int(y.x0),int(y.x1))]
                    t3=self._x_dict[(int(min(x.x0,y.x0)),int(max(x.x1,y.x1)))]
                    if max(t1,t2)<t3 and line_box.mergeable(y,x):
                        y.merge(x)
                        flag=True
                        break
            if flag==False:
                tmp.append(x)
        return tmp
        

    #Use the extension box boundary mechanism to expand the left and right borders of the uncommon box to the common left and right borders of the box
    #(the box whose width is less than a whole line becomes a whole line) to prevent the isolated box from affecting the next sorting
    #( Production test paper [ACM 2008] Real-Time, All-Frequency Shadows in Dynamic Scenes, the impact of the formula above the references on sorting)
    def _extend_box(self,page):#extend a box in a page to the most common x-axis boundary
        for box in page:
                for bound in self._most_common_bound:
                    if bound[0][0]-3<box.x0 and bound[0][1]+3>box.x1:
                        box.set_size(bound[0][0],bound[0][1],box.y0,box.y1)
                        break

    def _split_references(self):#split boxes into lines_list
        line_list=[]

        for i,page in enumerate(self._references_page):
            column=0
            page=self._merge_box(page)
            self._extend_box(page)
            page.sort(key=cmp_to_key(lambda x,y:-1 if x.x1<y.x0 else 1 if x.x0>y.x1 else y.y1-x.y1))#Sort boxes in reading order
            
            for j,box in enumerate(page):
                box.merge_lines()
                if len(box)==1 and len(box[0].get_text())<5 and (box.x0,box.x1)not in self._most_common_bound:
                    continue
                if j>0 and page[j-1].x1<box.x0:#If the two boxes are misaligned, consider another column
                    column+=1
                for line in box:
                    line_list.append((line,(i,column)))
                    if line.get_text().strip().lower().find("references")==0:
                        line_list=[]
        return line_list

    def _merge_references(self):
        line_list=self._split_references()
        
        sum_line_space,sum_line_space2,num_line_space=0,0,0#Count all line spacing to determine whether references have reached the end
        tmp=[]
        references_end=False
        for i,line in enumerate(line_list):
            tmp.append(line)
            if i==0 or line_list[i-1][1]!=line[1]:#If another column is created, count the line spacing of the text in this column
                line_space=[]
                for j in range(i+1,len(line_list)):
                    if line_list[j][1]!=line_list[j-1][1]:
                        break
                    line_space.append(line_list[j-1][0].y0-line_list[j][0].y1)
                if len(line_space)<6:#The sample is too small to be statistically significant
                    line_space_prize=False
                else:
                    line_space=sorted(line_space)[1:len(line_space)-1]#Remove the largest and smallest numbers
                    split_pos,avg_x,sig_x,avg_y,sig_y=cal_min_s2(line_space)#Divide the list into two, x represents the interval between two lines of the same reference, y represents the interval (estimation) between two references
                    line_space_prize=False if split_pos<=1 or split_pos>=len(line_space)-1 or avg_y-avg_x<3*max(sig_x,sig_y) else True
    
            value=0
            if(i!=len(line_list)-1):
                if i!=0 and line_list[i-1][1]==line[1]:#If this row and the previous row are on the same page and the same column
                    value+=3 if line_list[i-1][0].x1>line[0].x1 and int(len(line_list[i-1][0].get_text())*(line_list[i-1][0].x1-line[0].x1)/(line_list[i-1][0].x1-line_list[i-1][0].x0))>2 else 0#If the right end of the row is to the left of the right end of the row above, give a bonus
                if line_list[i+1][1]==line[1]:#If this row and the next row are on the same page and the same column
                    if line_space_prize==True:
                        #If the interval between this line and the next line is closer to avg_y (the interval between two references), a reward is given, otherwise a penalty is given, which is originally abs(line[0].y0-line_list[i+1][0].y1 -avg_x)/sig_x>abs(line[0].y0-line_list[i+1][0].y1-avg_y)/sig_y shift toprevent division by zero
                        value+=5 if abs(line[0].y0-line_list[i+1][0].y1-avg_x)*sig_y>abs(line[0].y0-line_list[i+1][0].y1-avg_y)*sig_x else -5
                    value+= 3 if line_list[i+1][0].x1>line[0].x1 and int(len(line_list[i+1][0].get_text())*(line_list[i+1][0].x1-line[0].x1)/(line_list[i+1][0].x1-line_list[i+1][0].x0))>2 else 0#If the right end of this row is to the left of the right end of the row below, give a bonus
                    value-=10 if line_list[i+1][1]==tmp[0][1] and int(len(tmp[0][0].get_text())*(line_list[i+1][0].x0-tmp[0][0].x0)/(tmp[0][0].x1-tmp[0][0].x0))>0 else 0#If the next row is in the same column as the first row of this reference (that is, there is no misalignment), and if the left end of the next row is different from the left end of the previous reference, a penalty will be imposed
                    if len(self._references_list)>=6:
                        avg_line_space=sum_line_space/num_line_space
                        sig_line_space=math.sqrt(cal_s2(sum_line_space,sum_line_space2,num_line_space))
                        if sig_line_space>1e-6 and line[0].y0-line_list[i+1][0].y1>2*(abs(avg_line_space)+3*sig_line_space):#If the next part is too long, the reference is considered to be over, and the paper goes to the next part
                            references_end=True
                    sum_line_space+=line[0].y0-line_list[i+1][0].y1
                    sum_line_space2+=(line[0].y0-line_list[i+1][0].y1)**2
                    num_line_space+=1
                elif len(self._references_list)>=6 and sig_line_space>1e-6 and  line[0].y0-self.min_y>5*(abs(avg_line_space)+3*sig_line_space):
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
    def _beautify_references(self):
        #use regular expression to remove Index of reference
        #use set to distinct references
        self._references_list=list(set([re.match(r"((\[.*?\])|([0-9]*\s*\.))?(.*)",x).group(4).strip() for x in self._references_list]))