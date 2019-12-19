# -*- coding: utf-8 -*-
# Based on python 3

from os import walk as os_walk
from os.path import splitext as os_path_splitext
from os.path import join as os_path_join
from os.path import dirname as os_path_dirname
from os import popen as os_popen
from os import rename as os_rename
from sys import argv as sys_argv
from re import compile as re_compile
from re import split as re_split
from shutil import move as shutil_move
from collections import Counter
from datetime import date
from datetime import timedelta
from time import strptime as time_strptime
from pandas import read_excel
from pandas import Series
from pandas import isnull
from pandas import concat
from numpy import NaN
from PIL.Image import open as Image_open
from PIL.Image import ANTIALIAS
from json import load as json_load
from json import loads as json_loads
from json import dumps as json_dumps

class BlockError(Exception):
    pass


def extract_file(excel, dir, dst):
    while True:
        title = input("请输入提取图片所依据的字段名：\n")
        try:
            table = read_excel(excel, converters={title: str})
            barcode = list(table[title])
            break
        except KeyError:
            print("\n输入的列名不在当前 Excel 表格之中，请重新输入")
            continue
    rdf = os_walk(dir)
    file_dict = {}
    for root, dirs, files in rdf:
        for file in files:
            name_ext = os_path_splitext(file)
            if name_ext[1].lower() in (".jpg", ".jpeg", ".tiff", ".tif", ".png"):
                img_path = os_path_join(root, file)
                file_dict[name_ext[0]] = img_path
            else:
                continue
    no_img_barcode = []
    for b in barcode:
        try:
            shutil_move(file_dict[b], dst)
        except KeyError:
            no_img_barcode.append(b)
            continue

    print("以下条形码未找到照片：\n\n")
    for n in no_img_barcode:
        print(n, end=", ")


def rename(dir):
    bar_error = []
    repeat_error = []
    cnt_ident = 0
    cnt_error = 0
    cnt_repeat = 0
    pdf = os_walk(dir)

    def ident(raw_img_path):
        nonlocal cnt_ident
        nonlocal cnt_error
        nonlocal cnt_repeat
        tmp_img = os_path_dirname(sys_argv[0]) + "/./zbar/tmp.jpg"
        zbarimg = os_path_dirname(sys_argv[0]) + "/./zbar/bin/zbarimg.exe"
        bar_pattern = re_compile(":([A-Z0-9]+)\n")
        try:
            if " " in raw_img_path:
                raise BlockError
            else:
                img = open(raw_img_path, "rb")
                im = Image_open(img)
                x, y = im.size
                if x > 3000:
                    rm = im.resize((2000, int(2000*y/x)), ANTIALIAS)
                    with open(tmp_img, "w") as pic:
                        rm.save(pic)
                    barcode_name = bar_pattern.findall(
                        os_popen("%s %s %s" % (zbarimg, "-q", tmp_img)).read())[0] + ".jpg"
                else:
                    barcode_name = bar_pattern.findall(
                        os_popen("%s %s %s" % (zbarimg, "-q", raw_img_path)).read())[0] + ".jpg"
                img.close()
                new_img_path = os_path_join(path, barcode_name)
                os_rename(raw_img_path, new_img_path)
                cnt_ident += 1
        except IndexError:
            bar_error.append(raw_img_path)
            cnt_error += 1
        except FileExistsError:
            repeat_error.append(raw_img_path)
            cnt_repeat += 1
            #barcode_name = bar_pattern.findall(os_popen("%s %s %s" % (
            #    zbarimg, "-q", raw_img_path)).read())[0] + "_" + str(cnt_repeat) + ".jpg"
            #new_img_path = os_path_join(path, barcode_name)
            #os_rename(raw_img_path, new_img_path)
            cnt_ident += 1
        return cnt_ident, cnt_error, cnt_repeat

    print("\n正在批处理图片，请耐心等待...")
    for path, dirs, files in pdf:
        #print(path, dirs, files)
        for file in files:
            if os_path_splitext(file)[1].lower() in (".jpg", ".jpeg", ".tiff", ".tif", ".png"):
                raw_img_path = os_path_join(path, file)
                try:
                    ident(raw_img_path)
                except BlockError:
                    tmp_img_path = raw_img_path.replace(" ", "")
                    os_rename(raw_img_path, tmp_img_path)
                    ident(tmp_img_path)
            else:
                continue

    print("\n结束识别，正在输出识别报告：")
    rate = cnt_ident / (cnt_ident + cnt_error)
    print("\n成功识别 %d 张，%d 张照片无法识别条形码，%d 张照片的条形码重复,识别率为 %.2f" %
          (cnt_ident, cnt_error, cnt_repeat, rate))
    if cnt_repeat != 0:
        print("\n以下照片条形码号在其文件夹下存在重复，已经对其进行增量命名，请进一步核实：\n")
        for r in repeat_error:
            print(r)
    if cnt_error != 0:
        print("\n以下照片无法识别，请手动命名：\n")
        for err in bar_error:
            print(err)


