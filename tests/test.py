# NoiOccurrence Test
from ipybd import NoiOccurrence

noi = NoiOccurrence(
    r"/Users/xuzhoufeng/OneDrive/PDP/testfile/DataCleaningTest.xlsx")
noi.write_json()


from enum import Enum

# Model Test
from ipybd import imodel


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


from ipybd import CVH

table = CVH(r"C:\Users\xu_zh\OneDrive\PDP\iherbarium\标签推荐模版ss.xlsx")



import pandas as pd

from ipybd import AdminDiv

admindiv = [
    "广东省,阳山",
    "四川省,南川县",
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



# 名称比较
from ipybd import BioName

test = BioName([
    'Rottlera',
    'Actinotinus sinensis Oliv.', 'Furcaria thalictroides (L.) Desv.',
    'Furcaria surattensis (Linn.) Kostel.', 'Furcaria cavanillesii Kostel.',
    'Aalius Rumph. ex Kuntze', 'Asparagopsis (Kunth) Kunth',
    'Ammannia baccifera Linn.', 'Asplenium laserpitiifolium Ching',
    'Canthium horridum Bl.Bijdr.', 'Hydrocotyle sibthorpioides Lam.',
    'Pinus massoniana Lanb.', 'Potentilla discolor Bge.',
    'Senecio scandens Buch.-Ham.', 'Vernonia patula (Dryand.) Merr.',
    'Ficus pumila L.', 'Senecio scandens Buch.-Ham. ex D.Don',
    'Euphorbia thymifolia L.', 'Euonymus japonicus Thunb.',
    'Mussaenda pubescens Dryand.'
    ])

print(test.get('powoAccepted'))


# 名称编码

authors = [
# 双字符等距，本质是 t 和 h 到 n 的距离相等，th 处于名字边缘，无后续运算，同时相互是否倒置，对绝对值没有影响
('Benht', 'Benth'),
('Pozd', 'Podz'),
# 单字符等距，本质是 o 和 i 到 l 的距离相等， o 和 i 都处于边缘，无后续运算需求
('Vignolo', 'Vignoli'),
# 乘壹
('Donnon', 'Donn'),
('Ascher', 'Aschers'),
('De Wild', 'De Wilde'),
('Wende', 'Wend'),
('Sanso', 'Sanson'),
('Anto', 'Anton'),
('Anders', 'Andersr'),
('Viji', 'Vij'),
# 镜像
('Fiori', 'Firoi'),
('Bellie', 'Beille'),
('Gordon', 'Godron'),
('Czetz', 'Cztez'),
('Tiselius', 'Tilesius'),
('E Pereira', 'E Periera'),
('Renier', 'Reiner'),
('Monico', 'Mocino'),
# 乘壹 + 边缘镜像
('Bures', 'Burser'),
# 同首倒置
('Kze ; Kl', 'Kl ; Kze')
]
