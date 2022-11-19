# -*- coding: utf-8 -*-
# Based on python 3

import json
import os
import re
from types import FunctionType, MethodType
from warnings import filterwarnings

import numpy as np
import pandas as pd
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt
from tqdm import tqdm

filterwarnings('error', category=UserWarning)

from ipybd.function.cleaner import (AdminDiv, BioName, DateTime, GeoCoordinate,
                                    HumanName, Number, RadioInput, UniqueID)

HERE = os.path.dirname(__file__)
STD_TERMS_ALIAS_PATH = os.path.join(HERE, 'lib', 'std_fields_alias.json')
PERSONAL_TEMPLATE_PATH = os.path.join(HERE, 'lib', 'personal_table_map.json')


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


class ExpressionCompleter(Completer):
    def __init__(self, raw_fields, std_fields, field_alias):
        self._raw_fields = list(raw_fields)
        self._std_fields = list(std_fields)
        self._field_alias = field_alias
        self._fields_num = [n for n, _ in enumerate(self._raw_fields)]
        self._fields_num.extend([m for m, _ in enumerate(self._std_fields)])
        self.terms = self._raw_fields + self._std_fields
        # print(self.terms)

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        for i, field in enumerate(self.terms):
            try:
                if word in field or word in self._field_alias[field]:
                    if self._fields_num[i] < i:
                        alias = self._field_alias[field]
                        display = HTML(
                            "%s<b>:</b> <ansired>%s</ansired>"
                        ) % (field, alias)
                    else:
                        display = field
                    yield Completion(
                        str(self._fields_num[i]),
                        start_position=-len(word),
                        display=display,
                    )
            except KeyError:
                continue


