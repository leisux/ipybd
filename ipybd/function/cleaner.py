import json
import os
import re
from datetime import date
from types import FunctionType, MethodType
from typing import Union
import warnings

import arrow
import pandas as pd
from tqdm import tqdm


PARENT_PATH = os.path.dirname(os.path.dirname(__file__))
STD_OPTIONS_ALIAS_PATH = os.path.join(
    PARENT_PATH, 'lib', 'std_options_alias.json')
ADMIN_DIV_LIB_PATH = os.path.join(PARENT_PATH, 'lib', 'chinese_admin_div.json')


def ifunc(obj):
    if isinstance(obj, (type, FunctionType)):
        def handler(*args, **kwargs):
            param = args[0]
            if isinstance(param, str) and param.startswith('$'):
                return obj, args, kwargs
            else:
                try:
                    if isinstance(param, tuple) and param[0].startswith('$'):
                        return obj, args, kwargs
                    elif isinstance(param, list) and param[0][0].startswith('$'):
                        return obj, args, kwargs
                    else:
                        # 如果数据对象不是通过$修饰，则返回正常调用
                        return obj(*args, **kwargs)
                except (AttributeError, TypeError, IndexError):
                    return obj(*args, **kwargs)
        return handler
    elif isinstance(obj, MethodType):
        pass
    else:
        raise ValueError('model value error: {}'.format(obj))


