from ipybd.core import RestructureTable
from ipybd.std_table_terms import *
import json


class OccurrenceRecord(RestructureTable):
    columns_model = OccurrenceTerms
    def __init__(self, io):
        super(OccurrenceRecord, self).__init__(io)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns()


class KingdoniaPlant(RestructureTable):
    columns_model = KingdoniaPlantTerms
    def __init__(self, io):
        super(KingdoniaPlant, self).__init__(io, fcol = True)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)
        self.meger_mult_idents()

    # Kingdonia 系统可以同时导入多个鉴定，每个鉴定及其相关信息组成一个json array
    # [['Murdannia undulata', '洪德元', '1974-01-01 00:00:01', 'type']]
    def meger_mult_idents(self):
        self.df['identifications'] = list(
            map(
            lambda v:json.dumps([v],ensure_ascii=False), 
            self.df['identifications']
            )
        )