def dwc_to_kingdonia(excel, style):
    """
    excel: Excel 表地址
    style: 需要转换成的数据表格式，"DWC"将转化为Kingdonia SimpleColumns 指定的列名，“Kingdonia“参数将转化为 Kiongdonia 标本数据库需要的列名
    return: 在原 Excel 表路径下生成一个新的 Kingdonia.xlsx 文件
    """
    kingdonia_columns = ["catalogNumber", "institutionCode", "otherCatalogNumbers", "classification", "lifeStage", 
                        "disposition", "preservedLocation", "preservedTime", "recordedBy", "recordNumber", "eventTime", 
                        "individualCount", "country", "stateProvince", "city", "county", "locality", "decimalLatitude", "decimalLongitude", 
                        "minimumElevationInMeters", "maximumElevationInMeters", "habitat", "habit", "频度", "体高", "胸径", 
                        "根", "茎", "叶", "花", "孢子囊（群）", "孢子叶（球）", "孢子体", "配子体", "子实体", "子实层", "果实", "种子",  
                        "菌盖", "菌柄", "菌肉", "气味", "当地名称", "野外鉴定", "organismRemarks", "occurrenceRemarks", "scientificName", 
                        "typeStatus", "identifiedBy", "dateIdentified", "associatedMedia", 
                        "molecularMaterialSample", "seedMaterialSample", "livingMaterialSample"]
    print("\n开始按照 DWC 标准转换表头...\n")
    table = fields_to_dwc(excel)
    try:
        dwc_columns = list(table.columns)
        all_columns = set(dwc_columns + kingdonia_columns)
    except AttributeError:
        return print("\n表头转换失败，请根据提示检查表头\n")
    print("\n开始校验前的数据列重组...\n")
    try:
        table = table.reindex(columns=all_columns)
    except AttributeError:
        return print("数据重组失败，请检查原Excel列名是否有重复语义的表头\n")
    tab_length = len(table)
    tab_len_scale = range(tab_length)
    print("开始经纬度的检查与转换...\n")
    table = convert_coordinate(table, tab_length, tab_len_scale)
    print("\033[32m程序会将任意书写格式的经纬度转化为十进制经纬度，并对错误的经纬度使用英文“!”标示。\033[0m\n")
    print("开始数值检查...\n")
    table = convert_number(table, "individualCount", form="int", max_num=30)
    table = convert_number(table, "minimumElevationInMeters", title2="maximumElevationInMeters", min_num=-1000, max_num=7000)
    print("\033[32m目前程序尚无法准确切分和标识“-100-1000m”这样的区间数据，但可以准确切分“100-1000m”，请核查时予以注意\n\033[0m")
    print("开始采集人的检查与转换...\n")
    print("\033[32m程序会自动规范英文采集人的写法，并且会统一以英文“,”分割各个采集人，对于采集人书写中\
        \n有明显错误字符的书写，会以英文“!”进行标示。\033[0m\n")
    table = convert_colloctor(table)
    print("开始日期的检查与转换...\n")
    table = convert_date(table, "eventTime", tab_len_scale)
    table = convert_date(table, "dateIdentified", tab_len_scale)
    print("\033[32m程序会对日期的任意书写格式以及日期的真实性进行转换和校验\
        \n将精确到日的日期，如”201212“转化为“2012-12-12 00:00:00”\
        \n将精确到月的日期，如“201212”转换为“2012-12-01 00:00:01”\
        \n将精确到年的日期，如“2012”转换为“2012-01-01 00:00:02”\
        \n以便于将日期直接应用于统计与计算。\033[0m\n")
    print("开始行政区划的检查与转换...\n")
    table = convert_div(table)
    print("\033[32m程序只会自动检查和转换中国县级及其以上行政区的各类中文写法，但目前尚无法处理英文行政区划\
        \n程序对中国中文行政区划的自动处理已经具备极高的可用性，但并不能保证百分之百正确，对于有疑议的处理通常\
        \n会以英文“！”标注。但对于“碧江”、“路南县”（云南省）这种孤立的现已撤销的行政区划，在其他省市区还有同\
        \n名或者其他地区名称被包括其中的行政区名称（中国,贵州省,铜仁市,碧江区，中国,湖南省,益阳市,南县）,程序\
        \n一定会出错且无法给出提示，这种情况虽然极少，但在人工核查时还需予以注意！\033[0m\n")
    print("开始重新组织拉丁学名...\n")
    table = convert_latinname(table, "scientificName")
    print("\033[32m目前程序只会对拉丁名进行去命名人处理，并不会核查拼写错误，后续会提出基于TPL的名称比对结果。\033[0m\n")
    print("开始单选字段的检查与转换...\n")
    table = convert_option(table, "habit")
    table = convert_option(table, "频度")
    table = convert_option(table, "typeStatus")
    table = convert_option(table, "lifeStage")
    table = convert_option(table, "disposition")
    table = convert_option(table, "molecularMaterialSample")
    table = convert_option(table, "classification")
    print("开始资源编号的检查...\n")
    table = check_catalognumber(table, "catalogNumber")
    table = check_catalognumber(table, "otherCatalogNumbers")
    print("\033[32m程序会对重复的/长度大于13位/编码中有非数字和字母的编号进行“!”标识\033[0m\n")
    print("开始检查馆代码...\n")
    table = check_herbariumcode(table, "institutionCode")
    print("\033[32m程序会对长度大于6位/非纯字母的字符进行标示，且会自动将小写字母转换为大写\033[0m\n")
    if style == "DWC":
        table = table.reindex(columns=dwc_columns)
        print("正在输出处理结果，数据量太大时，可能需要稍作等待...\n")
        table.to_excel(os_path_join(os_path_dirname(excel), "check.xlsx"), index=False)
        print("成功执行数据检查与转换，请前往原文件所在路径，查看输出的\033[33m check.xlsx \033[0m数据表\
        \n无法自动转换的错误数据已使用 '!' 进行标识，请打开转换后的 Excel 进行人工核查！！！\
        \n\033[33m对于各项数据的处理方式，请查看上述绿色字体说明。\033[0m \n\n")
    elif style == "Kingdonia":
        print("按照 Kingdonia 数字标本系统的标准取舍数据列...\n")
        table = table.reindex(columns=kingdonia_columns)
        print("开始使用默认值填充必填项...\n")
        table.fillna({"typeStatus":"not type", "seedMaterialSample":"0", "livingMaterialSample":"0", "identifiedBy":"缺失",  "habitat":"无", 
        "dateIdentified":"0000-01-01 00:00:00", "individualCount":"0", "molecularMaterialSample":"无", "decimalLatitude":0, "decimalLongitude":0}, inplace=True)
        with open(os_path_dirname(sys_argv[0]) + "/./Columns.json", "r", encoding="utf-8") as f:
            merger_columns = json_load(f)["ComplexColumns"]
        for k, v in merger_columns.items():
            if k == "identifications":
                ident = json_loads(table[v].to_json(orient="values", force_ascii=False))
                for n, w in enumerate(ident):
                    if w[0] == None:
                        ident[n] = None
                    else:
                        w.insert(1, 0)
                        ident[n] = json_dumps([w], ensure_ascii=False)
                table[k] = Series(ident)
            else:
                mergers = list(table[v].to_dict("records"))
                for i, r in enumerate(mergers):
                    c = r.copy()
                    for m, n in c.items():
                        if isnull(n):
                            del r[m]
                    if r == {}:
                        mergers[i] = None
                    else:
                        mergers[i] = json_dumps(r, ensure_ascii=False)
                table[k] = Series(mergers)
            table.drop(v, axis=1, inplace=True)
        print("正在输出处理结果，数据量太大时，可能需要稍作等待...\n")
        table.to_excel(os_path_join(os_path_dirname(excel), "kingdonia.xlsx"), index=False)
        print("成功执行数据检查与转换，请前往原文件所在路径，查看输出的\033[33m Kingdonia.xlsx \033[0m数据表\
        \n无法自动转换的错误数据已使用 '!' 进行标识，请打开转换后的 Excel 进行人工核查！！！\
        \n\033[33m对于各项数据的处理方式，请查看上述绿色字体说明。\033[0m \n\n")
    else:
        raise ValueError
    