@ifunc
class DateTime:
    def __init__(self, date_time: Union[list, pd.Series, tuple], style="num", timezone='+08:00'):
        self.datetime = date_time
        self.zone = timezone
        # 兼容 RestructureTable，供 __call__ 调用
        self.style = style

    def format_datetime(self, style):
        result = []
        for n, date_time in enumerate(tqdm(self.datetime, desc="日期处理", ascii=True)):
            # 兼容 Kingdonia 无日期写法
            # 遇到无日期的写法,直接将原始数据置为空
            if date_time in ["0000-01-01 00:00:02", "9999-01-01 00:00:00", "1970-01-01 00:00:00", "0000-01-01 00:00:00"]:
                self.datetime[n] = None
                result.append(None)
                continue
            # 先尝试作为 datetime 处理
            datetime = self.datetime_valid(date_time)
            if datetime:
                if style == "datetime":
                    result.append(datetime.format("YYYY-MM-DD HH:mm:ss"))
                elif style == "utc":
                    result.append(
                        datetime.format(
                            "YYYY-MM-DDTHH:mm:ss" +
                            self.zone))
                else:
                    result.append(
                        self.__format_date_style(
                            datetime.year,
                            datetime.month,
                            datetime.day,
                            style
                        )
                    )
            else:
                # 然后尝试作为 date 进行处理
                try:
                    date_degree, date_elements = self.get_date_elements(
                        date_time)
                except TypeError:
                    result.append(None)
                    continue
                # 获取单个日期的年月日值，如果单个日期的年月日值有不同的拼写法，则全部转换成整型
                date_elements = self.mapping_date_element(
                    date_degree, date_elements)
                if date_elements:
                    # 判断年月日的数值是否符合规范&判断各数值是 年 月 日 中的哪一个
                    try:
                        year, month, day = self.format_date_elements(
                            date_degree,
                            date_elements)
                        result.append(
                            self.__format_date_style(
                                year, month, day, style))
                    except TypeError:
                        result.append(None)
                        continue
                    except ValueError:
                        print("\n\n style 参数指定不正确\n")
                        break
                else:
                    result.append(None)
                    continue

        return result

    def datetime_valid(self, datetime):
        try:
            date_time = arrow.get(datetime)
            if date_time.datetime.hour:
                return date_time
            else:
                return None
        except BaseException:
            return None

    def to_utc(self, datetime, tz, to_tz):
        date_time = arrow.get(datetime).replace(tzinfo=tz).to(to_tz)
        return date_time.format("YYYY-MM-DDTHH:MM:SS"+to_tz)

    def __format_date_style(self, year, month, day, style='num'):
        if not month:
            if style == "num":
                return "".join([str(year), "00", "00"])
            elif style == "date":
                return "-".join([str(year), "01", "01"])
            elif style == "datetime":
                return "-".join([str(year), "01", "01 00:00:02"])
            elif style == "utc":
                return "-".join([str(year), "01", "01T00:00:02"]) + self.zone
            else:
                raise ValueError
        elif not day:
            if style == "num":
                if month < 10:
                    return "".join([str(year), "0", str(month), "00"])
                else:
                    return "".join([str(year), str(month), "00"])
            elif style == "date":
                return "-".join([str(year), str(month), "01"])
            elif style == "datetime":
                return "-".join([str(year), str(month), "01 00:00:01"])
            elif style == "utc":
                month = str(month)
                if len(month) == 1:
                    month = '0' + month
                return "-".join([str(year), month, "01T00:00:01"]) + self.zone
            else:
                raise ValueError
        else:
            if style == "num":
                if month < 10 and day < 10:
                    return "".join([str(year), "0", str(month), "0", str(day)])
                elif month < 10 and day > 9:
                    return "".join([str(year), "0", str(month), str(day)])
                elif month > 9 and day < 10:
                    return "".join([str(year), str(month), "0", str(day)])
                else:
                    return "".join([str(year), str(month), str(day)])
            elif style == "date":
                return "-".join([str(year), str(month), str(day)])
            elif style == "datetime":
                return "-".join([str(year), str(month),
                                 str(day)]) + " 00:00:00"
            elif style == "utc":
                month = str(month)
                if len(month) == 1:
                    month = '0' + month
                day = str(day)
                if len(day) == 1:
                    day = '0' + day
                return "-".join([str(year), month, day]
                                ) + "T00:00:00" + self.zone
            else:
                raise ValueError

    def format_date_elements(self, date_degree, date_elements):
        """ 判断日期中的每个元素是否符合逻辑
        """
        year, month, day = [None] * 3
        today = date.today()
        for k in range(date_degree):
            element = date_elements[k]
            # 先尝试获得合格的年份
            if element > today.year:
                return None
            elif element > 1599:
                if not year:
                    year = element
                    continue
                else:
                    return None
            elif element > 99:
                return None
            elif element > 31:
                if not year:
                    year = element + 1900
                    continue
                else:
                    return None
            elif element == 0:
                continue
            # 有三个数， 默认作为年月日样式的日期处理
            if date_degree == 3:
                if k == 1:
                    # 写在中间的数字，默认视为月份
                    if 0 < element < 13:
                        month = element
                    else:
                        return None
                elif year:
                    day = element
                # 如果日和年的数值，都小于31，将无法判断日和年的具体数值
                elif date_elements[2] > 31:
                    day = element
                else:
                    return None
            # 有两个数，默认作为没有 day 的日期处理
            elif date_degree == 2:
                if element > 12:
                    if year:
                        return None
                    elif month:
                        year = 1900 + element
                    elif date_elements[1] < 13:
                        year = 1900 + element
                    else:
                        return None
                elif element > 0:
                    if year:
                        month = element
                    elif date_elements[1] > 12:
                        month = element
                    else:
                        return None
                else:
                    return None
            # 只有一个数，若不能作为年份处理，则返回 None
            elif date_degree == 1:
                return None
            else:
                return None
        # 检查重新合成的日期，是否符合逻辑
        try:
            if date(year, month, day) > today:
                return None
        except ValueError:
            return None
        except TypeError:
            pass

        return year, month, day

    def mapping_date_element(self, date_degree, date_elements: list):
        alias_map = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "APRI": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "SEPT": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "Apri": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Sept": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12}
        for i in range(date_degree):
            try:
                date_elements[i] = int(date_elements[i])
            except ValueError:
                # print(date_elements)
                if date_elements[i] in alias_map:
                    date_elements[i] = alias_map[date_elements[i]]
                else:
                    return None
        return date_elements

    def get_date_elements(self, date_txt):
        dmy_pattern = re.compile(r"[A-Za-z]+|[0-9]+")
        try:
            date_elements = dmy_pattern.findall(date_txt)
            if date_elements == []:
                return None
        except (TypeError, ValueError):
            return None
        date_degree = len(date_elements)
        if date_degree == 6:
            date_degree = 3
            date_elements = date_elements[0:3]
        elif date_degree == 1:
            temp = date_elements[0]
            if len(temp) == 4:
                pass
            elif len(temp) == 6:
                date_degree = 2
                date_elements[0] = temp[0:4]
                date_elements.append(temp[4:6])
            elif len(temp) == 8:
                date_degree = 3
                date_elements[0] = temp[0:4]
                date_elements.append(temp[4:6])
                date_elements.append(temp[6:8])
            else:
                return None
        return date_degree, date_elements

    def __call__(self, mark=True):
        std_datetime = self.format_datetime(self.style)
        if mark:
            for i in range(len(self.datetime)):
                if not std_datetime[i]:
                    if not pd.isnull(self.datetime[i]):
                        try:
                            std_datetime[i] = "".join(["!", self.datetime[i]])
                        except TypeError:
                            std_datetime[i] = "".join(
                                ["!", str(self.datetime[i])])
        return pd.DataFrame({"dateTime": std_datetime})


