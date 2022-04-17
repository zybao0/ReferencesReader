# transform the box from pdfminer
# so that I can secondary process the result

class box_base:
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
    def y_nest(cls,obj1,obj2):
        return (obj1.y0+0.001>=obj2.y0 and obj1.y1-0.001<=obj2.y1) or (obj1.y0-0.001<=obj2.y0 and obj1.y1+0.001>=obj2.y1)

    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1)


class text_box(box_base):
    text=""
    def __init__(self,x0,x1,y0,y1,text):
        box_base.__init__(self,x0,x1,y0,y1)
        self.text=text.strip()

    @classmethod
    def mergeable(cls,obj1,obj2):
        return box_base.y_nest(obj1,obj2)

    @classmethod
    def _join(cls,obj1,obj2):
        return obj1.get_text().strip()+" "+obj2.get_text().strip()

    def merge(self,obj):
        self.text=text_box._join(self,obj)
        box_base.merge(self,obj)

    def get_text(self):
        return self.text

    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj.get_text())


class line_box(box_base):
    _lines=[]
    def __init__(self,x0,x1,y0,y1,lst):
        self._lines=[text_box.cast(x) for x in lst]
        box_base.__init__(self,x0,x1,y0,y1)

    def __len__(self):
        return len(self._lines)
    def __iter__(self):
        return iter(self._lines)
    def __getitem__(self,index):
        return self._lines[index]

    #if box A is nested by box B in y axis
    #and each line in box A and box B is aligned
    #then we think that box A and box B can be merged in to a larger line box 
    @classmethod
    def mergeable(cls,obj1,obj2):
        if len(obj1)>len(obj2):
            obj1,obj2=obj2,obj1
        if len(obj1)==0:
            return True
        if not box_base.y_nest(obj1,obj2):
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

    def merge(self,obj):
        self._lines+=[x for x in obj]
        box_base.merge(self,obj)

    def sort(self):
        self._lines.sort(key=lambda x:x.y1,reverse=True)

    #sometimes two lines in a line box is actually one line in the pdf
    #(this is cause by the faulty analysis of pdfminer or after we merge to line boxes)
    #so we have to amend it by merging lines which have same y coordinate into one line
    def merge_lines(self):
        self.sort()
        tmp=[]
        merged_lines=[]
        for i,x in enumerate(self._lines):
            tmp.append(x)
            if i==len(self._lines)-1 or not text_box.mergeable(tmp[0],self._lines[i+1]):#if the next line in the box is not mergeable with current line we should merge all the line in tmp and empty tmp
                tmp.sort(key=lambda x:x.x0)#the text with smaller x coordinate should be put in the front of a line
                for i in range(1,len(tmp)):
                    tmp[0].merge(tmp[i])
                merged_lines.append(tmp[0])
                tmp=[]
        self._lines=merged_lines

    @classmethod
    def cast(cls,obj):
        return cls(obj.x0,obj.x1,obj.y0,obj.y1,obj)