def fields_to_dwc(excel):
    """
    excel: 需要处理的 Excel 数据表路径，要处理的数据必须位于excel第一张表内，且表头必须位于第一行
    retrun: 返回符合 Kingdonia Columns 配置文件中的列名的 Dataframe 格式的数据表，可能会对某些列进行拆分或合并，但不回校验或改写数据
    care:如果原表中有多个语意重复的列名，且其中至少有一个列名属于 Kingdonia Columns 标准列名，那么 return 的 table 会存在两个相同的列名，且没有提示
         因此建议在转换之前先检查列表，尽量去除重复语意的列名
    """
    temp_table = read_excel(excel, parse_dates=False)
    columns_converters = {}
    for c in temp_table.columns:
        columns_converters[c] = str
    table = read_excel(excel, converters=columns_converters)
    #print(table.columns)
    dwc = read_excel(os_path_dirname(sys_argv[0]) + "/./term_versions.xlsx")
    raw_to_std = dict.fromkeys(table.columns)
    hand_to_std = []
    with open(os_path_dirname(sys_argv[0]) + "/./Columns.json", "r", encoding="utf-8") as f:
        remap_columns = json_load(f)
    basic_columns = sorted(list(remap_columns["SimpleColumns"].keys()))
    #检查表头列名是否已有对应转换关系
    for w in raw_to_std:
        if w in remap_columns["SimpleColumns"]:
            raw_to_std[w] = w
        elif w in dwc[dwc.status=="recommended"]["label"].values:
            raw_to_std[w] = w
        else:
            for k, v in remap_columns["SimpleColumns"].items():
                if w in v:
                    if k not in raw_to_std.values():
                        raw_to_std[w] = k
                        break
                    else:
                        return print("与 %s 字段语义相同的列有多个，请手动去重后再运行程序"%(w)) 
                else:
                    continue
        if raw_to_std[w] == None:
            hand_to_std.append(w)
    # 处理未能找到对应关系的表头列名
    if hand_to_std != []:
        for n, v in enumerate(basic_columns):
            strings = str(n+1) + ". " + v
            if (n+1)%3 > 0:
                print(strings.ljust(25), end="\t")
            else:
                print(strings.ljust(25), end="\n")
        print("\n\n若干 Excel 列表名未能自动匹配标准字段名，你可以对这些列执行以下操作：\n\n")
        print("【1】指定该列的标准列名：例如要指定 Excel 中“区县”列的标准名，可以参考上述标准名称输入序号“7”或者“county”；\
            \n     如果上述序号没有对应的 Darwin Core 列名，您可以直接输入符合 DWC 要求的字符，比如“eventDate”\
            \n     有关 DWC 囊括的字段及其意义请自行访问 \033[32m http://rs.tdwg.org/dwc/terms/\033[0m 查看。\
            \n\n【2】拆分该列为多列： 例如要拆分 Excel 中的“省市”列为“stateProvince”、“city”两列，需输入表达式\
            \n     “stateProvince,city”，其中的“,”为原表中省、市之间的实际分隔符，如果数据表中实际是以“;”分割，\
            \n     请将上述“,”替换为“;”，拆分而成的新列名比如上述“stateProvince, city”也必须符合 DWC 标准。\
            \n\n【3】将该列与其他列合并：例如需要将 Excel 中的“种加词”列与“属”、“种下等级” 合并为新列“scientificName”，\
            \n     则需输入表达式“属 种加词 种下等级=scientificName”，其中 scientificName 为符合 Darwin Core 规范的字\
            \n     段名，各个列名之间的符号则为合并后，值之间的分隔符，本例按照学名规范，使用的是空格作为分隔符。\
            \n\n【4】忽略该列：直接输入0，程序会保留原列不变。\n\n")
        to_json_clm = []
        hand_to_std = dict.fromkeys(hand_to_std)
        for clm in hand_to_std:
            if hand_to_std[clm] == "skip":
                continue
            while True:
                i = input(clm + ": ")
                if i.isdecimal():
                    if int(i) > 0:
                        try:
                            input_value = basic_columns[(int(i)-1)]
                        except IndexError:
                            print("录入的数字超出可选值范围，请重新输入：\n")
                            continue
                        if input_value not in raw_to_std.values():
                            raw_to_std[clm] = input_value
                            remap_columns["SimpleColumns"][input_value].append(clm)
                            break
                        else:
                            print("你选择的列名与表头中其他列名指向冲突，您可以使用表达式拆分或合并该列/忽视该列/重新指向。")
                    elif int(i) == 0:
                        del raw_to_std[clm]
                        break
                elif i.isalpha():
                    search = dwc[(dwc.label==i)&(dwc.status=="recommended")]
                    if search.empty and i not in basic_columns:
                        print("自定义等字段名不在 DarwinCore 推荐命名空间之中，请重新输入：\n")
                    elif i not in raw_to_std.values():
                        raw_to_std[clm] = i
                        try:
                            remap_columns["SimpleColumns"][i].append(clm)
                        except KeyError:
                            remap_columns["SimpleColumns"][i] = [clm]
                        break
                    else:
                        print("你选择的列名与表头中其他列名指向冲突，您可以使用表达式拆分或合并该列/忽视该列/重新指向。")
                elif len(i)>0 and i[-1].isalpha():
                    value = merge_or_split_columns(table, i, raw_to_std, basic_columns, filter=True)
                    if type(value) == str:
                        print(value)
                    else:
                        table, raw_to_std, i = value
                        for field in i:
                            if field in hand_to_std:
                                hand_to_std[field] = "skip"
                        break

    with open(os_path_dirname(sys_argv[0]) + "/./Columns.json", "w", encoding="utf-8") as js:
        js.write(json_dumps(remap_columns, ensure_ascii=False))
    table.rename(columns=raw_to_std, inplace=True)
    try:
        for title in to_json_clm:
            table[title] = Series([json_dumps(value, ensure_ascii=False) if value!={} else None for value in table[title]])
    except UnboundLocalError:
        print("/n表头均可自动进行名称变换！/n")
    return table