@ifunc
class HumanName:
    def __init__(self, names: Union[list, pd.Series, tuple], separator='，'):
        self.names = names
        self.separator = separator

    def format_names(self):
        """
        返回以英文逗号分隔的人名字符串，可中英文人名混排“徐洲锋,A. Henry,徐衡”，并以
        “!“ 标识可能错误写法的字符串，注意尚无法处理“徐洲锋 洪丽林 徐衡” 这样以空格切
        分的中文人名字符串
        """
        names_mapping = dict.fromkeys(self.names)
        pattern = re.compile(
            r'[\u4e00-\u9fa5\s]*[\u4e00-\u9fa5][\|\d]*|[A-Za-z\(\[][A-Za-z\u00C0-\u00FF\'\.\s\-\]\(\)]*[A-Za-z\u00C0-\u00FF\'\.\]\)][\|\d]*')
        #r'[\u4e00-\u9fa5\s]*[\u4e00-\u9fa5][\|\d]*|[A-Za-z\(\[][A-Za-z\u00C0-\u00FF\'\s\-\]\(\)]*[,]?[A-Za-z\u00C0-\u00FF\'\.\s\-\]\(\)]*[A-Za-z\u00C0-\u00FF\'\.\]\)][\|\d]*')
        for rec_names in tqdm(names_mapping, desc="人名处理", ascii=True):
            try:
                # 切分人名
                names = [name.strip()
                         for name in pattern.findall(rec_names)]
                # print(names)
                # 对一条记录里的每个人名的合理性进行判断
                for i, name in enumerate(names):
                    # 先判断人名是否来自 Biotracks 网页端导出的带 id 的人名
                    if re.search(r"[a-z\u4e00-\u9fa5]\|\d", name):
                        pass
                    # 再判断是否是普通的人名记录
                    elif not re.search(r"[\|\d]", name):
                        pass
                    else:
                        raise ValueError
                    if re.search(u"[\u4e00-\u9fa5]", name):
                        if len(name) <= 2:
                            # 如果人名队列是空值指使词
                            # 触发 NameError 跳出循环以使其最后被重设为 None
                            if name in ["无", "缺失", "佚名"] and len(names) == 1:
                                raise NameError
                            # 如果是中文人名, 首个人名字符长度不能小于 2
                            elif len(name) == 1 and i == 0:
                                raise ValueError
                            else:
                                names[i] = name
                        else:
                            # 对大于 2 个字符的中文人名，替换空格
                            # 主要解决双字名中，中间有空格的情况
                            names[i] = name.replace(" ", "")
                    else:
                        names[i] = self.format_westname(name)
                names_mapping[rec_names] = self.separator.join(names)
            except NameError:
                continue
            except BaseException:
                if pd.isnull(rec_names):
                    continue
                else:
                    names_mapping[rec_names] = "!" + str(rec_names)

        return [names_mapping[txt] for txt in self.names]

    def format_westname(self, name):
        # 判断名字长度
        if len(name) < 2:
            raise ValueError
        # 纠正空格数量
        while True:
            if "  " in name:
                name = name.replace("  ", " ")
            else:
                break
        # 纠正”.“后无空格
        en_name = [
            e + "."
            if len(e) > 0 else e
            for e in re.split(r"\.\s*", name)]
        # 去除非简写姓或名后的”.“
        if en_name[-1] == "":
            del en_name[-1]
        else:
            en_name[-1] = en_name[-1][:-1]
        #['de', 'das', 'dos', 'des', 'la', 'da', 'do', 'del', 'di', 'della', 'bai', 'la', 'zu', 'aus', 'dem', 'von', 'der', 'von', 'dem', 'vom', 'van']:
        return " ".join(en_name)

    def __call__(self):
        return pd.DataFrame(pd.Series(self.format_names()))


