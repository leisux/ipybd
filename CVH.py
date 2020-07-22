# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 14:31:29 2015

@author: Xu Zhoufeng
"""
from tqdm import tqdm
from tqdm import trange
from json import loads as json_loads
from re import compile as re_compile
from pandas import read_excel
from pandas import DataFrame
from dateutil.parser import parse
from pandas import Series
from pandas import isnull
from pandas import concat as pd_concat
from datetime import datetime
from os.path import join as os_path_join
from os.path import dirname as os_path_dirname


def kingdonia_fieds2cvh(excel):
    table = read_excel(excel, sheet_name="展开数据")
    #table = bkt_dynamicProperties2cvh(table)
    table = btk_datetime2cvh(table, "eventTime")
    table = btk_datetime2cvh(table, "dateIdentified")
    table = btk_collectors2cvh(table)
    table = btk_scientificName2cvh(table, "scientificName")
    kda2cvh = {"catalogNumber":"条形码", "institutionCode":"馆代码", "otherCatalogNumbers":"流水号", "lifeStage":"标本状态", 
    "disposition":"库存", "typeStatus":"模式类型", "recordedBy":"采集人", "recordNumber":"采集号", "eventTime":"采集日期", 
    "country":"国家", "stateProvince":"省市", "county":"区县", "locality":"小地点", "habitat":"生境", "minimumElevationInMeters":"海拔", 
    "decimalLongitude":"经度", "decimalLatitude":"纬度", "vernacularName":"中文名", "family":"科名", "vernacularFamilyName":"科中文名", 
    "genus":"属名", "vernacularGenusName":"属中文名", "种加词":"种加词", "命名人":"命名人", "种下等级":"种下等级", "种下命名人":"种下命名人", 
    "identifiedBy":"鉴定人", "dateIdentified":"鉴定日期", "occurrenceRemarks":"备注", "habit":"习性", "individualCount":"份数"}
    table.rename(columns=kda2cvh, inplace=True)
    table.drop(["maximumElevationInMeters", "preservedLocation", "preservedTime", "associatedMedia", "molecularMaterialSample", 
    "identificationID", "relationshipEstablishedTime", "classification", "city", "organismRemarks", "种子", "频度", "植物习性"], axis=1, inplace=True)
    table.to_excel(os_path_join(os_path_dirname(excel), "cvh.xlsx"), index=False)


def bkt_dynamicProperties2cvh(table):
    dynamicProperties = list(table["dynamicProperties"])
    for num, properties in enumerate(tqdm(dynamicProperties, desc="JSON 转列表", ascii=True)):
        try:
            properties = json_loads(properties)
            if isinstance(properties, dict):
                dynamicProperties[num] = properties
            else:
                dynamicProperties[num] = {}
        except:
            dynamicProperties[num] = {}
    df = DataFrame(dynamicProperties)
    table = pd_concat([table, df], axis=1)
    return table


def btk_datetime2cvh(table, title):
    datetimes = list(table[title])
    for num, dt in enumerate(tqdm(datetimes, desc=title, ascii=True)):
        if isinstance(dt, datetime):
            dt = str(dt)
        try:
            datetimes[num] = parse(dt).strftime('%Y%m%d') 
            if dt.endswith("00:00:02") and datetimes[num][4:6] == "01":
                datetimes[num] = datetimes[num].replace(datetimes[num][4:], "0000")
            if dt.endswith("00:00:01") and datetimes[num][6:] == "01":
                datetimes[num] = datetimes[num].replace(datetimes[num][6:], "00")
        except (ValueError, TypeError, IndexError):
            if isnull(dt) or dt.startswith("!"):
                continue
            else:
                datetimes[num] = "!" + str(dt)
    table[title] = Series(datetimes)
    return table
            

def btk_collectors2cvh(table):
    recordedby = list(table["recordedBy"])
    btk_userid_pattern = re_compile(r"\|[0-9]+")
    for num, coll in enumerate(tqdm(recordedby, desc="去除采集人ID", ascii=True)):
        if coll.startswith("!"):
            continue
        else:
            btk_userid = btk_userid_pattern.findall(coll)
            if btk_userid == []:
                continue
            else:
                for userid in btk_userid:
                    coll = coll.replace(userid, "")
                recordedby[num] = coll
    table["recordedBy"] = Series(recordedby)
    return table


def btk_scientificName2cvh(table, title):
    '''
    函数功能：处理各类手动输入的学名，返回去命名人/分列的学名
    table：需要处理的pandas.dataframe数据表
    title：需要处理的字段名称
    care:尚未解决命名人相关的错误
    testname:Saxifraga umbellulata Hook. f. et Thoms. var. pectinata (C. Marq. et Airy Shaw) J. T. Pan
             Anemone demissa Hook. f. et Thoms. var. yunnanensis Franch.
             Schisandra grandiflora (Wall.) Hook. f. et Thoms.
             Phaeonychium parryoides (Kurz ex Hook. f. et T. Anderson) O. E. Schulz
             Crucihimalaya lasiocarpa (Hook. f. et Thoms.) Al-Shehbaz et al.
             Saxifraga rufescens bal f. f.
             Saxifraga rufescens Bal f. f. var. uninervata J. T. Pan
             Lindera pulcherrima (Nees) Hook. f. var. attenuata C. K. Allen
             Polygonum glaciale (Meisn.) Hook. f. var. przewalskii (A. K. Skvortsov et Borodina) A. J. Li
             Psilotrichum ferrugineum (Roxb.) Moq. var. ximengense Y. Y. Qian
             Houpoëa officinalis (Rehd. et E. H. Wils.) N. H. Xia et C. Y. Wu
    '''
    goals = list(table[title])
    length = len(table)
    species_pattern = re_compile(r'\b([A-Z][a-zàäçéèêëöôùûüîï-]+)\s?([×X])?\s?([a-zäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s?(.*)')
    subspecies_pattern = re_compile(r'(.*?)\s?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form|cv\.|cultivar\.)\s?([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)\s?([(（A-Z].*)')
    gen_list = [None]*length
    spec_list = [None]*length
    spec_named_person = [None]*length
    subspec_list = [None]*length
    subspec_named_person = [None]*length
    #useless_word = ['ex','et','al','sp','nov','s','l']
    for i in trange(length, desc="拉丁名分列", ascii=True):
        try:
            species_split = species_pattern.findall(goals[i])[0]
        except:
            continue
        gen_list[i] = species_split[0]
        if species_split[1] == "":  #判定是否有杂交符
            spec_list[i] = species_split[2]
        else:
            spec_list[i] = species_split[1] + " " + species_split[2]
        subspec_split = subspecies_pattern.findall(species_split[3])
        if subspec_split == []:
            spec_named_person[i] = species_split[3]
        else:
            spec_named_person[i] = subspec_split[0][0]
            subspec_list[i] = subspec_split[0][1] + " " + subspec_split[0][2]
            subspec_named_person[i] = subspec_split[0][3]
    del table[title]
    #table['属名'] = Series(gen_list)
    table['种名'] = Series(spec_list)
    table['命名人'] = Series(spec_named_person)
    table['种下等级'] = Series(subspec_list)
    table['种下命名人'] = Series(subspec_named_person)
    return table