def merge_or_split_columns(table, txt, raw_to_std, basic_columns, filter=True):
    dwc = read_excel(os_path_dirname(sys_argv[0]) + "/./term_versions.xlsx")
    elements = re_compile("([\u4e00-\u9fa5a-zA-Z_]+)([^\u4e00-\u9fa5a-zA-z]*)").findall(txt)
    titles = [e[0] for e in elements]
    separators = [e[1] for e in elements[0:-1]]
    if separators[-1] == "=":
        if len(set(titles[0:-1])) < len(titles)-1:
            return "表达式重复，请重新录入合并表达式：\n"
        if False in [(t in table.columns) for t in titles[0:-1]]:
            return "要合并的列不在当前表格，请重新输入：\n"
        merge_column = titles[-1]
        if filter == True:
            if merge_column not in dwc[dwc.status=="recommended"]["label"].values and merge_column not in basic_columns:
                return "输入的列名不在 darwincore 标准之内，请重新输入：\n"
        separators = separators[0:-1]
        if merge_column in titles[0:-1]:
            table.rename(columns=dict([(merge_column, "xuzhoufeng")]), inplace=True)
            for n,t in enumerate(titles):
                if t == merge_column:
                    titles[n] = "xuzhoufeng"
                    break
            del raw_to_std[merge_column]
            raw_to_std["xuzhoufeng"] = None
        table.rename(columns=dict([(titles[0], merge_column)]), inplace=True)
        del raw_to_std[titles[0]]
        titles.remove(titles[0])
        for title, separator in zip(titles[0:-1], separators):
            table[merge_column] = table[merge_column].str.cat(table[title], sep=separator, na_rep='')
        table.drop(titles[0:-1], axis=1, inplace=True)
        for title in titles[0:-1]:
            del raw_to_std[title]
        if merge_column in raw_to_std.values():
            return "新的列名已有指向，请重新输入表达式\n"
        else:
            raw_to_std[merge_column] = merge_column

    elif separators[0] == "=":
        if len(set(titles[1:])) < len(titles) - 1:
            return "表达式内列名有重复，请重新录入合并表达式：\n"
        if True in [(t in raw_to_std.values()) for t in titles[1:]]:
            return "拆分形成的新字段已存在，请核查后重新输入：\n"
        split_column = titles[0]
        if split_column not in raw_to_std.keys():
            return "要拆分的列不存在，请重新输入\n"
        if filter == True:
            if False in [(t in dwc[dwc.status=="recommended"]["label"].values) for t in titles[1:]] and False in [(t in basic_columns) for t in titles[1:]]:
                return "输入的列名不在 darwincore 标准之内，请重新输入：\n"
        separators = separators[1:]
        separators.sort(key=len, reverse=True)
        p = "|".join(separators)
        try:
            table = concat([table, table[split_column].str.split(p, n=len(titles)-2, expand=True)], axis=1)
            del table[split_column]
            table.rename(columns=dict([(n, v) for n,v in enumerate(titles[1:])]), inplace=True)
        except:
            print("Excel 相应列的值不符合切分表达式，请重新输入：\n")
        raw_to_std.update(dict([(t, t) for t in titles[1:]]))
        titles = [split_column]
        if split_column not in raw_to_std.values():
            del raw_to_std[split_column]

    else:
        return "表达式错误，请重新输入：\n"

    return table, raw_to_std, titles


def convert_number(table, title, title2=None, form="float", min_num=0, max_num=8848):
    """
    table: Dataframe 数据表
    title: 要处理的列名
    title2: 如果title可能要被分为两列（比如诸如“120-130”的海拔）title2 指明第二列的列名
    form: title 数值的数值类型，支持 float 和 int
    min_num: 数值区间的低值
    max_num: 数值区间的高值
    return: 如果出现 keyerro，返沪列表参数错误, 否则返回处理好的table
    care: 对于“-20-30“ 的值，无法准确划分为 -20和30，会被划分为 20和30
    """
    float_pattern = re_compile(r"^[+-]?\d+[\.\d]*|\d+[\.\d]*")
    int_pattern = re_compile(r"^[+-]?\d+|\d+")
    if form == "float":
        pattern = float_pattern
    elif form == "int":
        pattern = int_pattern
    else:
        raise ValueError
    try:
        lst_title = [pattern.findall(value) if not isnull(value) else [] for value in table[title]]
        value_title = []
        if title2 == None:
            for i, v in enumerate(lst_title):
                if len(v) == 1 and min_num<= float(v[0]) <= max_num:
                    value_title.append(float(v[0]))
                else:
                    if isnull(table[title][i]):
                        value_title.append(None)
                    else:
                        value_title.append("!" + str(table[title][i]))
            table[title] = Series(value_title)
        else:
            lst_title2 = [pattern.findall(value) if not isnull(value) else [] for value in table[title2]]
            for p, q in  zip(lst_title, lst_title2):
                merge_value = p+q
                if len(merge_value) == 2 and min_num<= float(merge_value[0]) <= max_num and min_num<= float(merge_value[1]) <= max_num:
                    if float(merge_value[0])<= float(merge_value[1]):
                        p.insert(0, merge_value[0])
                        q.insert(0, merge_value[1])
                    elif float(merge_value[1]) == 0: #系统默认补0造成的高值低于低值，处理为同值
                        p.insert(0, merge_value[0])
                        q.insert(0, merge_value[0])
                    else:
                        p.insert(0, merge_value[1])
                        q.insert(0, merge_value[0])
                elif len(merge_value) == 1 and min_num<= float(merge_value[0]) <= max_num:
                    p.insert(0, merge_value[0])
                    q.insert(0, merge_value[0])
                else:
                    p.insert(0, "!")
                    q.insert(0, "!")
            table[title] = Series([float(lst_title[i][0]) if lst_title[i][0] != "!" else "".join(["!", str(table[title][i])]) if not isnull(table[title][i]) else table[title][i] for i in range(len(lst_title))])
            table[title2] = Series([float(lst_title2[i][0]) if lst_title2[i][0] != "!" else "".join(["!", str(table[title2][i])]) if not isnull(table[title2][i]) else table[title][i] for i in range(len(lst_title2))])

    except KeyError:
        return print("列表参数有误\n")
    return table
    

