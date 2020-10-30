from ipybd.noi import Link
from ipybd import OccurrenceRecord, NoiOccurrence

data = [{'Occurrence': {'occurrenceID': 'KUN:1233170',
                        'catalogNumber': '1233170',
                        'otherCatalogNumbers': '0969439',
                        'recordedBy': '陈文允,于文涛,黄永江',
                        'recordNumber': 'CYH036',
                        'individualCount': 2,
                        'lifeStage': '无花有果',
                        'disposition': '在库',
                        'associatedMedia': ['http://upyun.kingdonia.org/KUN/img/11/2019_08_09/d5c142da27c2fb41_11_1565324738.jpg'],
                        'occurrenceRemarks': '{"入库批号": "Z201103", "采集单位": "周浙昆", "伴生": "乌头，钩柱唐松草，尼泊尔蝇子草，狭苞橐吾，穗花荆芥等"}'},
         'Location': {'country': '中国',
                      'province': '四川省',
                      'city': '甘孜藏族自治州',
                      'county': '巴塘县',
                      'locality': '德达乡',
                      'decimalLatitude': 30.266389,
                      'decimalLongitude': 99.455,
                      'minimumElevationInMeters': 3963.0,
                      'maximumElevationInMeters': 3963.0},
         'Identification': [{'vernacularName': '钩柱唐松草',
                             'scientificName': 'Thalictrum ',
                             'identifiedBy': '于文涛',
                             'dateIdentified': '2010-12-20T00:00:00+08:00'}],
         'Event': {'eventDate': '2010-09-09T00:00:00+08:00',
                   'habitat': '山坡，沟谷中'},
         'Record': {'institutionCode': 'KUN',
                    'classification': 'Angiospermae',
                    'basisOfRecord': '馆藏标本',
                    'rights': 'GBWS',
                    'rightsHolder': 'KUN',
                    'licence': 'http://www.cvh.ac.cn'}}]

noi = NoiOccurrence(r'/Users/xuzhoufeng/OneDrive/xmwj/NOI/gbwstest.xlsx')
noi.save_table(r'/Users/xuzhoufeng/OneDrive/xmwj/NOI/gbws.xlsx')
datas = noi.df['DictForNoiOccurrence']

test = Link(datas, "KUN", 9)
test.link()
print(test.unvalid_resps)