@ifunc
class AdminDiv:
    """中国省市县行政区匹配

    本程序只会处理中国的行政区,最小行政区划到县级返回的字段值形式为
    “中国,北京,北京市,朝阳区”， 程序不能保证百分百匹配正确；
    对于只有“白云区”、“东区”等孤立的容易重名的地点描述，程序最终很可能给予错误
    的匹配，需要人工核查，匹配结果前有“!”标志；
    对于“碧江”、"路南县"（云南省）这种孤立的现已撤销的地点描述但在其他省市区还
    有同名或者其他地区名称被包括其中的行政区名称
    （中国,贵州省,铜仁市,碧江区，中国,湖南省,益阳市,南县）；程序一定会给出错误
    匹配且目前并不会给出任何提示；对于“四川省南川”、“云南碧江”这种曾经的行政区
    归属，程序会匹配字数多的行政区且这种状况下不会给出提示，如前者会匹配
    “中国,四川省”，对于字数一致的，则匹配短的行政区，但会标识，如后者可能匹配
    “!中国,云南省”
    """

    def __init__(self, address: Union[list, pd.Series, tuple]):
        self.org_address = address
        self.region_mapping = dict.fromkeys(self.org_address)

    def format_chinese_admindiv(self):
        new_regions = []
        with open(ADMIN_DIV_LIB_PATH, 'r', encoding='utf-8') as ad:
            std_regions = json.load(ad)
        # country_split = re.compile(r"([\s\S]*?)::([\s\S]*)")
        for raw_region in tqdm(self.region_mapping, desc="行政区划", ascii=True):
            if pd.isnull(raw_region):
                continue
            self._build_mapping(raw_region, std_regions)
        new_regions = [
            (
                self.region_mapping[region].split("::")
                if self.region_mapping[region] else self.region_mapping[region]
            ) for region in self.org_address
        ]
        # 未达县级的标准行政区，用None 补齐，注意浅拷贝陷阱
        [
            (
                region.extend([None]*(4-len(region)))
                if region and len(region) < 4 else region
            ) for region in new_regions
        ]

        self.country = [(region[0] if region else None)
                        for region in new_regions]
        self.province = [(region[1] if region else None)
                         for region in new_regions]
        self.city = [(region[2] if region else None) for region in new_regions]
        self.county = [(region[3] if region else None)
                       for region in new_regions]

    def _build_mapping(self, raw_region, std_regions):
        score = (0, 0)  # 分别记录匹配的字数和匹配项的长度
        region = raw_region.rstrip(":")
        region_index = len(region) - 1
        for stdregion in std_regions:
            len_stdregion = len(stdregion)
            each_score = 0  # 记录累计匹配的字数
            i = 0  # 记录 region 参与匹配的起始字符位置
            j = 0  # 记录 stdregion 参与匹配的起始字符位置
            while i < region_index and j < len_stdregion-1:  # 单字无法匹配
                k = 2  # 用于初始化、递增可匹配的字符长度
                n = stdregion[j:].find("::"+region[i:i+k])
                m = 0  # 记录最终匹配的字符数
                if n != -1:
                    # 白云城矿区可能会错误的匹配“中国,内蒙古自治区,白云鄂博矿区”
                    if region[-2] in stdregion:
                        while n != -1 and k <= region_index - i + 1:
                            k += 1
                            m = n
                            n = stdregion[j:].find(region[i:i+k])
                        i += k-1
                        j += m+k-1
                        each_score += k-1
                    else:
                        each_score = 2
                        break
                else:
                    i += 1
            if each_score < 2:
                continue
            elif each_score == score[0]:
                if self.region_mapping[raw_region] in stdregion:
                    pass
                # 优先匹配短的行政区，避免“河北”匹配“中国,天津,天津市,河北区“
                elif len_stdregion < score[1]:
                    score = each_score, len_stdregion
                    self.region_mapping[raw_region] = "!"+stdregion
            elif each_score > score[0]:
                score = each_score, len_stdregion
                self.region_mapping[raw_region] = stdregion
        if score == (0, 0):
            if raw_region == "中国":
                self.region_mapping[raw_region] = "中国"
            # 如果没有匹配到，又是中国的行政区，英文!标识
            elif "中国" in raw_region:
                self.region_mapping[raw_region] = "!" + raw_region
            else:
                self.region_mapping[raw_region] = raw_region
        # print(raw_region, self.region_mapping[raw_region])

    def __call__(self):
        self.format_chinese_admindiv()
        return pd.DataFrame({
                            'country': self.country,
                            'province': self.province,
                            'city': self.city,
                            'county': self.county
                            })