def convert_latinname(table, title):
    """
    函数功能：处理各类手动输入的学名，返回去命名人的学名
    filepath：需要处理的excel文件路径
    title：需要处理的字段名称
    尚未解决种命名人相关的错误
    """
    lst_ident = list(table[title])
    dic_ident = dict.fromkeys(lst_ident)
    species_pattern = re_compile("\\b([A-Z][a-zàäçéèêëöôùûüîï-]+)\s?([×X])?\s?([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s?(.*)")
    subspecies_pattern = re_compile("(.*?)\s?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form|cv\.|cultivar\.)\s?([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)\s?([(（A-Z].*)")
    for w in dic_ident:
        try:
            species_split = species_pattern.findall(w)[0]
        except:
            continue
        subspec_split = subspecies_pattern.findall(species_split[3])
        
        if subspec_split == []:
            dic_ident[w] = " ".join([species_split[0], species_split[2]]) if species_split[1]=="" else " ".join([species_split[0], species_split[1], species_split[2]])
        else:
            dic_ident[w] = " ".join([species_split[0], species_split[2], subspec_split[0][1], subspec_split[0][2]]) if species_split[1]=="" else " ".join([species_split[0], species_split[1], species_split[2], subspec_split[0][1], subspec_split[0][2]])
    table[title] = Series([dic_ident[w] for w in lst_ident])
    return table


def convert_div(table):
    """中国省市县行政区匹配
    table:Dataframe 数据，DWC 格式；本程序只会处理中国的行政区,最小行政区划到县级
    return:返回匹配好的列，返回的字段值形式为“中国，北京，北京市”，程序不能保证百分百匹配正确
    care:对于只有“白云区”、“东区”等孤立的容易重名的地点描述，程序最终很可能给予错误的匹配，需要人工核查，匹配结果前有“!”标志
         对于“碧江”、"路南县"（云南省）这种孤立的现已撤销的地点描述但在其他省市区还有同名或者其他地区名称被包括其中的行政区名称（中国,贵州省,铜仁市,碧江区，中国,湖南省,益阳市,南县）；程序一定会出错且无法给出提示
         对于“四川省南川”、“云南碧江”这种曾经的行政区归属，程序会匹配字数多的行政区（这种状况下不会给出提示），如前者会匹配“中国,四川省”，对于字数一致的，则匹配短的行政区，但会标识，如后者可能匹配“!中国，云南省”
    """
    table["country"].fillna("", inplace=True)
    table["stateProvince"].fillna("", inplace=True)
    table["city"].fillna("", inplace=True)
    table["county"].fillna("", inplace=True)
    table["div"] = table["country"].str.cat(table["stateProvince"], sep="::").str.cat( table["city"]).str.cat(table["county"])
    lst_region = list(table["div"])
    dic_region = dict.fromkeys(lst_region)
    new_region = []
    dfm_stdregion = read_excel(os_path_dirname(sys_argv[0]) + "/./xzqh.xlsx")["MergerName"]
    #country_split = re_compile(r"([\s\S]*?)::([\s\S]*)")
    for raw_region in dic_region:
        score = (0, 0)  #分别记录匹配的字数和匹配项的长度
        region = raw_region.rstrip(":")
        for stdregion in dfm_stdregion:
            each_score = 0  #记录累计匹配的字数
            i = 0  #记录 region 参与匹配的起始字符位置
            j = 0  #记录 stdregion 参与匹配的起始字符位置
            while i < len(region)-1 and j < len(stdregion)-1: #一个字符无法匹配
                k = 2  #用于初始化、递增可匹配的字符长度
                n = stdregion[j:].find("::"+region[i:i+k])
                m = 0  #记录最终匹配的字符数
                if n != -1:
                    if region[-2] in stdregion:   #若存在”白云城矿区“”，就可能会错误的匹配“中国，内蒙古自治区，白云鄂博矿区”
                        while n != -1 and k <= len(region[i:]):
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
                if dic_region[raw_region] in stdregion:
                    pass
                elif len(stdregion) < score[1]:  #优先匹配字符短的行政区，避免“河北”匹配上“中国,天津,天津市,河北区
                    score = each_score, len(stdregion)
                    dic_region[raw_region] = "!"+stdregion
            elif each_score > score[0]:
                score = each_score, len(stdregion)
                dic_region[raw_region] = stdregion
        if score == (0, 0):  #如果没有匹配到，是中国的行政区，则夹住！标识
            if "中国" in raw_region:
                dic_region[raw_region] = "!" + raw_region
            else:
                dic_region[raw_region] = raw_region
        else:
            continue

        #print(raw_region, dic_region[raw_region])
    new_region = [(dic_region[region].split("::") if dic_region[region] is not None else dic_region[region]) for region in lst_region]
    [(region.extend([None]*(4-len(region))) if region is not None and len(region) < 4 else region) for region in new_region] #注意浅拷贝陷阱
    table["country"] = Series([(region[0] if region is not None else None) for region in new_region])
    table["stateProvince"] = Series([(region[1] if region is not None else None) for region in new_region])
    table["city"] = Series([(region[2] if region is not None else None) for region in new_region])
    table["county"] = Series([(region[3] if region is not None else None) for region in new_region])
    del table["div"]
    return table


