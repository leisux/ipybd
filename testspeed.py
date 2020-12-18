#from ipybd import NoiOccurrence
#
#test = NoiOccurrence(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/DataCleaningTest.xlsx")
#
#test.write_json()

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