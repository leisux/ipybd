from ipybd.core import RestructureTable
from ipybd.std_table_terms import *
import json


class OccurrenceRecord(RestructureTable):
    columns_model = OccurrenceTerms
    def __init__(self, io):
        super(OccurrenceRecord, self).__init__(io)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns()


class NoiOccurrence(RestructureTable):
    columns_model = NoiOccurrenceTerms
    def __init__(self, io):
        super(NoiOccurrence, self).__init__(io)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)


class KingdoniaPlant(RestructureTable):
    columns_model = KingdoniaPlantTerms
    def __init__(self, io):
        super(KingdoniaPlant, self).__init__(io, fcol = True)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)
        self.cleaning_identifications()

    def cleaning_identifications(self):
        self.df['identifications'] = [
            None if idt[0][0]=='unknown' 
            else json.dumps(idt, ensure_ascii=False) 
            for idt in self.df['identifications']
            ]