@ifunc
class Number:
    def __init__(self, min_column: Union[list, pd.Series, tuple], max_column: Union[list, pd.Series, tuple] = None,
                 typ=float, min_num=-423, max_num=8848):
        """
            min_column: 可迭代对象，数值区间中的小数值数据列
            max_column: 可迭代对象, 数据区间中的大数值数据列
            typ: 数值的类型，支持 float 和 int
            min_num: 数值区间的低值
            max_num: 数值区间的高值
        """
        self.min_column = min_column
        self.max_column = max_column
        self.typ = typ
        self.min_num = min_num
        self.max_num = max_num

    def format_number(self, mark=False):
        """
        return: 如果出现 keyerro，返回列表参数错误, 否则返回处理好的table
        """
        pattern = re.compile(r"^[+-]?\d+\.?\d*(?<=\d)|\d+\.?\d*(?<=\d)")
        try:
            column1 = [
                pattern.findall(str(value)) if not pd.isnull(value) else []
                for value in self.min_column
            ]
            if self.max_column is None:
                new_column = []
                for i, v in enumerate(tqdm(column1, desc="数值处理", ascii=True)):
                    if (len(v) == 1
                            and self.min_num <= float(v[0]) <= self.max_num):
                        new_column.append([self.typ(float(v[0]))])
                    elif pd.isnull(self.min_column[i]):
                        new_column.append([None])
                    # 如果拆分出多个值，作为错误值标记
                    elif mark:
                        new_column.append(["!" + str(self.min_column[i])])
                    else:
                        new_column.append([None])
                return new_column
            else:
                column2 = [
                    pattern.findall(str(value)) if not pd.isnull(value) else []
                    for value in self.max_column
                ]
                return self._min_max(column1, column2, self.typ, mark)
        except KeyError:
            raise ValueError("列表参数有误\n")

    def _min_max(self, column1, column2, typ, mark=False):
        """ 修复数值区间中相应的大小数值

            column1: 小数值 list, 每个元素必须也为 list
            column2: 大数值 list，每个元素必须也为 list
            typ: 数值的类型，如 int, flora
        """
        for p, q in zip(
            tqdm(column1, desc="数值区间", ascii=True),
            tqdm(column2, desc="数值区间", ascii=True)
        ):
            # 只要 p + q 最终能获得两个数即可
            # 因此不需要 p 或 q 一定是单个数
            # 这对于一些使用非一致分隔符表达的数值区间比较友好
            # 这保证了即便有些数值区间的值无法被拆分表达式准确的拆分
            # 但只要能够伴随大值列和小值列值实例化Number类
            # 最终仍然可以准确获得小值列和大值列
            merge_value = p + q
            if (len(merge_value) == 2
                and self.min_num <= float(merge_value[0]) <= self.max_num
                    and self.min_num <= float(merge_value[1]) <= self.max_num):
                if float(merge_value[0]) <= float(merge_value[1]):
                    p.insert(0, merge_value[0])
                    q.insert(0, merge_value[1])
                # 系统默认补0造成的高值低于低值，处理为同值
                elif float(merge_value[1]) == 0:
                    p.insert(0, merge_value[0])
                    q.insert(0, merge_value[0])
                else:
                    p.insert(0, merge_value[1])
                    q.insert(0, merge_value[0])
            elif (len(merge_value) == 1
                  and self.min_num <= float(merge_value[0]) <= self.max_num):
                # 若两个值中只有一个值含数字，程序会自动清非数字点的值
                # 并使用另外一个数字填充两个值
                p.insert(0, merge_value[0])
                q.insert(0, merge_value[0])
            else:
                p.insert(0, None)
                q.insert(0, None)
        if mark:
            min_column = [
                typ(float(column1[i][0]))
                if column1[i][0] else "".join(
                    ["!", str(self.min_column[i])])
                if not pd.isnull(self.min_column[i]) else None
                for i in range(len(column1))]
            max_column = [
                typ(float(column2[i][0]))
                if column2[i][0] else "".join(
                    ["!", str(self.min_column[i])])
                if not pd.isnull(self.max_column[i]) else None
                for i in range(len(column2))]
        else:
            min_column = [
                typ(float(column1[i][0]))
                if column1[i][0] else None
                if not pd.isnull(self.min_column[i]) else None
                for i in range(len(column1))
            ]
            max_column = [
                typ(float(column2[i][0]))
                if column2[i][0] else None
                if not pd.isnull(self.max_column[i]) else None
                for i in range(len(column2))
            ]
        return [[i, j] for i, j in zip(min_column, max_column)]

    def __call__(self, mark=True):
        new_column = self.format_number(mark)
        if self.typ is int:
            # 解决含 None 数据列，pandas 会将int数据列转换为float的问题
            # 这里要求 pandas 版本支持
            typ = 'Int64'
        else:
            typ = self.typ
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                return pd.DataFrame(new_column, dtype=typ)
        except (ValueError, TypeError):
            # 解决数据列中混入某些字符串无法转 Int64 等数据类型的问题。
            return pd.DataFrame(new_column)


