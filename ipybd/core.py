# -*- coding: utf-8 -*-
# Based on python 3

import json
import os
import re
from types import FunctionType, MethodType

import numpy as np
import pandas as pd
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt
from tqdm import tqdm

from warnings import filterwarnings

filterwarnings('error', category=UserWarning)

from ipybd.cleaner.cleaner import (AdminDiv, BioName, DateTime, GeoCoordinate,
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
        self.original_fields_mapping = dict.fromkeys(self.df.columns)
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

    def split_column(self, split_column, splitters, new_headers=None):
        """ 将一列分割成多列

            split_column: 要分割的列名 str
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
            self.df[split_column],
            (splitters for _ in range(self.df.shape[0]))
        )
        if new_headers:
            frame = pd.DataFrame(frame)
            frame.columns = new_headers
            self.df.drop(split_column, axis=1, inplace=True)
            self.df = pd.concat([self.df, frame], axis=1)
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

    def merge_columns(self, columns, separators, new_header=None):
        """ 按指定模式合并多列

            columns：self.df 列名 list
            separators: 合并后，各列值之间的分隔符，如果各列之间分隔符不同，可
                        按序组成 元组传递
                        如果传递的是字符 'd', 'r', 'o', 'l', 'a' 则分别表示将各
                        列合 并成字典、行列，json object 对象、json array 对象。
            new_header: 新列名,若为 None 则不删除旧列、生成新列、返回 list 结果
        """
        if separators == 'r':
            mergers = self._merge2pairs(columns, typ='rowList')
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
            self.df.drop(columns, axis=1, inplace=True)
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
            del self.original_fields_mapping[org_field]
            return []
        except KeyError:  # 字段在之前已经删除，或者被用于拆分或合并
            relax_field = []
            del_field = None
            for field in self.original_fields_mapping:
                if isinstance(field, tuple) and org_field in field:
                    del_field = field
                    relax_field = list(field[:1])
                    relax_field.remove(org_field)
                    break
            if del_field:
                del self.original_fields_mapping[del_field]
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
            手动处理获得得最新映射关系将被存储在 self.original_fields_mapping 中。

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
                self.original_fields_mapping[field] = field
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
                self.original_fields_mapping.update(
                    {fields2merge[0]: std_field})
            else:
                fields2merge.append(separators)
                self.original_fields_mapping.update(
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
            self.original_fields_mapping.update(
                {tuple(field2split): std_fields})
            # print(self.original_fields_mapping)
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
                        del self.original_fields_mapping[raw_field]
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
        mapping_fields = list(self.original_fields_mapping.values())
        for v in self.original_fields_mapping.values():
            if type(v) == tuple:
                mapping_fields.remove(v)
                mapping_fields.extend(v)
        invalid_mapping = {}
        for std_field in set(mapping_fields):
            # 重复对应或者无对应的字段，都会作为无效映射
            if mapping_fields.count(std_field) > 1 or std_field is None:
                raw_fields = []
                for rawfield, map_field in self.original_fields_mapping.items():
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
            self.original_fields_mapping[raw_field] = raw_field
        else:
            # 如果列名用的不是标准名子，逐个比较别名库，找到对应的标准名称
            std_options = []
            for k, v in FormatDataset.std_field_alias.items():
                if raw_field.upper() in v:
                    std_options.append(k)
            if len(std_options) == 1:
                self.original_fields_mapping[raw_field] = std_options[0]
            elif len(std_options) == 0:
                self.original_fields_mapping[raw_field] = None
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
                        self.original_fields_mapping[raw_field] = None
                        break
                    try:
                        self.original_fields_mapping[raw_field] = std_options[int(
                            choice2std)-1]
                        break
                    except (IndexError, ValueError):
                        print("\n所选值有误，请重新输入\n")

    def build_mapping_template(self):
        for raw_field in tqdm(self.original_fields_mapping, desc="列名映射", ascii=True):
            self.__auto2std_field(raw_field)
        invalid_mapping = self.__check_duplicate_mapping()
        self._stdfields = tuple(FormatDataset.std_field_alias.keys())
        while invalid_mapping:
            # print("\n下方式是可以映射的标准列名序列表：\n")
            # self._prt_items(2, self._stdfields)
            self.__manual2std_fields(invalid_mapping)
            invalid_mapping = self.__check_duplicate_mapping()
        # 完成的映射，存储于私人模板之中，避免用户日后再次执行映射
        # print(self.original_fields_mapping)
        json_template = {str(k): str(v)
                         for k, v in self.original_fields_mapping.items()}
        # 防止 ipybd 运行没有获得系统管理员权限，写入文件被拒而被终止
        try:
            with open(PERSONAL_TEMPLATE_PATH, "w", encoding="utf-8") as pt:
                pt.write(json.dumps(json_template, ensure_ascii=False))
        except PermissionError:
            print("\n提醒：使用系统管理员权限运行终端，iPybd 可记录转换历史！\n")
            pass

    def to_excel(self, path):
        writer = pd.ExcelWriter(path, engine='openpyxl')
                            # 下面原由的这段代码，应该是 xlsxwriter 的engine 参数，
                            # 使用 openpyxl报错具体原因待确实，先隐去处理
                            #engine_kwargs={"options":{'strngs_to_urls':False}})
        self.df.to_excel(writer, index=False)
        writer.save()

    def save_data(self, path):
        if path.endswith('.xlsx'):
            self.to_excel(path)
        elif path.endswith('.xls'):
            self.to_excel(path)
        elif path.endswith('.csv'):
            self.df.to_csv(path, index=None)
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
                if self.name_cache ==  headers:
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
                if get_action in ['simpleName', 'apiName', 'scientificName', 'plantSplitName', 'fullPlantSplitName', 'animalSplitName']:
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
    def format_scientificname(self, *headers, pattern, new_headers, concat=False):
        return pattern, headers, concat, new_headers

    @get_name
    def name_spell_check(self, *headers, concat=False):
        return 'stdName', headers, concat, ('nameSpellCheck', 'nameAuthors', 'mixFamily')

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
            'publicationYearNote', 'referenceRemarks', 'reference',
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
    def __init__(self, *args, fields_mapping=False, cut=False, fcol=False, **kwargs):
        super(RestructureTable, self).__init__(*args, **kwargs)
        # 设置补充缺失列的数值
        self.fcol = fcol
        self.fields_mapping = fields_mapping
        self.cut = cut
        self.rebuild_table()

    def rebuild_table(self):
        if not self.fields_mapping:
            for key in self.original_fields_mapping:
                self.original_fields_mapping[key] = key
        elif self.__check_old_mapping():
            self.build_mapping_template()
        # 对表格按照定义的枚举Terms进行重塑
        new_columns = self.rebuild_columns()
        # 对枚举中尚未定义的列按照人工给定的映射关系进行重塑
        self.table_mapping(self.original_fields_mapping)
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
            self.original_fields_mapping = old_mapping
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

    def rebuild_columns(self):
        """ 按照 std_table_terms 定义的 key 生成新表格的各列
        """
        new_columns = []
        for field in self.__class__.columns_model:
            try:
                params = field.value
                # print(params)
                if not isinstance(params, dict) and isinstance(params[0], (type, FunctionType, MethodType)) and isinstance(params[-1], dict):
                    if isinstance(params[1], tuple) and len(params) == 3:
                        # Enum 的 title 不准有重复，因此 _ 开头的名称
                        # 是模板用于临时定义同名字段使用，命名时需要去除 _
                        # 同时模版中以 _ 结尾的 title
                        # 具有特殊含义，命名时需特殊对待
                        field_name = field.name.strip('_')
                        columns = field_name.split('__')
                        args = self.get_args(field_name, params[1], params[-1])
                        if args:
                            # 通过定义类的__call__函数实现原始列值的处理
                            if isinstance(params[0], type):
                                # 通过 ipybd 内置类处理数据
                                new_cols = params[0](*args[0], **args[1])()
                                # 唯一性标识，可以传递多列进行重复比较
                                # 但并不会删除其他参与运算但列，只会更换第一列
                                if params[0].__name__ == 'UniqueID':
                                    args[-1][:] = [args[-1][0]]
                            else:
                                # 通过自定义的函数处理数据
                                new_cols = self.custom_func_desc(params[0](*args[0], **args[1]))
                            new_cols.columns = columns
                            self.df.drop(args[-1], axis=1, inplace=True)
                            self.df = pd.concat([self.df, new_cols], axis=1)
                            new_columns.extend(columns)
                        elif self.fcol is not False:
                            for col in columns:
                                if col not in self.df.columns:
                                    self.df[col] = self.fcol
                            new_columns.extend(columns)
                        else:
                            pass
                    else:
                        raise ValueError("model value error: {}".format(field.name))
                elif isinstance(params, (str, tuple, dict, list)):
                    field_name = field.name.lstrip('_')
                    columns = field_name.split('__')
                    arg_name = self.model_param_parser(field_name, params)
                    # print(arg_name)
                    if arg_name:
                        # print(args_name)
                        # 如果是对列进行切分，arg_name 为 None ，因此这里
                        # 只会对原表相应对字段名进行修改，args_name 为 str 类型
                        self.df.rename(
                            columns={arg_name: field_name}, inplace=True)
                        new_columns.extend(columns)
                    # 如果原表中无法找到相应的列，用指定的 self.fcol 填充新列
                    elif self.fcol is not False:
                        for col in columns:
                            if col not in self.df.columns:
                                self.df[col] = self.fcol
                        new_columns.extend(columns)
                    # 如果是列拆分，将拆分获得的列名加入新列
                    elif isinstance(params, dict):
                        new_columns.extend(columns)
                    else:
                        pass
                else:
                    raise ValueError("model value error: {}".format(field.name))
            except Exception as e:
                raise e
        # 去重复&删除已经被多次处理转换为其他列的列名
        # 并尽可能的按照模型定义的顺序返回新的列名
        new_columns = sorted(set(new_columns), key=new_columns.index)
        return [column for column in new_columns if column in self.df.columns]

    def get_args(self, title, args, kwargs):
        columns = []
        new_args = []
        for param in args:
            if isinstance(param, str) and param.startswith('$'):
                column = self.get_param(title, param[1:])
                if column:
                    new_args.append(self.df[column])
                    columns.append(column)
                else:
                    return None
            else:
                try:
                    if isinstance(param, tuple) and param[0].startswith('$'):
                        column = self.model_param_parser(title, param)
                        if column:
                            new_args.append(self.df[column])
                            columns.append(column)
                        else:
                            return None
                    elif isinstance(param, list) and param[0][0].startswith('$'):
                        column = self.model_param_parser(title, param)
                        if column:
                            new_args.append(self.df[column])
                            columns.append(column)
                        else:
                            return None
                    else:
                        new_args.append(param)
                except AttributeError:
                    new_args.append(param)
        for key, value in kwargs.items():
            if isinstance(value, str) and value.startswith('$'):
                column = self.get_param(title, value[1:])
                if column:
                    kwargs[key] = self.df[column]
                    columns.append(column)
                else:
                    return None
            else:
                try:
                    if isinstance(value, tuple) and value[0].startswith('$'):
                        column = self.model_param_parser(title, value)
                        if column:
                            kwargs[key] = self.df[column]
                            columns.append(column)
                        else:
                            return None
                    elif isinstance(value, list) and value[0][0].startswith('$'):
                        column = self.model_param_parser(title, value)
                        if column:
                            kwargs[key] = self.df[column]
                            columns.append(column)
                        else:
                            return None
                except AttributeError:
                    pass
        return new_args, kwargs, columns

    def model_param_parser(self, title, param):
        # title 由单列映射
        if isinstance(param, str):
            if param.startswith('$'):
                arg_name = self.get_param(title, param[1:])
            else:
                raise ValueError('model param of {} error'.format(title))
        # title 由多列合并
        elif isinstance(param, tuple):
            try:
                fields_name = [field[1:] if field.startswith(
                    '$') else None for field in param[:-1]]
                if all(fields_name):
                    fields_name.append(param[-1])
                    arg_name = self.get_param(title, tuple(fields_name))
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
                    param = list(param)
                    param.append(" ")
                    arg_name = self.model_param_parser(
                        new_fields, tuple(param))
                elif isinstance(param, str):
                    arg_name = self.model_param_parser(new_fields, param)
                else:
                    raise ValueError('model param of {} error'.format(title))
            else:
                raise ValueError('model param of {} error'.format(title))
            if arg_name:
                # 执行拆分前，先检查原有数据列是否已存在与要拆分出的列同名的列
                find_columns = self.build_basic_param(tuple(new_fields))
                # 如果同名列存在，再检查待拆分的列是否属于同名列
                # 如果属于，删除除此列之外的同名列再拆分此列
                # 如果不属于，先删除所有同名列再进行拆分
                if find_columns:
                    columns_name = [column for column in find_columns if column]
                    try:
                        columns_name.remove(arg_name)
                    except ValueError:
                        pass
                    self.df.drop(columns_name, axis=1, inplace=True)
                self.split_column(arg_name, separators, new_fields)
                return None
        # title 有多种可能的方式形成
        elif isinstance(param, list):
            # 如果某个参数有多种可能的情况，则发现首个符合条件的就终止
            for choice in param:
                arg_name = self.model_param_parser(title, choice)
                if arg_name:
                    return arg_name
        else:
            raise ValueError('model param of {} error'.format(title))
        return arg_name

    def get_param(self, title, param):
        """ 获取模型定义的单个参数列名

        title: 新列名，可能是 str 或 list
        param: 数据模型中定义的数据列参数表达式，可能是 str 或 tuple
               如果是 tuple ，其最后一个元素应该是分隔符
        return: None 或 str, str 是真实可调用的数据表表头名
        """
        if isinstance(param, str):
            columns = self.build_basic_param(param)
        elif isinstance(param, tuple):
            columns = self.build_basic_param(param[:-1])
        else:
            raise ValueError('model params error!')
        # 位置参数只要缺失一个，就终止处理
        if not columns:
            # print("\n{0} 没有在原表中找到对应表头\n".format(param))
            return None
        # 如果是要进行数据列的分列，则检查是否有分列的必要和条件
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
                self.merge_columns(list(clm[:-1]), clm[-1], param[n])
                columns[n] = param[n]
            elif isinstance(clm, tuple) and isinstance(param, str):
                self.merge_columns(list(clm[:-1]), clm[-1], param)
                columns[n] = param
        # 对整个参数做进一步处理
        if (len(columns) > 1
            or isinstance(param, tuple) and
                param[-1] in ['d', 'l', 'a', 'o', 'r']):
            # 相应的参数需要进一步由多列合并而成比如对于
            # (country, stateProvince, city, county, ",") 的 param
            # 返回的 columns 或许就是 ["国", "省"， ”市“, "县"]，
            # 这个时候需要对 columns 进行进一步的合并才能获得 param
            fields = []
            # 合并之前先去除真实数据表中未能找到的列，
            # 比如 (country, stateProvince, city, county)
            # 这样的单个位置参数是由多个标准列进一步合并而成，
            # 真实数据表中可能就不存在 country ,然后将相应原始字段名
            # 转换为标准字段名以统一合并值中的 key
            for col, std_col in zip(columns, param):
                if col is None:
                    continue
                else:
                    self.df.rename(columns={col: std_col}, inplace=True)
                    fields.append(std_col)
            # 最后再做合并，并将合并成的新列作为真正的位置参数返回
            self.merge_columns(fields, param[-1], title)
            return title
        else:
            # 列名可与相应位置参数一对一映射，则直接映射
            return columns[0]

    def build_basic_param(self, param):
        """ 获取与单个模型参数对应的真实列名或列名组成的元组

        param: std_table_terms 定义的单个位置参数，可能是个 str 字段名，
               也可能是 tuple 如果是tuple，tuple 中的元素都为 str，
               表示该位置参数需由多个标准字段先合并组成
               其他元素为参与合并的字段名。
        return: 返回与 param 对应的真实可调用列名组成的 list，
                list 是由 str 或 tuple 元素组成的列表；
                如果找不到对应列名，返回 None
        """
        column_names = []
        # 如果 ReStructureTable 已经与 FormatDataset 一致，
        # 则直接用原始表中与之对应列
        if param in self.original_fields_mapping.values():
            column_names.append(self.__get_key(param))
            del self.original_fields_mapping[column_names[0]]
        # 对于ReStructureTable与 FormatDataset 不一致的字段转换，
        # 综合比较后以前者为主修改后者，前者未覆盖的则依据后者处理。
        else:
            if isinstance(param, str):
                param = (param,)
            for n, clm in enumerate(param):
                for field in list(self.original_fields_mapping.values()):
                    # param 元素能和相应原始字段一一对应
                    if type(field) == str and clm == field:
                        column_names.append(self.__get_key(field))
                        del self.original_fields_mapping[self.__get_key(field)]
                    # param 元素是待拆分字段的组成部分
                    # 则先对原始字段进行拆分
                    elif type(field) == tuple and clm in field:
                        key = self.__get_key(field)
                        self.split_column(key[0], list(key[1]), field)
                        del self.original_fields_mapping[self.__get_key(field)]
                        for header in field:
                            if header != clm:
                                self.original_fields_mapping.update(
                                    {header: header})
                        column_names.append(clm)
                if len(column_names) < n + 1:
                    # self.original_fields_mapping 记录了尚未被模型使用的原始
                    # 字段到标准字段的映射关系。对于需要进行多次映射处理的字段，
                    # self.original_fields_mapping 只会记录字段的首次映射关系，
                    # 因此若 self.original_fields_mapping 无法找到 clm，
                    # 则进一步寻找现有实际表格字段名self.df.columns,
                    # 因此对于一些泛化模型，如果泛化的字段首次映射时已经被
                    # 处理为一个定制字段名，则后续模型需要再次处理它，
                    # 就必须使用它的定制字段名，比如 scientificName 首次被处理为
                    # “学名”，后续还需要对 scientificName 进行处理，则后续模型
                    # 定义就必须使用 “学名”，否则无法在 self.df.columns 找到
                    if clm in self.df.columns:
                        column_names.append(clm)
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
            return column_names

    def __get_key(self, value):
        for k, v in self.original_fields_mapping.items():
            if v == value or v == value[:-1]:
                return k