def convert_coordinate(table, tab_length, tab_len_scale):
    table["经纬度"] = table["decimalLongitude"].astype("str").str.cat(table["decimalLatitude"].astype("str"), sep=";")
    raw_coordinate_list = list(table["经纬度"])
    new_coordinate_lng = [None]*tab_length
    new_coordinate_lat = [None]*tab_length
    coordinate_pattern_1 = re_compile("[NESWnesw][^A-Za-z,，；;]*[0-9][^A-Za-z,，；;]+")                               #NSWE 前置经纬度
    coordinate_pattern_2 = re_compile("[0-9][^A-Za-z,，；;]+[NESWnesw]")                               #NSWE 后置经纬度
    coordinate_pattern_3 = re_compile(r"[+-]?\d+[\.\d]*")
    coordinate_pattern_num = re_compile(r"[\d\.]+")
    coordinate_pattern_NSEW = re_compile("[NESWnesw]")
    for i in tab_len_scale:
        try:
            tem_coordinate_element = coordinate_pattern_1.findall(raw_coordinate_list[i])      #提取坐标，并将其列表化，正常情况下将有两个元素组成列表
            if len(tem_coordinate_element) != 2:                                               #通过小数点个数和列表长度初步判断是否是合格的坐标
                tem_coordinate_element = coordinate_pattern_2.findall(raw_coordinate_list[i])
                if len(tem_coordinate_element) != 2:
                    tem_coordinate_element = coordinate_pattern_3.findall(raw_coordinate_list[i])
                    #print(tem_coordinate_element)
                    if len(tem_coordinate_element) == 2 and abs(float(table["decimalLatitude"][i])) <= 90 and abs(float(table["decimalLongitude"][i])) <= 180:
                        new_coordinate_lng[i] = round(float(table["decimalLongitude"][i]), 6)
                        new_coordinate_lat[i] = round(float(table["decimalLatitude"][i]), 6)
                        continue
                    else:
                        #print(tem_coordinate_element ,type(table["decimalLongitude"][i]))
                        new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]            #如果值由错误，则保留原值，如果是数值型值，考虑到已无法恢复，则触发错误不做任何保留
                        new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
                        continue
            direct_fir = coordinate_pattern_NSEW.findall(tem_coordinate_element[0])[0]         #单个单元格内，坐标第一个值的方向指示
            direct_sec = coordinate_pattern_NSEW.findall(tem_coordinate_element[1])[0]         #单个单元格内，坐标第二个值的方向指示
            coordinate_fir_num = coordinate_pattern_num.findall(tem_coordinate_element[0])    #获得由坐标中的度分秒值组成的数列
            coordinate_sec_num = coordinate_pattern_num.findall(tem_coordinate_element[1])
            #print(i, " ", direct_fir, direct_sec, coordinate_fir_num, coordinate_sec_num)
            if direct_fir in "NSns" and direct_sec in "EWew" and float(coordinate_fir_num[0]) <= 90 and float(coordinate_sec_num[0]) <= 180:                            #判断哪一个数值是纬度数值，哪一个数值是经度数值
                direct_fir_seq = 1
            elif direct_fir in "EWew" and direct_sec in "NSns" and float(coordinate_sec_num[0]) <= 90 and float(coordinate_fir_num[0]) <= 180:
                direct_fir_seq = 0
            else:
                new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
                continue
            direct_plus_minus = {"N":1, "S":-1, "E":1, "W":-1, "n":1, "s":-1, "e":1, "w":-1}
            if len(coordinate_fir_num) == 3 and len(coordinate_sec_num) == 3:
                if int(coordinate_fir_num[1]) >= 60:
                    new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                    new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
                    continue
                if float(coordinate_fir_num[2]) >= 60 or float(coordinate_sec_num[2]) >= 60:  #度分表示法写成了度分秒表示法
                    if direct_fir_seq == 1:
                        new_coordinate_lat[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + float(coordinate_fir_num[1] + "." + coordinate_fir_num[2])/60, 6)
                        new_coordinate_lng[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + float(coordinate_sec_num[1] + "." + coordinate_sec_num[2])/60, 6)
                    else:
                        new_coordinate_lng[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + float(coordinate_fir_num[1] + "." + coordinate_fir_num[2])/60, 6)
                        new_coordinate_lat[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + float(coordinate_sec_num[1] + "." + coordinate_sec_num[2])/60, 6)
                else:                                                                        #度分秒表示法
                    if direct_fir_seq == 1:
                        new_coordinate_lat[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + int(coordinate_fir_num[1])/60 + float(coordinate_fir_num[2])/3600, 6)
                        new_coordinate_lng[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + int(coordinate_sec_num[1])/60 + float(coordinate_sec_num[2])/3600, 6)
                    else:
                        new_coordinate_lng[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + int(coordinate_fir_num[1])/60 + float(coordinate_fir_num[2])/3600, 6)
                        new_coordinate_lat[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + int(coordinate_sec_num[1])/60 + float(coordinate_sec_num[2])/3600, 6)
            elif len(coordinate_fir_num) == 2 and len(coordinate_sec_num) == 2:             #度分表示法
                if float(coordinate_fir_num[1]) >= 60:
                    new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                    new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
                    continue
                if direct_fir_seq ==1:
                    new_coordinate_lat[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + float(coordinate_fir_num[1])/60, 6)
                    new_coordinate_lng[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + float(coordinate_sec_num[1])/60, 6)
                else:
                    new_coordinate_lng[i] = direct_plus_minus[direct_fir]*round(int(coordinate_fir_num[0]) + float(coordinate_fir_num[1])/60, 6)
                    new_coordinate_lat[i] = direct_plus_minus[direct_sec]*round(int(coordinate_sec_num[0]) + float(coordinate_sec_num[1])/60, 6)
            elif len(coordinate_fir_num) == 1 and len(coordinate_sec_num) == 1:            #度表示法
                if direct_fir_seq ==1:
                    new_coordinate_lat[i] = direct_plus_minus[direct_fir]*round(float(coordinate_fir_num[0]), 6)
                    new_coordinate_lng[i] = direct_plus_minus[direct_sec]*round(float(coordinate_sec_num[0]), 6)
                else:
                    new_coordinate_lng[i] = direct_plus_minus[direct_fir]*round(float(coordinate_fir_num[0]), 6)
                    new_coordinate_lat[i] = direct_plus_minus[direct_sec]*round(float(coordinate_sec_num[0]), 6)
            elif len(coordinate_fir_num) < 4 and len(coordinate_sec_num) < 4:            #处理度分/度分秒表示法中，纬度、经度最后一项正好为0被省略导致经纬度不等长的问题
                if False not in [f() for f in [(lambda i=i:float(i)<60) for i in coordinate_fir_num[1:]+coordinate_sec_num[1:]]]:
                    if (lambda n = min(coordinate_fir_num, coordinate_sec_num)[-1]:"." not in n)():
                        if direct_fir_seq == 1:
                            new_coordinate_lat[i] = direct_plus_minus[direct_fir]*round(sum([float(coordinate_fir_num[i])/pow(60, i) for i in range(len(coordinate_fir_num))]),6)
                            new_coordinate_lng[i] = direct_plus_minus[direct_sec]*round(sum([float(coordinate_sec_num[i])/pow(60, i) for i in range(len(coordinate_sec_num))]),6)
                        else:
                            new_coordinate_lng[i] = direct_plus_minus[direct_fir]*round(sum([float(coordinate_fir_num[i])/pow(60, i) for i in range(len(coordinate_fir_num))]),6)
                            new_coordinate_lat[i] = direct_plus_minus[direct_sec]*round(sum([float(coordinate_sec_num[i])/pow(60, i) for i in range(len(coordinate_sec_num))]),6)
                    else:
                        new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                        new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
                else:
                    new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                    new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]
            else:
                    new_coordinate_lng[i] = "!" + table["decimalLongitude"][i]
                    new_coordinate_lat[i] = "!" + table["decimalLatitude"][i]

        except TypeError:
            continue
        except ValueError:
            new_coordinate_lng[i] = "!" + str(table["decimalLongitude"][i])
            new_coordinate_lat[i] = "!" + str(table["decimalLatitude"][i])
            continue
    table["decimalLongitude"] = Series(new_coordinate_lng)
    table["decimalLatitude"] = Series(new_coordinate_lat)
    del table["经纬度"]
    #print(table[["decimalLongitude", "decimalLatitude"]])
    return table