@ifunc
class GeoCoordinate:
    def __init__(self, coordinates: Union[list, pd.Series, tuple]):
        self.coordinates = coordinates

    def format_coordinates(self):
        new_lng = [None]*len(self.coordinates)
        new_lat = [None]*len(self.coordinates)
        gps_p_1 = re.compile(
            r"[NESWnesw][^A-Za-z,，；;]*[0-9][^A-Za-z,，；;]+")  # NSWE 前置经纬度
        gps_p_2 = re.compile(r"[0-9][^A-Za-z,，；;]+[NESWnesw]")  # NSWE 后置经纬度
        gps_p_3 = re.compile(r"[+-]?\d+[\.\d]*")  # 十进制经纬度
        gps_p_num = re.compile(r"[\d\.]+")
        gps_p_NSEW = re.compile(r"[NESWnesw]")
        for i in tqdm(range(len(self.coordinates)), desc="经纬度", ascii=True):
            try:
                gps_elements = gps_p_1.findall(
                    self.coordinates[i])  # 提取坐标，并将其列表化，正常情况下将有两个元素组成列表
                if len(gps_elements) != 2:  # 通过小数点个数和列表长度初步判断是否是合格的坐标
                    gps_elements = gps_p_2.findall(self.coordinates[i])
                    if len(gps_elements) != 2:
                        gps_elements = gps_p_3.findall(self.coordinates[i])
                        # print(gps_elements)
                        if len(gps_elements) == 2 and abs(
                                float(gps_elements[0])) <= 90 and abs(
                                float(gps_elements[1])) <= 180:
                            new_lng[i] = round(float(gps_elements[1]), 6)
                            new_lat[i] = round(float(gps_elements[0]), 6)
                            continue
                        else:
                            # print(gps_elements ,type(gps_elements[1]))
                            # 如果值有错误，则保留原值，如果是数值型值，考虑到已无法恢复，则触发错误不做任何保留
                            new_lat[i] = "!" + gps_elements[0]
                            new_lng[i] = "!" + gps_elements[1]
                            continue
                direct_fir = gps_p_NSEW.findall(
                    gps_elements[0])[0]  # 单个单元格内，坐标第一个值的方向指示
                direct_sec = gps_p_NSEW.findall(
                    gps_elements[1])[0]  # 单个单元格内，坐标第二个值的方向指示
                gps_fir_num = gps_p_num.findall(
                    gps_elements[0])  # 获得由坐标中的度分秒值组成的数列
                gps_sec_num = gps_p_num.findall(gps_elements[1])
                # print(i, " ", direct_fir, direct_sec, gps_fir_num, gps_sec_num)
                if direct_fir in "NSns" and direct_sec in "EWew" and float(
                        gps_fir_num[0]) <= 90 and float(
                        gps_sec_num[0]) <= 180:  # 判断哪一个数值是纬度数值，哪一个数值是经度数值
                    direct_fir_seq = 1
                elif direct_fir in "EWew" and direct_sec in "NSns" and float(gps_sec_num[0]) <= 90 and float(gps_fir_num[0]) <= 180:
                    direct_fir_seq = 0
                else:
                    new_lng[i] = "!" + gps_elements[1]
                    new_lat[i] = "!" + gps_elements[0]
                    continue
                direct = {
                    "N": 1,
                    "S": -1,
                    "E": 1,
                    "W": -1,
                    "n": 1,
                    "s": -1,
                    "e": 1,
                    "w": -1}
                if len(gps_fir_num) == 3 and len(gps_sec_num) == 3:
                    if int(gps_fir_num[1]) >= 60:
                        new_lng[i] = "!" + gps_elements[1]
                        new_lat[i] = "!" + gps_elements[0]
                        continue
                    if float(gps_fir_num[2]) >= 60 or float(
                            gps_sec_num[2]) >= 60:  # 度分表示法写成了度分秒表示法
                        if direct_fir_seq == 1:
                            new_lat[i] = direct[direct_fir] * round(
                                int(gps_fir_num[0]) +
                                float(gps_fir_num[1] + "." +
                                      gps_fir_num[2]) / 60,
                                6)
                            new_lng[i] = direct[direct_sec] * round(
                                int(gps_sec_num[0]) +
                                float(gps_sec_num[1] + "." +
                                      gps_sec_num[2]) / 60,
                                6)
                        else:
                            new_lng[i] = direct[direct_fir] * round(
                                int(gps_fir_num[0]) +
                                float(gps_fir_num[1] + "." +
                                      gps_fir_num[2]) / 60,
                                6)
                            new_lat[i] = direct[direct_sec] * round(
                                int(gps_sec_num[0]) +
                                float(gps_sec_num[1] + "." +
                                      gps_sec_num[2]) / 60,
                                6)
                    else:  # 度分秒表示法
                        if direct_fir_seq == 1:
                            new_lat[i] = direct[direct_fir] * round(
                                int(gps_fir_num[0]) + int(gps_fir_num[1]) / 60 +
                                float(gps_fir_num[2]) / 3600, 6)
                            new_lng[i] = direct[direct_sec] * round(
                                int(gps_sec_num[0]) + int(gps_sec_num[1]) / 60 +
                                float(gps_sec_num[2]) / 3600, 6)
                        else:
                            new_lng[i] = direct[direct_fir] * round(
                                int(gps_fir_num[0]) + int(gps_fir_num[1]) / 60 +
                                float(gps_fir_num[2]) / 3600, 6)
                            new_lat[i] = direct[direct_sec] * round(
                                int(gps_sec_num[0]) + int(gps_sec_num[1]) / 60 +
                                float(gps_sec_num[2]) / 3600, 6)
                elif len(gps_fir_num) == 2 and len(gps_sec_num) == 2:  # 度分表示法
                    if float(gps_fir_num[1]) >= 60:
                        new_lng[i] = "!" + gps_elements[1]
                        new_lat[i] = "!" + gps_elements[0]
                        continue
                    if direct_fir_seq == 1:
                        new_lat[i] = direct[direct_fir] * round(
                            int(gps_fir_num[0]) + float(gps_fir_num[1]) / 60, 6)
                        new_lng[i] = direct[direct_sec] * round(
                            int(gps_sec_num[0]) + float(gps_sec_num[1]) / 60, 6)
                    else:
                        new_lng[i] = direct[direct_fir] * round(
                            int(gps_fir_num[0]) + float(gps_fir_num[1]) / 60, 6)
                        new_lat[i] = direct[direct_sec] * round(
                            int(gps_sec_num[0]) + float(gps_sec_num[1]) / 60, 6)
                elif len(gps_fir_num) == 1 and len(gps_sec_num) == 1:  # 度表示法
                    if direct_fir_seq == 1:
                        new_lat[i] = direct[direct_fir] * \
                            round(float(gps_fir_num[0]), 6)
                        new_lng[i] = direct[direct_sec] * \
                            round(float(gps_sec_num[0]), 6)
                    else:
                        new_lng[i] = direct[direct_fir] * \
                            round(float(gps_fir_num[0]), 6)
                        new_lat[i] = direct[direct_sec] * \
                            round(float(gps_sec_num[0]), 6)
                # 处理度分/度分秒表示法中，纬度、经度最后一项正好为0被省略导致经纬度不等长的问题
                elif len(gps_fir_num) < 4 and len(gps_sec_num) < 4:
                    if False not in [
                        f()
                        for f
                        in
                        [(lambda i=i: float(i) < 60)
                         for i in gps_fir_num[1:] + gps_sec_num[1:]]]:
                        if (lambda n=min(gps_fir_num, gps_sec_num)
                                [-1]: "." not in n)():
                            if direct_fir_seq == 1:
                                new_lat[i] = direct[direct_fir]*round(
                                    sum([float(gps_fir_num[i])/pow(60, i) for i in range(len(gps_fir_num))]), 6)
                                new_lng[i] = direct[direct_sec]*round(
                                    sum([float(gps_sec_num[i])/pow(60, i) for i in range(len(gps_sec_num))]), 6)
                            else:
                                new_lng[i] = direct[direct_fir]*round(
                                    sum([float(gps_fir_num[i])/pow(60, i) for i in range(len(gps_fir_num))]), 6)
                                new_lat[i] = direct[direct_sec]*round(
                                    sum([float(gps_sec_num[i])/pow(60, i) for i in range(len(gps_sec_num))]), 6)
                        else:
                            new_lng[i] = "!" + gps_elements[1]
                            new_lat[i] = "!" + gps_elements[0]
                    else:
                        new_lng[i] = "!" + gps_elements[1]
                        new_lat[i] = "!" + gps_elements[0]
                else:
                    new_lng[i] = "!" + gps_elements[1]
                    new_lat[i] = "!" + gps_elements[0]

            except TypeError:
                continue
            except IndexError:
                continue
            except ValueError:
                new_lng[i] = "!" + str(gps_elements[1])
                new_lat[i] = "!" + str(gps_elements[0])
                continue
        return new_lat, new_lng

    def __call__(self):
        self.lat, self.lng = self.format_coordinates()
        return pd.DataFrame({
            "decimalLatitude": self.lat,
            "decimalLongitude": self.lng
        })


