# NoiOccurrence Test
from ipybd import NoiOccurrence

noi = NoiOccurrence(
    r"/Users/xuzhoufeng/OneDrive/PDP/testfile/DataCleaningTest.xlsx")
noi.write_json()


# Model Test
from ipybd import imodel
from enum import Enum

@imodel
class MyCollection(Enum):
    记录人 = '$采集人'
    记录编号 = '$采集号'
    记录时间 = '$采集日期'
    省_市 = {'$省市': ','}
    学名 = ('$属', '$种', '$种下等级', ' ')


cvh = MyCollection(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx")


# Label Test
from ipybd import Label

printer = Label(r"/Users/xuzhoufeng/OneDrive/PDP/testfile/cvh.xlsx", repeat=2)
printer.write_html(start_code="KUN004123", page_num=8)


# HumanName Test
from ipybd import HumanName

names = HumanName([
    "Henry, A.",
    "David, D. M., Henry, A., Delavayi F. K., Bob, C. F.",
    "Chow, --",
    "Chow, -- & Tsang",
    "-- Tsang, -- Tang & Fung, --",
    "-- Dorsett & -- Dorsett",
    "-- Tsang, -. Tang & Fung, --",
    "To Kang P'eng, W. T. Tsang & Ts' Ang Un Kin",
    "Rev. Mr. Rankin",
    "-- Keng & -. Kao",
    "U. K. Tsang, -- Tang & Fung, --",
    "Teilhard de Chardin (Abbé) Pierre, Teilhard de Chardin (Abbé) Pierre",
    "David (Abbé)",
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


# BioName format_latin_names

from ipybd import BioName

latiname = [
 'Saxifraga umbellulata Hook. f. et Thoms. var. pectinata (C. Marq. et Airy Shaw) J. T. Pan',
 'Anemone demissa Hook. f. et Thoms. var. yunnanensis Franch.',
 'Schisandra grandiflora (Wall.) Hook. f. et Thoms.',
 'Phaeonychium parryoides (Kurz ex Hook. f. et T. Anderson) O. E. Schulz',
 'Crucihimalaya lasiocarpa (Hook. f. et Thoms.) Al-Shehbaz et al.',
 'Saxifraga rufescens bal f. f.',
 'Saxifraga rufescens Bal f. f. var. uninervata J. T. Pan',
 'Lindera pulcherrima (Nees) Hook. f. var. attenuata C. K. Allen',
 'Polygonum glaciale (Meisn.) Hook. f. var. przewalskii (A. K. Skvortsov et Borodina) A. J. Li',
 'Psilotrichum ferrugineum (Roxb.) Moq. var. ximengense Y. Y. Qian',
 'Houpoëa officinalis (Rehd. et E. H. Wils.) N. H. Xia et C. Y. Wu',
 'Rhododendron delavayi Franch.',
 'Rhodododendron',
 'Fabaceae',
 'Lindera sinisis var. nssi Franch.',
 'Poa annua subsp. sine',
 'Poa annua',
 'Poa annua annua',
 'Poa annua annua (Kurz ex Hook. f. et T. Anderson) O. E. Schulz',
 'Saxifraga rufescens Bal. var.uninervata J. T. Pan',
 'Saxifraga rufescens Bal f. f. var.uninervata J. T. Pan',
 'Rhododendron delavayi Franch.'
 ]

test = BioName(latiname, style='fullPlantSplitName')
test()



from ipybd import CVH

table = CVH(r"C:\Users\xu_zh\OneDrive\PDP\iherbarium\标签推荐模版ss.xlsx")



from ipybd import AdminDiv
import pandas as pd

admindiv = [
    "内蒙古阿左旗贺兰山南寺沟",
    "内蒙古",
    "辽宁省，朝阳市，努鲁儿虎山自然保护区",
    "中国浙江省，临安市，浙江农林大学新校区",
    "中国浙江省，临安市",
    "中国浙江省，临安市，天目山景区",
    "西藏日喀则地区",
    "中国,西藏,林芝市，巴宜区",
    "西藏林芝县",
    "西藏林芝",
    "西藏林芝米林"
]

test = AdminDiv(admindiv)
test.format_chinese_admindiv()
table = pd.DataFrame({
    "raw":admindiv,
    "country":test.country,
    "province":test.province,
    "city":test.city,
    "county":test.county
})
table
