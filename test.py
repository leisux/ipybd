# NoiOccurrence Test
from enum import Enum
from ipybd import HumanName
from ipybd import Label
from ipybd import imodel
from ipybd import NoiOccurrence

noi = NoiOccurrence(
    r"/Users/xuzhoufeng/OneDrive/PDP/testfile/DataCleaningTest.xlsx")
noi.write_json()


# Model Test


@imodel
class MyCollection(Enum):
    记录人 = '$采集人'
    记录编号 = '$采集号'
    记录时间 = '$采集日期'
    省_市 = {'$省市': ','}
    学名 = ('$属', '$种', '$种下等级', ' ')


cvh = MyCollection(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx")


# Label Test

printer = Label(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx", repeat=2)
printer.write_html(start_code="KUN004123", page_num=8)


# HumanName Test

names = HumanName([
    "Capt. Francis (Frank) Kingdon-Ward", 
    "(Johann) Albert von Regel", 
    "T.N. Ho, B.M. Bartholomew, M.G. Gilbert & S.W. Liu", 
    "A Herb. Monteiro de Carvalho", "[Cavalerie] J.", 
    "[en chinois]", "[Delavay]", "Alleizette C. d'", 
    "Alleizette C. d', Maire leg.",
    "Annenkov N. I.", 
    "Handel-Mazzetti H. von", 
    "Hong De-Y", "Higuchi M.", 
    "Hort. Bot. Vilmorin", "Wan F.-H.", 
    "Soulié J.A.", "To, Ts'ang", 
    "Bons d'Anty", "Bonvalot P.G.E., d'Orléans H.", 
    "Incarville   P.N.   C. d'", 
    "Kang P., Tak Ts'ang, Kin Ts'ang"])
    
names()