@ifunc
class RadioInput:
    def __init__(self, column, lib=None):
        self.column = column
        if isinstance(lib, dict):
            self.rewritelib = 0
            self.std2alias = lib
        elif isinstance(lib, str):
            with open(STD_OPTIONS_ALIAS_PATH, "r", encoding="utf-8") as o:
                self.lib = json.load(o)
                self.rewritelib = 1
                self.std2alias = self.lib[lib]
        else:
            raise ValueError('unvalid lib!')

    def format_option(self, std2alias):
        options_mapping = {k:k for k in self.column} 
        std_titles = sorted(list(std2alias.keys()))
        mana2std = []
        for option in tqdm(options_mapping, desc="选值处理", ascii=True):
            if option in std_titles:
                options_mapping[option] = option
            else:
                for k, v in std2alias.items():
                    if option in v:
                        options_mapping[option] = k
                        break
                if option == options_mapping[option]:
                    if pd.isnull(option):
                        continue
                    else:
                        mana2std.append(option)
        # 手动指定无法自动匹配的可选值
        if mana2std:
            if int(
                input(
                    "\n选值中有 {} 个值需要逐个手动指定，手动指定请输入 1 ，全部忽略请输入 0：\n".format(
                        len(mana2std)))):
                for option in mana2std:
                    print(
                        "".join(
                            ["\n\n", str(option),
                             "=>请将该值对应至以下可选值中的某一个:\n"]))
                    for n, m in enumerate(std_titles):
                        strings = str(n+1) + ". " + m
                        if (n+1) % 3 > 0:
                            print(strings.ljust(25), end="\t")
                        else:
                            print(strings.ljust(25), end="\n\n")
                    while True:
                        n = input("\n\n请输入对应的阿拉伯数字，无法对应请输入 0 :\n\n")
                        if n == '0':
                            options_mapping[option] = "!" + str(option)
                            break
                        else:
                            try:
                                std2alias[std_titles[int(
                                    n)-1]].append(option)
                                options_mapping[option] = std_titles[int(n)-1]
                                break
                            except BaseException:
                                print("\n输入的字符有误...\n")
                if self.rewritelib:
                    with open(STD_OPTIONS_ALIAS_PATH, "w", encoding="utf-8") as f:
                        f.write(json.dumps(self.lib, ensure_ascii=False))

        return [options_mapping[w] for w in self.column]

    def __call__(self):
        return pd.DataFrame(pd.Series(self.format_option(self.std2alias)))