class FormatDataset:
    with open(STD_TERMS_ALIAS_PATH, encoding="utf-8") as std_alias:
        std_field_alias = json.load(std_alias)

    def __init__(self, *args, **kwargs):
        self.df = self.read_data(*args, **kwargs)
        self.fields_manual_mapping = dict.fromkeys(self.df.columns)
        self.raw_columns = tuple(self.df.columns)
        self.size = self.df.size

    def table_mapping(self, mapping: dict):
        """按照给定的 dict 对 dataframe 各列进行列拆分、合并、修改列名

            mapping: dataframe 需要重塑的各列映射关系，相应写法如下：
                     改列名 raw_fied:new_field
                     列拆分 (raw_field, (sp1, sp2, sp3)):(new1,new2,new3)
                     列合并 (raw1, raw2, raw3, (sp1,sp2)):new_field
                     其中 raw 为原列名，new 为新列名，sp 为列合并或分割的分隔符
        """
        for org_field, new_field in mapping.items():
            # 只修改列名
            if isinstance(org_field, str):
                self.df.rename(columns={org_field: new_field}, inplace=True)
            # 列拆分
            elif len(org_field) == 2 and isinstance(org_field, tuple):
                self.split_column(org_field[0], org_field[1], new_field)
            # 列合并
            elif len(org_field) > 2 and isinstance(org_field, tuple):
                self.merge_columns(org_field[:-1], org_field[-1], new_field)
            else:
                print("\n{0}:{1} 映射有误\n".format(org_field, new_field))

    def concat_and_rename_columns(self, new_columns):
        """ 为 self.df 拼接新列
            new_columns 为 Dataframe 或者 Series 对象
            return: None
        """
        try:
            new_headers = new_columns.columns
        except AttributeError:
            new_headers = [new_columns.name]
        is_repeats = [header in self.df.columns for header in new_headers]
        for is_repeat, header in zip(is_repeats, new_headers):
            if is_repeat: self.df.rename({header:''.join([header, '_'])}, axis=1, inplace=True)
        self.df = pd.concat([self.df, new_columns], axis=1)

    def split_column(self, column, splitters, new_headers=None, inplace=True):
        """ 将一列分割成多列

            column: 要分割的列名 str
            splitters: 分割依据的分割符 tuple 或 str
            new_heaers: 分割出的新列列名 list
            return: 若 new_headers=None，返回list组成的拆分结果，
                    如果有新列名，则返回由新列组成的 DataFrame,
                    如果列值无法拆分出足够的列，则用 None 补齐空列
                    如果数值类型不可拆分，则不作处理
        """
        if isinstance(splitters, str):
            splitters = (splitters,)
        frame = map(
            self.__split_txt,
            self.df[column],
            (splitters for _ in range(self.df.shape[0]))
        )
        if new_headers:
            frame = pd.DataFrame(frame)
            frame.columns = new_headers
            if inplace:
                self.df.drop(column, axis=1, inplace=True)
                self.df = pd.concat([self.df, frame], axis=1)
            else:
                # 新产生的列名,如果与原有列名有重复, 则使用单下划线进行标记
                # 在使用模型处理数据列时, 该后缀的列名将会做进一步的处理
                self.concat_and_rename_columns(frame)
        else:
            return list(frame)

    def __split_txt(self, txt, splitters) -> list:
        result = [txt]
        for splitter in splitters:
            try:
                if splitter == "$":
                    # 中英文分列
                    match = re.match(
                        r"[\s\"\']*[\u4e00-\u9fa5][^a-zA-Z0-9]*",
                        result[-1]
                    )
                    if match:
                        result[-1:] = [
                            match.group(0).strip(),
                            result[-1][match.span()[1]:]
                        ]
                    else:
                        match = re.match(
                            r"[\s\"\']*[a-zA-Z0-9][^\u4e00-\u9fa5]*",
                            result[-1]
                        )
                        if match:
                            result[-1:] = [
                                match.group(0).strip(),
                                result[-1][match.span()[1]:]
                            ]
                else:
                    result[-1:] = result[-1].split(splitter, 1)
            except (TypeError, AttributeError):
                pass
        # 未能按照预期拆分出来的元素，用 None 补齐
        # 因此可以让拆分出的新列总是符合预期
        result.extend((len(splitters)-len(result)+1)*[None])
        return result

    def merge_columns(self, columns, separators, new_header=None, inplace=True):
        """ 按指定模式合并多列

            columns：self.df 列名 list
            separators: 合并后，各列值之间的分隔符，如果各列之间分隔符不同，可
                        按序组成 元组传递
                        如果传递的是字符 'd', 'r', 'o', 'l', 'a' 则分别表示将各
                        列合 并成字典、行列，json object 对象、json array 对象。
            new_header: 新列名, 若为 None 则不删除旧列、生成新列、返回 list 结果
            inplace: 生成新的列后, 是否需要删除参与合并的列
        """
        if separators == 'r':
            mergers = self._merge2pairs(columns, typ='rowList')
        elif separators == 't':
            mergers = self._merge2pairs(columns, typ='kvText')
        elif separators == 'o':
            mergers = self._merge2pairs(columns, typ='jsonObject')
        elif separators == 'a':
            mergers = self._merge2pairs(columns, typ='jsonArray')
        elif separators == 'l':
            mergers = self._merge2pairs(columns, typ='list')
        elif separators == 'd':
            mergers = self._merge2pairs(columns, typ='dict')
        elif isinstance(separators, str):
            mergers = self.df[columns[0]]
            for column in columns[1:]:
                mergers = map(
                    self.__merge_txt2line,
                    mergers,
                    self.df[column],
                    (separators for _ in range(self.df.shape[0]))
                )
        elif isinstance(separators, tuple):
            mergers = self.df[columns[0]]
            for column, sepa in zip(columns[1:], separators):
                mergers = list(map(
                    self.__merge_txt2line,
                    mergers,
                    self.df[column],
                    (sepa for _ in range(self.df.shape[0]))
                ))
        if new_header:
            if inplace:
                self.df.drop(columns, axis=1, inplace=True)
            elif new_header in self.df.columns:
                # 对于新生成的列名, 与已有的列名发生重复, 将原有列先用单 _ 进行标记
                # 模型在处理具有单下划线后缀的字段名时, 会进行进一步的处理
                self.df.rename({new_header: ''.join([new_header, '_'])}, axis=1, inplace=True)
            else:
                pass
            self.df[new_header] = pd.Series(mergers)
        else:
            if isinstance(mergers, map):
                return list(mergers)
            else:
                return mergers

    def _merge2pairs(self, columns, typ='dict'):
        try:
            mergers = list(self.df[columns].to_dict("records"))
        except UserWarning:
            # 出现此错误，说明 columns 中有元素在 self.df.columns 中可能存在多个同名
            # 如果人工和模型指定的对应关系没有错误，那么极有可能是原始字段中存在字段名
            # 误用的情形：
            # 比如转换关系中存在 rights:$rightsHolder, rightsHolder:$dataFrom
            # 这样的关系，且 rights 和 rightsHolder 在原始数据中是独立的两列，
            # 那么最终这两列都会被转换为 dataFrom 而非用户所希望的 rightsHolder 和
            # dataFrom 造成这一问题的原因在于 rightsHolder 在原始表中的语义被误用了，
            # 而该字段名又需要被赋予原始数据中的其他列，当程序先执行 rights 到
            # rightsHolder 的映射后，self.df 中就会存在两个 rightsHolder，
            # 程序再次执行 rightsHolder  到 dataFrom 转换是，
            # 就又会将两列 rightsHolder 全部转换为 dataFrame
            # 当 rightsholder 再次被调用时，就会在此处产生警告。
            # 此问题可以通过更改字段转换顺序予以解决
            # 也可以在转换关系确定后，通过程序进行初步的筛查
            # 这些等后面有时间再完善把！
            raise ValueError("字段转换中，存在环状转换链，请检查原始字段是否有字段名误用!\n")
        for i, r in enumerate(mergers):
            c = r.copy()
            for title, value in c.items():
                # if not pd.Series(value).any():
                try:
                    if pd.isnull(value):
                        del r[title]
                except ValueError:
                    if pd.isnull(value).all():
                        del r[title]
            if r == {}:
                mergers[i] = None
                continue
            if typ == 'dict':
                continue
            if typ == 'list':
                mergers[i] = list(r.values())
            if typ == 'jsonObject':
                mergers[i] = json.dumps(r, cls=NpEncoder, ensure_ascii=False)
            if typ == 'rowList':
                dict2txt = map(lambda kv: "：".join(kv), tuple(r.items()))
                mergers[i] = "\n".join(dict2txt)
            if typ == 'kvText':
                dict2txt = map(lambda kv: "：".join(kv), tuple(r.items()))
                mergers[i] = "；".join(dict2txt)
            if typ == 'jsonArray':
                mergers[i] = json.dumps(
                    list(r.values()), cls=NpEncoder, ensure_ascii=False
                )
        return mergers

    def __merge_txt2line(self, ahead_txt, next_txt, separator):
        if pd.isnull(ahead_txt):
            if pd.isnull(next_txt):
                return None
            else:
                return next_txt
        else:
            if pd.isnull(next_txt):
                return ahead_txt
            else:
                try:
                    return separator.join([ahead_txt, next_txt])
                except:
                    return separator.join([str(ahead_txt), str(next_txt)])

    def _prt_items(self, col_num, seq, seq_num=None):
        for n, v in enumerate(seq):
            if seq_num:
                strings = "{0}. {1}".format(seq_num.index(v), v)
            elif type(v) == str:
                strings = "{0}. {1}".format(n+1, v)
            else:
                strings = "{0}. {1}".format(n+1, v[:-1])
            if (n+1) % col_num > 0:
                print(strings.ljust(25), end="\t")
            else:
                print(strings.ljust(25), end="\n")

    def __mapping_clean(self, org_field):
        try:
            del self.fields_manual_mapping[org_field]
            return []
        except KeyError:  # 字段在之前已经删除，或者被用于拆分或合并
            relax_field = []
            del_field = None
            for field in self.fields_manual_mapping:
                if isinstance(field, tuple) and org_field in field:
                    del_field = field
                    relax_field = list(field[:1])
                    relax_field.remove(org_field)
                    break
            if del_field:
                del self.fields_manual_mapping[del_field]
            return relax_field

    def __unmapped_columns2std(self, unmapped_fields: list):
        """解析用户通过表达式说明的列名重组意图

        unmapped_fields: 未能与标准列名表形成对应关系的表格原始列名序列

        func: 用户输入的表达式以指定列名的拆分/合并/转换的映射关系，其规则如下：
            合并表达式：2 ; 4 , 5 = 11; 拆分表达式 11 = 2 ; 4 , 5
            其中 = 号之前的数字为原始表格列名排序序号， = 号之后为标准列名序号；
            数字之间的标点符号，为数据列按照映射关系进行拆分或合并的分隔符号；
            拆分表达式 = 号之前只能有一个列名序号，合并表达式 = 号之后只能有一
            个标准列名序号。
            手动处理获得得最新映射关系将被存储在 self.fields_manual_mapping 中。

        return: 返回尚未被手动处理的列名序列
        """

        print("\n\n以下是还需通过手录表达式指定其标准名的原始表格表头：\n")
        self._prt_items(2, unmapped_fields, self.raw_columns)
        expression = prompt("\n\n请输入列名转换表达式，录入 0 忽略所有：",
                            completer=ExpressionCompleter(
                                self.raw_columns,
                                self._stdfields,
                                FormatDataset.std_field_alias),
                            complete_while_typing=False
                            )
        # 如果忽略所有，这些列名将映射到自身
        if expression.strip() == "0":
            for field in unmapped_fields:
                self.fields_manual_mapping[field] = field
            return None
        p_raw2std = re.compile(r"([dlroa]?)\s*(\d+)([^\d]*)")
        elements = p_raw2std.findall(expression)
        if len(elements) < 2:
            print("\n录入的表达式有误，请重新输入")
            return unmapped_fields
        # 一个或多个列名合并为单个标准列名
        if elements[-2][-1].strip() == "=" and elements[-1][-1].strip() == "":
            nums2merge = [num[1] for num in elements[0:-1]]
            std_field_num = elements[-1][1]
            try:
                fields2merge = [self.raw_columns[int(n)] for n in nums2merge]
                std_field = self._stdfields[int(std_field_num)]
            except IndexError:
                print("\n输入的表达式数值有误，请重新输入\n")
            for field in fields2merge:
                try:
                    unmapped_fields.remove(field)
                except ValueError:  # 字段之前已经映射，又被用于与其他字段合并
                    pass
                # 若该字段之前已经被映射，删除之前的映射，
                # 并将相关字段重新加入未映射
                unmapped_fields.extend(self.__mapping_clean(field))
            # 分隔符是空格的，保留一个空格，非空格的分隔符去除两侧空格
            if elements[0][0] in ['d', 'l', 'r', 'o', 'a']:
                separators = elements[0][0]
            else:
                separators = tuple(
                    sep[2].strip() if set(sep[2]) != {" "} else " "
                    for sep in elements[0:-2]
                )
            if separators == ():
                # 如果合并的列名只有一个，为一对一映射
                self.fields_manual_mapping.update(
                    {fields2merge[0]: std_field})
            else:
                fields2merge.append(separators)
                self.fields_manual_mapping.update(
                    {tuple(fields2merge): std_field})
        # 单个列名分拆为多个标准列名
        elif elements[0][-1].strip() == "=" and elements[-1][-1].strip() == "":
            num2split = elements[0][1]
            num2stdfields = [num[1] for num in elements[1:]]
            if len(num2stdfields) > len(set(num2stdfields)):
                print("\n拆分表达式存在重复，请重新输入\n")
                return unmapped_fields
            try:
                field2split = [self.raw_columns[int(num2split)]]
                std_fields = tuple(self._stdfields[int(n)]
                                   for n in num2stdfields)
            except IndexError:
                print("\n输入的表达式数值有误，请重新输入\n")
            try:
                unmapped_fields.remove(field2split[0])
            except ValueError:
                pass
            # 若该字段之前已经被映射，删除之前映射，并将相关字段重新加入未映射
            unmapped_fields.extend(self.__mapping_clean(field2split[0]))
            # 分隔符是空格的，保留一个空格，非空格的分隔符去除两侧空格
            splitters = tuple(
                spl[2].strip() if set(spl[2]) != {" "} else " "
                for spl in elements[1:-1]
            )
            field2split.append(splitters)
            self.fields_manual_mapping.update(
                {tuple(field2split): std_fields})
            # print(self.fields_manual_mapping)
        else:
            print("\n录入的表达式有误，请重新输入\n")
        return unmapped_fields

    def __manual2std_fields(self, invalid_mapping: dict):
        # 手动解决映射冲突，意味着一定会产生无映射字段，先建立无映射字段容器
        try:
            unmapped_fields = invalid_mapping[None]
        except KeyError:
            unmapped_fields = []
        # 对于冲突的映射，先给出冲突项，人工选择正确的映射关系
        for std_field, raw_fields in invalid_mapping.items():
            if std_field:
                print(
                    "\n\n以下多个列名指向 {0} 字段，请选择与之正确对应的，若均不正确，请输入 0 忽略所有：\n\n".format(std_field))
                self._prt_items(2, raw_fields)
                # 正确映射的列名需从冲突列名序列内删除
                while True:
                    try:
                        i = input("\n\n {0}: ".format(std_field))
                        if int(i) == 0:
                            break
                        else:
                            raw_fields.remove(raw_fields[int(i)-1])
                            break
                    except (IndexError, ValueError):
                        print("\n录入的数字有误，请重新输入\n")
                # 解除重复的映射关系，
                # 并将映射错误的原始列名写入无对应关系的列名序列内
                for raw_field in raw_fields:
                    try:
                        del self.fields_manual_mapping[raw_field]
                    except KeyError:
                        pass
                    if type(raw_field) == tuple:
                        unmapped_fields.extend(set(raw_field[:-1]))
                    else:
                        unmapped_fields.append(raw_field)
        unmapped_fields = list(set(unmapped_fields))
        # 对于没有映射关系的原始列名，
        # 人工录入表达式以指定：拆分、合并、转换等映射关系
        while unmapped_fields:
            unmapped_fields = self.__unmapped_columns2std(unmapped_fields)

    def __check_duplicate_mapping(self):
        mapping_fields = list(self.fields_manual_mapping.values())
        for v in self.fields_manual_mapping.values():
            if type(v) == tuple:
                mapping_fields.remove(v)
                mapping_fields.extend(v)
        invalid_mapping = {}
        for std_field in set(mapping_fields):
            # 重复对应或者无对应的字段，都会作为无效映射
            if mapping_fields.count(std_field) > 1 or std_field is None:
                raw_fields = []
                for rawfield, map_field in self.fields_manual_mapping.items():
                    if std_field == map_field:
                        raw_fields.append(rawfield)
                    # 被手动拆分的字段，也可能与其他映射字段存在冲突
                    elif type(map_field) == tuple and std_field in map_field:
                        raw_fields.append(rawfield)
                invalid_mapping.update({std_field: raw_fields})
        return invalid_mapping

    def __auto2std_field(self, raw_field):
        # 首先找出表格列名中使用标准名称的列名
        if raw_field in FormatDataset.std_field_alias:
            self.fields_manual_mapping[raw_field] = raw_field
        else:
            # 如果列名用的不是标准名子，逐个比较别名库，找到对应的标准名称
            std_options = []
            for k, v in FormatDataset.std_field_alias.items():
                if raw_field.upper() in v:
                    std_options.append(k)
            if len(std_options) == 1:
                self.fields_manual_mapping[raw_field] = std_options[0]
            elif len(std_options) == 0:
                self.fields_manual_mapping[raw_field] = None
            # 如果有多个标准名与该列名对应，咨询用户，让其手动确定需要对应哪一个
            else:
                print(
                    "\n\n原表中 {0} 列有多个标准字段名与之对应：\
                    \n".format(raw_field)
                )
                while True:
                    self._prt_items(2, std_options)
                    choice2std = input("\n请从潜在对应中选择一个，都不是录入 0：")
                    if choice2std.strip() == "0":
                        self.fields_manual_mapping[raw_field] = None
                        break
                    try:
                        self.fields_manual_mapping[raw_field] = std_options[int(
                            choice2std)-1]
                        break
                    except (IndexError, ValueError):
                        print("\n所选值有误，请重新输入\n")

    def build_mapping_template(self):
        """ 建立数据表映射关系

            这个过程中不对数据表进行任何实际操作
        """
        for raw_field in tqdm(self.fields_manual_mapping, desc="列名映射", ascii=True):
            self.__auto2std_field(raw_field)
        invalid_mapping = self.__check_duplicate_mapping()
        self._stdfields = tuple(FormatDataset.std_field_alias.keys())
        while invalid_mapping:
            # print("\n下方式是可以映射的标准列名序列表：\n")
            # self._prt_items(2, self._stdfields)
            self.__manual2std_fields(invalid_mapping)
            invalid_mapping = self.__check_duplicate_mapping()
        # 完成的映射，存储于私人模板之中，避免用户日后再次执行映
        # print(self.fields_manual_mapping)
        json_template = {str(k): str(v)
                         for k, v in self.fields_manual_mapping.items()}
        # 防止 ipybd 运行没有获得系统管理员权限，写入文件被拒而被终止
        try:
            with open(PERSONAL_TEMPLATE_PATH, "w", encoding="utf-8") as pt:
                pt.write(json.dumps(json_template, ensure_ascii=False))
        except PermissionError:
            print("\n提醒：使用系统管理员权限运行终端，iPybd 可记录转换历史！\n")
            pass
    
    def rename_duplicate_headers(self, tail_cols_num=None):
        """ 为 self.df 中重复的列名添加一致多个 _ 后缀
            new_cols_num: 设置可忽视 self.df 尾部列名的数量
        """ 
        if tail_cols_num:
            headers = self.df.columns[:-tail_cols_num]
            duplicates = np.append(headers.duplicated(), [False]*tail_cols_num)
        else:
            duplicates = self.df.columns.duplicated()
        while self.df.columns.has_duplicates:
            self.df.columns = [header + '_' if duplicates[j] else header for j, header in enumerate(self.df.columns)]

    def to_excel(self, path):
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            # 下面原由的这段代码，应该是 xlsxwriter 的engine 参数，
            # 使用 openpyxl报错具体原因待确实，先隐去处理
            #engine_kwargs={"options":{'strngs_to_urls':False}})
            self.df.to_excel(writer, index=False)

    def save_data(self, path):
        if path.endswith('.xlsx'):
            self.to_excel(path)
        elif path.endswith('.xls'):
            self.to_excel(path)
        elif path.endswith('.csv'):
            self.df.to_csv(path, index=None, encoding='utf-8-sig')
        elif path.endswith('.sql'):
            pass
        else:
            raise ValueError("file type must be sql, csv, excel!")

    def read_data(self, *args, **kwargs):
        if isinstance(args[0], pd.DataFrame):
            return args[0]
        if isinstance(args[0], str):
            path_elms = os.path.splitext(args[0])
            if path_elms[1].lower() in [".xls", ".xlsx"]:
                print(
                    "\n开始载入数据表格...\n\n如果数据表格太大，此处可能会耗时很长...\n如果长时间无法载入，请将 Excel 表转换为 CSV 格式后重新尝试...\n")
                table = pd.read_excel(*args, dtype=str, engine='openpyxl', **kwargs)
            elif path_elms[1].lower() == '.csv':
                table = self.read_csv(*args, **kwargs)
            elif path_elms[1].lower() == '.txt':
                table = pd.read_data(*args, **kwargs)
            elif path_elms[1].lower() == ".json":
                table = pd.read_json(*args, **kwargs)
            elif path_elms[1].lower() == "":
                table = pd.read_sql(*args, **kwargs)
        print("\n数据表载入完毕。\n")
        return table

    def read_csv(self, *args, dtype=str, chunksize=20000, **kwargs):
        reader = pd.read_csv(*args, dtype=str, chunksize=20000, **kwargs)
        table = []
        for chunk in reader:
            table.append(chunk)
        table = pd.concat(table, axis=0)
        return table

    def get_name(func):
        def get_func(self, *args, **kwargs):
            get_action, headers, concat, new_headers = func(
                self, *args, **kwargs)
            try:
                if self.name_cache == headers:
                    pass
                else:
                    self.name_cache = headers
                    if len(headers) > 1:
                        names = self.merge_columns(list(headers), " ")
                    else:
                        names = self.df[headers[0]]
                    self.bioname = BioName(names)
            except AttributeError:
                self.name_cache = headers
                if len(headers) > 1:
                    names = self.merge_columns(list(headers), " ")
                else:
                    names = self.df[headers[0]]
                self.bioname = BioName(names)
            finally:
                if isinstance(get_action, str) and get_action in ['simpleName', 'apiName', 'scientificName', 'plantSplitName', 'fullPlantSplitName', 'animalSplitName']:
                    results = self.bioname.format_latin_names(get_action)
                else:
                    results = self.bioname.get(get_action)
            if concat and results:
                new_columns = pd.DataFrame(results)
                new_columns.columns = new_headers
                self.df = pd.concat([self.df, new_columns], axis=1)
            else:
                return results
        return get_func

    @get_name
    def format_scientificname(self, *headers, pattern, new_headers=None, concat=False):
        return pattern, headers, concat, new_headers
    
    @get_name
    def get_native_name(self, *headers, lib:'Series', new_header=('nativeName', 'nativeAuthor'), concat=False):
        return lib, headers, concat, new_header

    @get_name
    def name_spell_check(self, *headers, concat=False):
        return 'stdName', headers, concat, ('nameSpellCheck', 'nameAuthors', 'mixFamily', 'mixCode')

    @get_name
    def get_tropicos_accepted(self, *headers, concat=False):
        return 'tropicosAccepted', headers, concat, ('tropicosAccepted',)

    @get_name
    def get_tropicos_name(self, *headers, concat=False):
        return 'tropicosName', headers, concat, ('tropicosName', 'tropicosAuthors',
                                             'tropicosFamily', 'tropicosNameId')
    @get_name
    def get_ipni_name(self, *headers, concat=False):
        return 'ipniName', headers, concat, ('ipniName', 'ipniAuthors',
                                             'ipniFamily', 'ipniNameLsid')

    @get_name
    def get_ipni_reference(self, *headers, concat=False):
        return 'ipniReference', headers, concat, ('publishingAuthor',
            'publication', 'referenceCollation', 'publicationYear',
            'publicationYearNote', 'referenceRemarks', 'citationReference',
            'bhlLink', 'ipniPublicationLsid')

    @get_name
    def get_powo_name(self, *headers, concat=False):
        return 'powoName', headers, concat, ('powoName', 'powoAuthors',
                                             'powoFamily', 'ipniNameLsid')

    @get_name
    def get_powo_images(self, *headers, concat=False):
        return 'powoImages', headers, concat, (
            'powoImage1', 'powoImage2', 'powoImage3')

    @get_name
    def get_powo_accepted(self, *headers, concat=False):
        return 'powoAccepted', headers, concat, ('powoAccepted',)

    @get_name
    def get_col_taxontree(self, *headers, concat=False):
        return 'colTaxonTree', headers, concat, (
            'colGenus', 'colFamily', 'colOrder', 'colClass', 'colPhylum', 'colKingdom')

    @get_name
    def get_col_name(self, *headers, concat=False):
        return 'colName', headers, concat, ('colName', 'colAuthors',
                                            'colFamily', 'colCode')

    @get_name
    def get_col_synonyms(self, *headers, concat=False):
        return 'colSynonyms', headers, concat, ('colSynonyms',)

    @get_name
    def get_col_accepted(self, *headers, concat=False):
        return 'colSynonyms', headers, concat, ('colAccepted',)

    def drop_and_concat_columns(func):
        def format_func(self, *args, **kwargs):
            new_columns, headers, inplace = func(self, *args, **kwargs)
            # 将新列的列名修改为原表对应的列名
            try:
                new_columns.columns = headers
            # 如果列数有变，则使用返回的默认列名
            except ValueError:
                pass
            if inplace:
                self.df.drop(headers, axis=1, inplace=True)
                self.df = pd.concat([self.df, new_columns], axis=1)
            else:
                return new_columns
        return format_func

    @drop_and_concat_columns
    def format_latlon(self, *headers, inplace=True):
        """ 格式化经纬度

        headers: 经纬度列名，可以是多个字段名组成的序列，也可以是单个字段名
        inplace: 是否替换 self.df 中相应的列
        """
        headers = list(headers)
        if len(headers) > 1:
            latlon = self.merge_columns(headers, ";")
        else:
            latlon = self.df[headers[0]]
        return GeoCoordinate(latlon)(), headers, inplace

    @drop_and_concat_columns
    def format_admindiv(self, *headers, inplace=True):
        headers = list(headers)
        if len(headers) > 1:
            admindiv = self.merge_columns(headers, ',')
        else:
            admindiv = self.df[headers[0]]
        return AdminDiv(admindiv)(), list(headers), inplace

    @drop_and_concat_columns
    def format_datetime(self, header, style='datetime',
                        timezone='+08:00', mark=False, inplace=True):
        return DateTime(self.df[header], style, timezone)(
            mark), [header], inplace

    @drop_and_concat_columns
    def format_number(self, header1, header2=None, typ=float, min_num=0,
                      max_num=8848, inplace=True, mark=False):
        if header2:
            number = Number(self.df[header1], self.df[header2], typ, min_num,
                            max_num)
            headers = [header1, header2]
        else:
            number = Number(self.df[header1], header2, typ, min_num, max_num)
            headers = [header1]
        return number(mark), headers, inplace

    @drop_and_concat_columns
    def format_options(self, header, lib=None, inplace=True):
        return RadioInput(self.df[header], lib)(), [header], inplace

    @drop_and_concat_columns
    def format_human_name(self, header, inplace=True):
        return HumanName(self.df[header])(), [header], inplace

    @drop_and_concat_columns
    def mark_repeat(self, *headers, inplace=True):
        columns = [self.df[header] for header in headers]
        return UniqueID(*columns)(), list(headers), inplace