def convert_colloctor(table):
    """
    table: 要处理的dwc标准的 dataframe 数据表
    return: 返回table, 并将dwc采集人统一转换为以英文逗号分隔的人名字符串，可中英文人名混排“徐洲锋,A. Henry,徐衡”，并以 “!“ 标识可能错误写法的字符串
    care: 无法处理“徐洲锋 洪丽林 徐衡” 这样单以空格切分单中文人命字符串
    """
    raw_col = list(table["recordedBy"])
    dic_col = {}.fromkeys(raw_col)
    for rec in dic_col:
        try:
            rec_lst = [name.strip().title() for name in re_split("[,，;；、\&。][\s]*", rec)]
            rmv_elm = []
            for i, w in enumerate(rec_lst[:]):
                if len(w) < 3 and w[-1] in [".", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "K", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]:
                    rec_lst[i] = rec_lst[i-1] + " " + w[0] + "."  ## 解决类似 A.Henry  这样的人名
                    rmv_elm.append(rec_lst[i-1])
            dic_col[rec] = ",".join([s for s in rec_lst if s not in rmv_elm])
        except:
            if isnull(rec):
                continue
            else:
                dic_col[rec] = "!" + str(rec)
    pur_col = [dic_col[txt] for txt in raw_col]
    table["recordedBy"] = Series(pur_col)
    return table