@ifunc
class UniqueID:
    def __init__(self, *columns: pd.Series):
        # columns 可以包含多个数据列联合判重
        self.df = pd.concat(columns, axis=1)

    def mark_duplicate(self):
        # 重复的行，将以 ! 标记
        self.duplicated = self.df.duplicated(keep=False)
        marks = [
            "".join(["!", str(m)]) if d and not pd.isnull(m) else m
            for m, d in zip(self.df.iloc[:, 0], self.duplicated)
        ]
        return marks

    def __call__(self):
        self.df[self.df.columns[0]] = self.mark_duplicate()
        return self.df.iloc[:, [0]]


@ifunc
class FillNa:
    def __init__(self, *columns: pd.Series, value=None, method=None, axis=None, limit=None, downcast=None):
        self.df = pd.concat(columns, axis=1)
        self.value = value
        self.method = method
        self.axis = axis
        self.limit = limit
        self.downcast = downcast

    def __call__(self):
        return self.df.fillna(value=self.value, method=self.method, axis=self.axis, inplace=False, limit=self.limit, downcast=self.downcast)


@ifunc
class Url:
    def __init__(self, column: Union[list, pd.Series, tuple]):
        self.urls = column
        self.pattern = re.compile(
            r"http://[^,\|\"\']+|https://[^,\|\"\']+|ftp://[^,\|\"\']+")

    def split_url_to_list(self):
        return map(lambda url: self.pattern.findall(url)
                   if url and not pd.isnull(url) else None, self.urls)

    def __call__(self):
        return pd.DataFrame(pd.Series(self.split_url_to_list()))


if __name__ == "__main__":
    pass
