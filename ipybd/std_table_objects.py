from ipybd.core import RestructureTable
from ipybd.std_table_terms import *
import json


def record(enum_columns, cut=False):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._re_range_columns(cut)

    cls_name = enum_columns.__name__
    cls_attrs = dict(columns_model=enum_columns, __init__=__init__)

    return type(cls_name, (RestructureTable,), cls_attrs)


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
        super(KingdoniaPlant, self).__init__(io, fcol=None)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)
        self.cleaning_null_identifications()

    def cleaning_null_identifications(self):
        self.df['identifications'] = [
            None if idt[0][0]=='unknown'
            else json.dumps(idt, ensure_ascii=False)
            for idt in self.df['identifications']
            ]


class NSII(RestructureTable):
    columns_model = NsiiTerms
    def __init__(self, io):
        super(NSII, self).__init__(io)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)

