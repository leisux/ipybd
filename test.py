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
    'Narcissus enemeritoi (Sánchez-Gómez,A.F.Carrillo,A.Hern.,M.A.Carrión & Güemes) Sánchez-Gómez,A.F.Carrillo,A.Hernández González,M.A.Carrión & Güemes',
    'Adansonia za var. bozy (Jum. & H.Perrier) H.Perrier',
    'Potamogeton iilinoensis var. ventanicola (Hicken) Horn af Rantzien',
    'Hieracium lagopus Soest non Don',
    'Pithecellobium angulatum var. heterophylla (Roxb.) Prain, nom.nud.',
    'Ania elmeri (Ames & sine ref.) A.D.Hawkes',
    'Ophrys vernixia var. regis-ferinandii (Renz) H.Baumann & al.',
    'Lightfootia longifolia var. oppositifolia Sonder p.p.',
    'Bursera exequielii León de la Luz',
    'Bidens cabopulmensis León de la Luz & B.L.Turner',
    'Tachigali spathulipetala L.F.Gomes da Silva, L.J.T.Cardoso, D.B.O.S.Cardoso & H.C.Lim',
    'Convolvulus tricolor subsp. cupanianus (Sa ad) Stace',
    'Calea aldamoides G.H.L. da Silva, Bringel & A.M.Teles',
    'Adiantum thalictroides var. hirsutum (Hook. & Grev.) de la Sota',
    'Acianthera oricola (H.Stenzel) Karremans, Chiron & Van den Berg',
    'Reseda urnigera var. boissieri (Müll.Arg.) Abdallah & de Wit',
    'Cereus auratus var. intermedius Regel & Klein bis',
    'Mitrophyllum articulatum (L.Bolus) de Boer ex H.Jacobsen',
    'Ulex parviflorus subsp. willkommii (Webb) Borja & al.',
    'Lycopodioideae W.H.Wagner & Beitel ex B.Øllg.',
    'Polygala paludosa var. myurus A.St.-Hil. in A.St.-Hil., Juss. & Cambess.',
    'Phyllostachys nigra var. stauntonii (Munro) Keng f. ex Q.F.Zheng & Y.M.Lin',
    'Salix cordata var. angustifolia Zabel in Beissn., Schelle & Zabel',
    'Tsugaxpicea hookeriana (A.Murray bis) M.Van Campo-Duplan and H.Gaussen',
    'Centaurea biokorensis Teyber amend.Radic',
    'Elaeagnus lanceolata Warb. apud',
    # 下一个名字无法正确拆分
    'Ocotea caesariata van der Werff',
    'Aiouea palaciosii (van der Werff) R.Rohde',
    # 下一个名字无法正确拆分
    'Saxifraga rufescens bal f. f.',
    'Saxifraga rufescens Bal f. f. var. uninervata J. T. Pan',
    'Bulbophyllum nigricans (Aver.) J.J.Verm., Schuit. & de Vogel',
    'Dactyloctenium mucronatum var. contractum Nees in Seem.',
    'Microcephala discoidea var. discoidea (Ledeb.) K.Bremer, H.Eklund, Medhanie, Heiðm., N.Laurent, Maad, Niklasson & A.Nordin',
    'Afzelia xylocarpa (Kurz) Cra',
    'Passiflora × alatocaerulea Lindl.',
    'Convolvulus ×turcicus nothosubsp. peshmenii (C.Aykurt & Sümbül) ined.',
    'Betula ×piperi Britton, pro spec. & C.L.Hitchc.',
    'Aster ×versicolor Willd.(pro sp.)',
    'Sapium chihsinianum S．lee',
    'Opithandra dalzielii (W.W.S.mit',
    'Opithandra dalzielii (W.W.S.mit)',
    'Sycopsis salicifolia Li apud Wa',
    'Plumeria cv. Acutifolia',
    'Phegopteris decursive-pinnata (van Hall)',
    'Eurya handel-mazzettii Hung T. Chang',
    'Saxifraga umbellulata Hook. f. et Thoms. var. pectinata (C. Marq. et Airy Shaw) J. T. Pan',
    'Cerasus pseudocerasus (Lindl.)G.Don',
    'Anemone demissa Hook. f. et Thoms. var. yunnanensis Franch.',
    'Schisandra grandiflora (Wall.) Hook. f. et Thoms.',
    'Phaeonychium parryoides (Kurz ex Hook. f. et T. Anderson) O. E. Schulz',
    'Crucihimalaya lasiocarpa (Hook. f. et Thoms.) Al-Shehbaz et al.',
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



# 名称比较
from ipybd import BioName

test = BioName([
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