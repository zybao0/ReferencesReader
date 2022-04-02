import math
import string

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