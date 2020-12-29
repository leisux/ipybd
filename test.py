# NoiOccurrence Test
from ipybd import NoiOccurrence

noi = NoiOccurrence(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/DataCleaningTest.xlsx")
noi.write_json()


# Model Test
from enum import Enum 
from ipybd import imodel

@imodel 
class MyCollection(Enum): 
    记录人 = '>采集人' 
    记录编号 = '>采集号' 
    记录时间 = '>采集日期' 
    _省_市 = {'>省市':','} 
    学名 = ('>属', '>种', '>种下等级', ' ') 

cvh = MyCollection(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx") 



# Label Test
from ipybd import Label

printer = Label(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx", repeat=2)
printer.write_html(start_code="KUN004123", page_num=8)
