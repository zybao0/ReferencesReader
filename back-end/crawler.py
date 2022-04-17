import requests
from urllib.parse import parse_qs,urlparse
from bs4 import BeautifulSoup
import re
def get_bib_from_baiduxueshu(reference):
    headers={
        "user-agent":"Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    }
    url="https://xueshu.baidu.com/s?"
    data={
        "wd":reference,
        "ie":"utf-8",
        "tn":"SE_baiduxueshu_c1gjeupa",
        "sc_from":"",
        "sc_as_para":"sc_lib:",
        "rsv_sug2":"0",
    }
    respond=requests.get(url=url,params=data,headers=headers)

    soup=BeautifulSoup(respond.text,"lxml")
    result=soup.find("div",attrs={"class":"result sc_default_result xpath-log","id":"1"})
    paperid_url=result.find("a",href=re.compile("paperid"))["href"]
    query=urlparse(paperid_url).query
    params=parse_qs(query)

    url="https://xueshu.baidu.com/u/citation?"
    data={
        "type":"bib",
        "paperid":params["paperid"][0],
    }
    respond=requests.get(url=url,params=data,headers=headers)
    return respond.text