class RestructureTableMeta(type):
    def __new__(cls, name, bases, dct):
        if name != 'RestructureTable' and 'columns_model' not in dct:
            raise TypeError(
                'subclass {} should implement columns_model attr'.format(name))
        return super().__new__(cls, name, bases, dct)


class RestructureTable(FormatDataset, metaclass=RestructureTableMeta):
    # self.__class__.columns_model from std_table_objects
    def __init__(self, *args, fields_mapping=False, cut=False, fcol=None, **kwargs):
        super(RestructureTable, self).__init__(*args, **kwargs)
        self.fcol = fcol  # 设置填充缺失列的默认值
        self.fields_mapping = fields_mapping
        self.cut = cut
        self.rebuild_table()

    def rebuild_table(self):
        if self.fields_mapping is False:
            for key in self.fields_manual_mapping:
                self.fields_manual_mapping[key] = key
        elif self.__check_old_mapping():
            # 如果开启字段映射，会自动将数据表头映射至dwc字段名
            self.build_mapping_template()
        # 对表格按照定义的枚举Terms进行重塑
        new_columns = self.rebuild_columns()
        for header in self.fields_manual_mapping:
            # 如果原表格一些未被模型使用的列名与模型定义的新列名重复
            # 这些列名实际上应该已经被模型增加了_ 后缀, 如果对原列名进行处理
            # 则会直接修改模型新增的同名列, 从而导致最终结果与预期不一致
            # 因此这里将保留现有数据列,不再对这些列名按照手动映射的关系进行重塑
            if header in new_columns:
                pass
            else:
                # 对枚举中尚未定义的列按照人工给定的映射关系进行重塑
                self.table_mapping(self.fields_manual_mapping)
        self._re_range_columns(new_columns)

    def __check_old_mapping(self):
        """ 确定用户处理的数据表是否之前已经经过处理

        用户之前处理过的表格字段转换模板存储在personal_table_map.json文件中
        比对当前表格的字段与私人模板中的字段，完全一致，则返回 False
        不一致则返回 True
        """
        with open(PERSONAL_TEMPLATE_PATH, "r", encoding="utf-8") as pt:
            old_mapping = json.load(pt)
        old_columns = []
        for field in old_mapping:
            try:
                # 复合字段使用元组包裹，需要先将 str 转为 tuple
                compound_field = eval(field)[:-1]
                old_columns.extend(compound_field)
            except NameError:
                old_columns.append(field)
            except SyntaxError:
                old_columns.append(field)
            except TypeError:
                # 表头包含包含python内置类型名称，比如 id
                old_columns.append(field)
        # 判断表格字段与之前表格的是否一致
        if set(old_columns) == set(self.raw_columns):
            if input(
                    "\n检测发现该表格与您上一次处理的表格字段一致，请问是否直接使用上一次表格转换模板以简化操作 (y/n) :\n\n") == 'y':
                pass
            else:
                return True
            mapping_columns = tuple(old_mapping.keys())
            for column in mapping_columns:
                if column.startswith("("):
                    try:
                        old_mapping[eval(column)] = eval(old_mapping[column])
                    except NameError:
                        old_mapping[eval(column)] = old_mapping[column]
                    del old_mapping[column]
            self.fields_manual_mapping = old_mapping
            return False
        else:
            return True

    def _re_range_columns(self, columns):
        if not self.cut:
            other_columns = [
                column for column in self.df.columns
                if column not in columns
            ]
            columns.extend(other_columns)
        self.df = self.df.reindex(columns=columns)

    def custom_func_desc(self, series):
        try:
            return pd.concat(series, axis=1)
        except TypeError:
            return pd.DataFrame(series)
        except Exception as e:
            raise e

    def _underline_modifer_parse(self, field):
        if field.endswith('___'):
            inplace = False
            fcol = True
        elif field.endswith('__'):
            inplace = False
            fcol = False  
        elif field.endswith('_'):
            inplace = True
            fcol = True
        else:
            inplace = True
            fcol = False
        return inplace, fcol

    def fields_func_mapping(self, model_key, func, model_args, model_kwargs, fcol, inplace):
        fields_name = model_key.split('__')
        new_columns = []
        args = self.get_args(model_key, model_args, model_kwargs, inplace)
        if args:
            cols, kwargs, org_columns_name, cols_name = args
            if isinstance(func, type):
                # 通过 ipybd 内置类处理数据
                new_cols = func(*cols, **kwargs)()
                # 唯一性标识，可以传递多列进行重复比较
                # 但并不会删除其他参与运算的列，只会更换第一列
                if func.__name__ == 'UniqueID':
                    cols_name[:] = [cols_name[0]]
            else:
                # 通过自定义的函数处理数据
                new_cols = self.custom_func_desc(func(*cols, **kwargs))
            new_cols.columns = fields_name
            if inplace:
                self.df.drop(cols_name, axis=1, inplace=True)
                self.concat_and_rename_columns(new_cols)
                new_columns.extend(fields_name)
            else:
                # 首先从 self.df 中删除现有 df 中相关的数据列, 并将这些数据列暂存
                # 注意这里的 org_columns_name 可能与 self.df.columns存在一对
                # 多列的问题, 但不影响数据处理
                org_columns = self.df[org_columns_name]
                self.df.drop(org_columns_name, axis=1, inplace=True)
                # 然后尝试删除由原数据列进一步合成的可直接参与运算的新数据列
                try:
                    # 如果是先合成了用于运算的新数据列, 则予以删除
                    self.df.drop(cols_name, axis=1, inplace=True)
                except KeyError:
                    # 如果是直接使用 df 相关数据列参与新列的运算, 则不做任何处理
                    pass
                # 然后将新数据列的列名与已有列名进行比较, 如果与原来列名重复, 原列名添加 _
                self.df = pd.concat([self.df, org_columns], axis=1)
                self.concat_and_rename_columns(new_cols)
                # 由于 org_columns_name 可能在合成用于直接运算的 cols_name 时
                # 被重新命名, 这有可能会与之前的列名发生冲突, 所以需要对全列再次进
                # 行重名重命名
                self.rename_duplicate_headers(tail_cols_num=len(fields_name))
                org_columns_name = self.__get_new_headers(org_columns_name)
                new_columns.extend(org_columns_name + fields_name)
        elif fcol:
            self.__fill_nonexistent_columns(fields_name)
            new_columns.extend(fields_name)
        else:
            pass
        return new_columns
    
    def __get_new_headers(self, org_columns_name):
        """ 获得因列名重复, 改名的当前新列名称
            org_columns_name: 原始表格列名组成的 list
            return: 返回新列名组成的 list
        """
        # 数据列拆分或者合并时, 虽然已经对与新产生的列名重复的列名增加了单 _ 后缀
        # 但是在遇到一些列名在模型定义的 key 中被多次重复使用时, 仍然会造成带有单
        # 下划线后缀的列名出现重复, 而这些列名有可能会是 org_columns_name 中相
        # 应列名的原始列名, 因此若模型需要保留原列名, 这些同名列就可能造成调用冲突,
        # 因此这里需要对整表可能重复的列名进一步增加 _ 后缀, 由于合并或者拆分形成
        # 的新列名已经做过去重复处理, 因此该操作不会修改当前新生成的列名
        dup_headers = {header.strip('_'): header for header in self.df.columns if header.endswith('_')}
        for i, header in enumerate(org_columns_name):
            if header in dup_headers:
                org_columns_name[i] = dup_headers[header]
        return org_columns_name
    
    def __fill_nonexistent_columns(self, fields_name):
        for col in fields_name:
            if col not in self.df.columns:
                self.df[col] = self.fcol

    def fields_simple_mapping(self, model_key, params, fcol, inplace):
        fields_name = model_key.split('__')
        new_columns = []
        arg_name = self.model_param_parser(model_key, params, inplace)
        if arg_name:
            org_columns_name, column_name = arg_name
            # 只是修改列名, 在此直接修改
            if isinstance(params, str):
                self.df.rename(
                    columns={column_name: model_key}, inplace=True)
                new_columns.extend(fields_name)
            # 列名是由模型 [...] 表达式中的相应的选项列直接修改列名获得
            elif isinstance(params, list) and column_name != model_key:
                self.df.rename(
                    columns={column_name: model_key}, inplace=True)
                new_columns.extend(fields_name)
            # 数据列经合并、拆分等操作获得
            elif inplace:
                new_columns.extend(fields_name)
            else:
                self.rename_duplicate_headers()
                org_columns_name = self.__get_new_headers(org_columns_name)
                new_columns.extend(org_columns_name + fields_name)
        # 如果原表中无法找到相应的列，用指定的 self.fcol 填充新列
        elif fcol:
            self.__fill_nonexistent_columns(fields_name)
            new_columns.extend(fields_name)
        else:
            pass
        return new_columns

    def rebuild_columns(self):
        """ 按照 std_table_terms 定义的 key 生成新表格的各列
        """
        new_columns = []
        for field in self.__class__.columns_model:
            try:
                params = field.value
                inplace, fcol = self._underline_modifer_parse(field.name)
                raw_fields_name = field.name.strip('_')
                # print(params)
                if not isinstance(params, dict) and isinstance(params[0], (type, FunctionType, MethodType)) and isinstance(params[-1], dict):
                    if isinstance(params[1], tuple) and len(params) == 3:
                        func, model_args, model_kwargs = params
                        columns = self.fields_func_mapping(raw_fields_name, func, model_args, model_kwargs, fcol, inplace)
                    else:
                        raise ValueError("model value error: {}".format(field.name))
                elif isinstance(params, (str, tuple, dict, list)):
                    columns = self.fields_simple_mapping(raw_fields_name, params, fcol, inplace)
                else:
                    raise ValueError("model value error: {}".format(field.name))
            except Exception as e:
                raise e
            new_columns.extend(columns)
        # 去重复&删除已经被多次处理转换为其他列的列名
        # 并尽可能的按照模型定义的顺序返回新的列名
        new_columns.reverse()
        new_columns = sorted(set(new_columns), key=new_columns.index)
        new_columns.reverse()
        return [column for column in new_columns if column in self.df.columns]
    
    def add_fields_mapping(self, headers):
        new_fields_mapping = {header: header for header in headers}
        if self.fields_func_mapping:
            for header in headers:
                if header.endswith('_'):
                    pass
                else:
                    pass

        self.fields_manual_mapping.update(new_fields_mapping)

    def get_args(self, title, args, kwargs, inplace=True):
        """ 获得数据列处理方法的参数
            title: 模型定义的新列名，比如 province__city
            args: 模型相应方法的位置参数表达式，比如 (['$verbatimCoordinates', ('$decimalLatitude', '$decimalLongitude', ';')]
            kwargs: 处理方法所需的关键字参数
            inplace: 是否使用处理获得新列替代参与运算的旧列
            return: None 或者数据列、kwargs、原始数据列名、新数据列名组成的元组
        """
        columns = []
        new_args = []
        org_fields = []
        for param in args:
            if isinstance(param, str) and param.startswith('$'):
                column = self.get_param(title, param[1:], inplace)
                if column:
                    new_args.append(self.df[column[-1]])
                    columns.append(column[-1])
                    org_fields.extend(column[0])
                else:
                    return None
            else:
                try:
                    if isinstance(param, tuple) and param[0].startswith('$'):
                        column = self.model_param_parser(title, param, inplace)
                        if column:
                            new_args.append(self.df[column[-1]])
                            columns.append(column[-1])
                            org_fields.extend(column[0])
                        else:
                            return None
                    elif isinstance(param, list) and param[0][0].startswith('$'):
                        column = self.model_param_parser(title, param, inplace)
                        if column:
                            new_args.append(self.df[column[-1]])
                            columns.append(column[-1])
                            org_fields.extend(column[0])
                        else:
                            return None
                    else:
                        new_args.append(param)
                except AttributeError:
                    new_args.append(param)
        for key, value in kwargs.items():
            if isinstance(value, str) and value.startswith('$'):
                column = self.get_param(title, value[1:], inplace)
                if column:
                    kwargs[key] = self.df[column[-1]]
                    columns.append(column[-1])
                    org_fields.extend(column[0])
                else:
                    return None
            else:
                try:
                    if isinstance(value, tuple) and value[0].startswith('$'):
                        column = self.model_param_parser(title, value, inplace)
                        if column:
                            kwargs[key] = self.df[column[-1]]
                            columns.append(column[-1])
                            org_fields.extend(column[0])
                        else:
                            return None
                    elif isinstance(value, list) and value[0][0].startswith('$'):
                        column = self.model_param_parser(title, value, inplace)
                        if column:
                            kwargs[key] = self.df[column[-1]]
                            columns.append(column[-1])
                            org_fields.extend(column[0])
                        else:
                            return None
                except AttributeError:
                    pass
        return new_args, kwargs, org_fields, columns

    def model_param_parser(self, title, param, inplace=True):
        """ 对模型中定义的各列 value 进行解析
            title: 模型定义的新列名, 如果是列拆分为 list 否则为 str
            param: 模型 value 中的各类参数，可能是 str, dict, tuple, list 
            return: 由 get_param 返回的值进一步检查后，返回 tuple 元素
            tuple 包含两个元素，前一个元素为与此相关的原始表头名组（list)
            后一个元素是单个真实可调用的数据表表头名（str）
        """
        # title 由单列映射
        if isinstance(param, str):
            if param.startswith('$'):
                arg_name = self.get_param(title, param[1:], inplace)
            else:
                raise ValueError('model param of {} error'.format(title))
        # title 由多列合并
        elif isinstance(param, tuple):
            try:
                fields_name = [field[1:] if field.startswith(
                    '$') else None for field in param[:-1]]
                if all(fields_name):
                    fields_name.append(param[-1])
                    arg_name = self.get_param(title, tuple(fields_name), inplace)
                else:
                    raise ValueError('model param of {} error'.format(title))
            except AttributeError:
                raise ValueError('model param of {} error'.format(title))
        # title 是由单列分割而成
        elif isinstance(param, dict):
            # 首先检查数据中是否存在要分割单列
            keys = list(param.keys())
            if len(keys) == 1:
                separators = param[keys[0]]
                param = keys[0]
                new_fields = title.split('__')
                # 如果要拆分的列本身就是由其他列合并而成
                if isinstance(param, tuple):
                    arg_name = self.model_param_parser(title, param, inplace)
                elif isinstance(param, str):
                    arg_name = self.model_param_parser(new_fields, param, inplace)
                else:
                    raise ValueError('model param of {} error'.format(title))
            else:
                raise ValueError('model param of {} error'.format(title))
            if arg_name:
                self.split_column(arg_name[-1], separators, new_fields, inplace)
                return arg_name[0], new_fields 
        # title 有多种可能的方式形成
        elif isinstance(param, list):
            # 如果某个参数有多种可能的情况，则发现首个符合条件的就终止
            for choice in param:
                arg_name = self.model_param_parser(title, choice, inplace)
                if arg_name:
                    return arg_name
        else:
            raise ValueError('model param of {} error'.format(title))
        return arg_name

    def get_param(self, title, param, inplace=True):
        """ 获取模型定义的单个参数列名

        title: 新列名，可能是 str 或 list
        param: 数据模型中定义的数据列参数表达式，可能是 str 或 tuple
               如果是 tuple ，其最后一个元素应该是分隔符
        inplace: 对于需要拆分或者合并到列，是否使用新列替换旧列
        return: None 或 tuple, tuple 包含两个元素，
                原始表头名组(list)与可调用的数据表表头名（str）
                
        """
        if isinstance(param, str):
            fields = self.build_basic_param(param, inplace)
        elif isinstance(param, tuple):
            fields = self.build_basic_param(param[:-1], inplace)
        else:
            raise ValueError('model params error!')
        # 位置参数只要缺失一个，就终止处理
        if fields is None:
            # print("\n{0} 没有在原表中找到对应表头\n".format(param))
            return None
        # 如果是要进行数据列的分列，则检查是否有分列的必要和条件
        columns = fields[-1]
        if isinstance(title, list):
            # 如果数据表中相应的列，与要拆分出的列名一致，则不用再进行分列
            if columns == title:
                return None
            # 否则：检查找到的列是否能够完整构成要拆分的列
            elif isinstance(param, tuple):
                try:
                    # 如果找到的列无法构成完整的待拆分列，则放弃拆分
                    columns.remove(None)
                    return None
                except ValueError:
                    # 如果要拆分出的列数和已有的列数一致，则不再进行拆分
                    if len(columns) == len(title):
                        rename_columns = {}
                        for k,v in zip(columns, title):
                            rename_columns[k] = v
                        self.df.rename(columns=rename_columns,inplace=True)
                        return None
                    else:
                        title = "__".join(title)
        # 对单个参数基本元素做进一步处理
        for n, clm in enumerate(columns):
            # 找到的如果是一个待拆分字段如 [("GPS", (";"))]
            # 则直接用该列名作为实际参数。
            if isinstance(clm, tuple) and len(clm) == 2:
                columns[n] = clm[0]
            # 找到的字段若需进一步合并，先执行合并
            elif isinstance(clm, tuple) and isinstance(param, tuple):
                # 注意 merge_columns 只能接受 list 类型的 columns
                self.merge_columns(list(clm[:-1]), clm[-1], param[n], inplace)
                columns[n] = param[n]
            elif isinstance(clm, tuple) and isinstance(param, str):
                self.merge_columns(list(clm[:-1]), clm[-1], param, inplace)
                columns[n] = param
        # 对整个参数做进一步处理
        if (len(columns) > 1
            or isinstance(param, tuple) and
                param[-1] in ['d', 'l', 'a', 'o', 'r']):
            # 相应的参数需要进一步由多列合并而成比如对于
            # (country, stateProvince, city, county, ",") 的 param
            # 返回的 columns 或许就是 ["国", "省"， ”市“, "县"]，
            # 这个时候需要对 columns 进行进一步的合并才能获得 param
            # 合并之前先去除真实数据表中未能找到的列，
            # 比如 (country, stateProvince, city, county)
            # 这样的单个位置参数是由多个标准列进一步合并而成，
            # 真实数据表中可能就不存在 country，因此先排除没有找到的列
            merge_fields = [col for col in columns if col]
            self.merge_columns(merge_fields, param[-1], title, inplace)
            return fields[0], title
        else:
            # 列名可与相应位置参数一对一映射，则直接映射
            return fields[0], columns[0]

    def build_basic_param(self, param, inplace=True):
        """ 获取与单个模型参数对应的真实列名或列名组成的元组

        param: std_table_terms 定义的单个位置参数，可能是个 str 字段名，
               也可能是 tuple 如果是tuple，tuple 中的元素都为表示字段名的 str。
        return: 返回有两个元素的元组, 前者是由原始列名 str 组成的 list,
                后者是与与 param 对应的当前真实可调用列名组成的 list，
                后者的元素由 str 或 tuple 元素组成； 如果是tuple，其最后一个
                元素为拆分或合并的分隔符，其余元素为可调用的列名。
                如果找不到对应列名，返回 None
        """
        column_names = []
        org_fields = []
        # 如果 ReStructureTable 已经与 FormatDataset 一致，
        # 则直接用原始表中与之对应列
        if param in self.fields_manual_mapping.values():
            key = self.__get_key(param)
            column_names.append(key)
            org_fields.append(key) if isinstance(key, str) else org_fields.extend(key[:-1])
            del self.fields_manual_mapping[column_names[0]]
        # 对于ReStructureTable与 FormatDataset 不一致的字段转换，
        # 综合比较后以前者为主修改后者，前者未覆盖的则依据后者处理。
        else:
            if isinstance(param, str):
                param = (param,)
            for n, clm in enumerate(param):
                for field in list(self.fields_manual_mapping.values()):
                    # param 元素能和相应原始字段一一对应
                    if type(field) == str and clm == field:
                        key = self.__get_key(field)
                        column_names.append(key)
                        org_fields.append(key) if isinstance(key, str) else org_fields.extend(key[:-1])
                        del self.fields_manual_mapping[self.__get_key(field)]
                    # param 元素是待拆分字段的组成部分
                    # 则先对原始字段进行拆分
                    elif type(field) == tuple and clm in field:
                        key = self.__get_key(field)
                        self.split_column(key[0], list(key[1]), field, inplace)
                        del self.fields_manual_mapping[self.__get_key(field)]
                        for header in field:
                            if header != clm:
                                self.fields_manual_mapping.update(
                                    {header: header})
                        column_names.append(clm)
                        org_fields.append(key[0])
                if len(column_names) < n + 1:
                    # self.fields_manual_mapping 记录了尚未被模型使用的原始
                    # 字段到标准字段的映射关系。对于需要进行多次映射处理的字段，
                    # self.fields_manual_mapping 只会记录字段的首次映射关系，
                    # 因此若 self.fields_manual_mapping 无法找到 clm，
                    # 则进一步寻找现有实际表格字段名self.df.columns,
                    # 因此对于一些泛化模型，如果泛化的字段首次映射时已经被
                    # 处理为一个定制字段名，则后续模型需要再次处理它，
                    # 就必须使用它的定制字段名，比如 scientificName 首次被处理为
                    # “学名”，后续还需要对 scientificName 进行处理，则后续模型
                    # 定义就必须使用 “学名”，否则无法在 self.df.columns 找到
                    if clm in self.df.columns:
                        column_names.append(clm)
                        org_fields.append(clm)
                    # 一些 tuple 型位置参数在实际表中并非每个字段都可以找到，
                    # 缺失字段名会用 None 占位，但不会强制用户补全。
                    # 位置参数中如行政区划就是由
                    # (country, stateProvince, city, county, ",")
                    # 进一步组合而成。其中的 country 在实际表格中确实有可能
                    # 就不存在，这种标准结构字段，有些确实会因部分字段缺失
                    # 导致信息不可用，比如学名中的属名，
                    # 有些则对数据的进一步校验影响不大。
                    # 但无论如何对于缺失的字段，这里都不会强求用户补全，
                    # 而会在具体的数值校验程序中进行处理。
                    else:
                        column_names.append(None)
        # 如果没有找到对应字段，则返回 None
        if set(column_names) == {None}:
            return None
        else:
            return org_fields, column_names

    def __get_key(self, value):
        for k, v in self.fields_manual_mapping.items():
            if v == value or v == value[:-1]:
                return k
