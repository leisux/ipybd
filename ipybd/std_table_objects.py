from ipybd.core import RestructureTable
from ipybd.std_table_terms import *
import json
import os
import pandas as pd
from ipybd.core import NpEncoder
import jsonschema
from ipybd.lib.noi_occurrence_schema import schema


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
    def __init__(self, *args, **kwargs):
        if isinstance(args[0], pd.DataFrame):
            self.json_file_path = os.getcwd()
        else:
            path_elms = os.path.splitext(args[0])
            if path_elms[1] == "":
                # 如果不是从文件中获得数据
                # 默认使用工作路径存储后续相关数据
                self.json_file_path = os.getcwd()
            else:
                self.json_file_path = path_elms[0]
        super(NoiOccurrence, self).__init__(*args, **kwargs)
        # 对重塑结果中的各列进行重新排序
        self._re_range_columns(cut=True)

    def write_json(self):
        print("\n开始数据质量检查,此处可能耗时较长，请耐心等待...\n")
        valid_datas, unvalid_datas, need_modified = self.datas_verifier()
        print("\n开始打包数据...\n")
        if valid_datas:
            with open(self.json_file_path + '_ready.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(valid_datas, cls=NpEncoder, sort_keys=False, indent=2, separators=(',', ': '),ensure_ascii=False))
            print("合法记录：{} 条".format(len(valid_datas)))
        if need_modified:
            with open(self.json_file_path + '_needcheck.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(need_modified, cls=NpEncoder, sort_keys=False, indent=2, separators=(',', ': '),ensure_ascii=False))
            print("需要进一步修正的记录：{} 条".format(len(need_modified)))
        if unvalid_datas:
            with open(self.json_file_path + '_unvalid.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(unvalid_datas, cls=NpEncoder, sort_keys=False, indent=2, separators=(',', ': '),ensure_ascii=False))
            print("非法记录：{} 条".format(len(unvalid_datas)))
        print("\n数据已经打包完成，请在原路径下查看\n")

    def datas_verifier(self):
        records = list(self.df['DictForNoiOccurrence'])
        valid_datas = []
        unvalid_datas = []
        need_modified = []
        for record in records:
            # 首先将记录人转换为 list
            try:
                record['Occurrence']['recordedBy'] = record['Occurrence']['recordedBy'].split(", ")
            except KeyError:
                pass
            # 然后验证值的合理性
            if self.dirty_data_verifier(record):
                need_modified.append(record)
            else:
                try:
                    # 最后验证 schema 结构的合理性
                    jsonschema.validate(instance=record, schema=schema)
                    valid_datas.append(record)
                except jsonschema.ValidationError:
                    unvalid_datas.append(record)
        return valid_datas, unvalid_datas, need_modified

    def dirty_data_verifier(self, node:dict):
        """ 递归检查字典数据的每一个值，以确定是否有疑问的值
        """
        if isinstance(node, dict):
            for v in node.values():
                if self.dirty_data_verifier(v):
                    return True
        if isinstance(node, list):
            for e in node:
                if self.dirty_data_verifier(e):
                    return True
        if isinstance(node, str):
            try:
                if node[0] == '!':
                    return True
            except IndexError:
                return True


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