def convert_date(table, title, tab_len_scale):
    raw_date = list(table[title])
    #print(raw_date)
    dmy_pattern = re_compile("[A-Za-z]+|[0-9]+")
    er_date_dict = {"JAN":1, "FEB":2, "MAR":3, "APR":4, "APRI":4, "MAY":5, "JUN":6, "JUL":7, "AUG":8, "SEP":9, "SEPT":9, "OCT":10, "NOV":11, "DEC":12,"Jan":1, "Feb":2, "Mar":3, "Apr":4, "Apri":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Sept":9, "Oct":10, "Nov":11, "Dec":12, "I":1, "II":2, "III":3, "IV":4, "V":5, "VI":6, "VII":7, "VIII":8, "IX":9, "X":10, "XI":11, "XII":12}
    for j in tab_len_scale:
        try:
            timestamp = time_strptime(raw_date[j], "%Y-%m-%d %H:%M:%S")
        except (TypeError,ValueError):
            #对日期字符串的数值进行拆分提取
            try:
                single_date_list = dmy_pattern.findall(raw_date[j])
                if single_date_list == []:
                    raw_date[j] = None
                    continue
            except (TypeError, ValueError):
                raw_date[j] = None
                continue
            date_degree = len(single_date_list)
            if date_degree == 6:
                date_degree = 3
                single_date_list = single_date_list[0:3]
            elif date_degree == 1:
                temp = single_date_list[0]
                if len(temp) == 6:
                    date_degree = 2
                    single_date_list[0] = temp[0:4]
                    single_date_list.append(temp[4:6])
                elif len(temp) == 8:
                    date_degree = 2
                    single_date_list[0] = temp[0:4]
                    single_date_list.append(temp[4:6])
                    if temp[6:8] != "00":
                        date_degree = 3
                        single_date_list.append(temp[6:8])

            year, month, day = [], [], []
            HMS = " 00:00:00"
            #获取单个日期的年月日值，如果单个日期的年月日值有不同的拼写法，则全部转换成整型
            for i in range(date_degree):
                try:
                    single_date_list[i] = int(single_date_list[i])
                except ValueError:
                    #print(single_date_list)
                    if single_date_list[i] in er_date_dict:
                        single_date_list[i] = er_date_dict[single_date_list[i]]
                    else:
                        raw_date[j] = "!" + raw_date[j]
                        break
            if raw_date[j][0] == "!":
                continue
            else:
                #判断年月日的数值是否符合规范，以及判断各个数值是 年 月 日 中的哪一个
                for k in range(date_degree):
                    single_date_element = single_date_list[k]
                    if date_degree == 3:
                        if k == 1:
                            month = single_date_element
                        elif single_date_element > 2099:
                            raw_date[j] = "!" + raw_date[j]
                            break
                        elif single_date_element > 999:
                            year = single_date_element
                        elif single_date_element >31:
                            year = 1900 + single_date_element%100
                        elif year != []:
                            day = single_date_element
                        elif single_date_list[2] > 31:
                            day = single_date_element
                        else:
                            raw_date[j] = "!" + raw_date[j]
                            break
                    elif date_degree == 2:
                        if single_date_element > 2099:
                            raw_date[j] = "!" + raw_date[j]
                            break
                        elif single_date_element > 999:
                            year = single_date_element
                        elif single_date_element > 31:
                            year = single_date_element%100 + 1900
                        elif single_date_element > 12:
                            if year != []:
                                raw_date[j] = "!" + raw_date[j]
                                break
                            elif month != []:
                                year = 1900 + single_date_element
                            elif single_date_list[1] < 13:
                                year = 1900 + single_date_element
                            else:
                                raw_date[j] = "!" + raw_date[j]
                                break
                        elif single_date_element > 0:
                            if year != []:
                                month = single_date_element
                            elif single_date_list[1] > 12:
                                month = single_date_element
                            else:
                                raw_date[j] = "!" + raw_date[j]
                                break
                        else:
                            raw_date[j] = "!" + raw_date[j]
                            break
                    elif date_degree ==1:
                        if single_date_element > 2099:
                            raw_date[j] = "!" + raw_date[j]
                            break
                        elif single_date_element > 999:
                            year = single_date_element
                        elif single_date_element > 31:
                            year = 1900 + single_date_element%100
                        else:
                            raw_date[j] = "!" + raw_date[j]
                    else:
                        raw_date[j] = "!" + raw_date[j]
                        break
                if raw_date[j][0] == "!":
                    continue
                else:
                    if day == []:
                        day = 1
                        HMS = " 00:00:01"
                    if month == []:
                        month =1
                        HMS = " 00:00:02"
                    try:                                                         #判断该日期是否真实存在
                        date(year,month,day)
                        raw_date[j] = str(year) + "-" + str(month) + "-" + str(day) + HMS
                    except ValueError:
                        raw_date[j] = "!" + raw_date[j]
                        continue
            timestamp = time_strptime(raw_date[j], "%Y-%m-%d %H:%M:%S")

        if date(timestamp[0], timestamp[1], timestamp[2]) > date.today():
            raw_date[j] = "!" + raw_date[j]
        else:
            continue
    table[title] = Series(raw_date)
    return table



def convert_option(table, attr):
    goals = list(table[attr])
    dic_values = dict.fromkeys(goals)
    with open(os_path_dirname(sys_argv[0]) + "/./options.json", "r", encoding="utf-8") as o:
        std_values = json_load(o)
    ls_std_values = sorted(list(std_values[attr].keys()))
    for key in dic_values:
        if key in ls_std_values:
            dic_values[key] = key
        else:
            for k, v in std_values[attr].items():
                if key in v:
                    dic_values[key] = k
                    break
            if dic_values[key] is None:
                if isnull(key):
                    continue
                else:
                    print(str(key) + "=>不是标准的属性值，请将其对应至以下可选值中的某一个:\n")
                    for n, m in enumerate(ls_std_values):
                        strings = str(n+1) + ". " + m
                        if (n+1)%3 > 0:
                            print(strings.ljust(25), end="\t")
                        else:
                            print(strings.ljust(25), end="\n\n")
                    while True:
                        n = input("\n\n请输入对应的阿拉伯数字，无法对应请输入数字\033[1;35;43m 0 \033[0m:\n\n")
                        if n == '0':
                            dic_values[key] = "!" + key
                            break
                        else:
                            try:
                                std_values[attr][ls_std_values[int(n)-1]].append(key)
                                dic_values[key] = ls_std_values[int(n)-1]
                                break
                            except:
                                print("\n输入的字符有误...\n")
    
    with open(os_path_dirname(sys_argv[0]) + "/./options.json", "w") as f:
        f.write(json_dumps(std_values, ensure_ascii=False))
    table[attr] = Series([dic_values[w] for w in goals])
    return table
            

def check_catalognumber(table, title):
    barcodes = list(table[title])
    barcodes_rpt = Counter(barcodes)
    for sequence, barcode in enumerate(barcodes):
        if isnull(barcode):
            continue
        elif barcode.isalnum() and len(barcode) < 14:
            if barcodes_rpt[barcode] == 1:
                continue
            else:
                barcodes[sequence] = "!" + barcode
        else:
            barcodes[sequence] = "!" + barcode
    table[title] = Series(barcodes)
    return table


def check_herbariumcode(table, title):
    codes = list(table[title])
    for num, code in enumerate(codes):
        try:
            if code.isalpha() and len(code) < 6:
                if code.isupper():
                    continue
                else:
                    codes[num] = code.upper()
            else:
                codes[num] = "!" + str(code)
        except AttributeError:
            continue
    table[title] = Series(codes)
    return table


