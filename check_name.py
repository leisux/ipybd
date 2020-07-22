import pandas as pd
import requests
import time
import urllib
import asyncio
import aiohttp
import re
from enum import Enum

SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'http://beta.ipni.org/api/1'
POWO_API = 'http://www.plantsoftheworldonline.org/api/2'

class Filters(Enum):
    familial = {"kew":"f_familial", "col":"getFamiliesByFamilyName"}
    infrafamilial = {"kew":"f_infrafamilial"}
    generic = {"kew":"f_generic", "col":"getSpeciesByScientificName"}
    infrageneric = {"kew":"f_infrageneric"}
    specific = {"kew":"f_specific", "col":"getSpeciesByScientificName"}
    infraspecific = {"kew":"f_infraspecific", "col":"getSpeciesByScientificName"}
    commonname = {"col":"getSpeciesByCommonName"}


def run(latin_names, classificaiton=True):
    #start = time.time()
    #控制异步并发数量可修改这里
    sema = asyncio.Semaphore(500)
    querys = build_querys(latin_names)
    loop = asyncio.get_event_loop()
    session = loop.run_until_complete(creat_session())
    tasks = [asyncio.ensure_future(
        get_col_name(sema, querys[rawname], SP2000_API, session)) 
        for rawname in querys if querys[rawname] != None]
    result = loop.run_until_complete(asyncio.gather(*tasks))
    loop.run_until_complete(session.close())
    loop.close()
    for res in result:
        querys[res[0]] = res[1], res[2], res[3]
    for raw in querys:
        if querys[raw] == None:
            try:
                #无法格式化的学名用英文感叹号标注
                querys[raw] = "".join(["!", raw]), None, None
            except TypeError:
                #若非文本字符，就清掉
                querys[raw] = None, None, None

    full_name = [querys[w][0] for w in latin_names]
    if classificaiton:
        family = [querys[w][1] for w in latin_names]
        genus = [querys[w][2] for w in latin_names]
    return full_name, genus, family
    #end = time.time()
    #print("Execution Time: ", end - start)

async def creat_session():
    return aiohttp.ClientSession()

def build_querys(idents):
    raw2stdname = dict.fromkeys(idents)
    for raw_name in raw2stdname:
        raw2stdname[raw_name] = format_name(raw_name)
    return raw2stdname

def format_name(raw_name):
    """ 将手写学名转成规范格式

        raw_name: 各类手录学名，目前仅支持 属名 x 种名 种命名人 种下加词 种下命名人
                  这类学名格式的清洗，其中杂交符、种命名人、种下命名人均可缺省。
        
        目前仍有个别命名人十分复杂的名称学名，清洗后无法得到正确而的结果，使用时需注意
    """
    species_pattern = re.compile(r"\b([A-Z][a-zàäçéèêëöôùûüîï-]+)\s?([×X])?\s?([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s?(.*)")
    subspecies_pattern = re.compile(r"(.*?)\s?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form|cv\.|cultivar\.)\s?([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)\s?([(（A-Z].*)")
    try:
        species_split = species_pattern.findall(raw_name)[0]
    except:
        return None
    subspec_split = subspecies_pattern.findall(species_split[3])
    
    if subspec_split == []:
        simple_name = " ".join([species_split[0], species_split[2]]) if \
            species_split[1]=="" else " ".join([species_split[0], 
                species_split[1], species_split[2]])
        author = species_split[3]
        if species_split[2] != "":
            rank = Filters.specific
        elif species_split[0].endswith((
            "aceae", "Umbelliferae", "Labiatae", "Compositae", "Gramineae", 
            "Leguminosae")):
            rank = Filters.familial
        else:
            rank = Filters.generic
    else:
        simple_name = " ".join([species_split[0], species_split[2], subspec_split[0][1], subspec_split[0][2]]) if species_split[1]=="" else " ".join([species_split[0], species_split[1], species_split[2], subspec_split[0][1], subspec_split[0][2]])
        author = subspec_split[0][3]
        rank = Filters.infraspecific
    return simple_name.strip(), rank, author, raw_name

async def get_col_name(sema, query, api, session):
    """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息
        
        sema: 异步并发数限制
        query: (simple_name, rank, author, raw_name)
        api: COL V2 的数据接口地址
        seesion：发起异步协程请求时的 session
        return：raw_name, scientificName, family, genus
    """
    name = await check_col_search(sema, query, api, session)
    if not name:
        # 如果 col 无合法结果，搜索 kew 数据库
        return await get_kew_name(sema, query, IPNI_API, session)
    else:
        try:
            scientific_name = " ".join([name['scientific_name'], name['accepted_name_info']['author']])
            family = name['accepted_name_info']['taxonTree']['family']
            genus = name['accepted_name_info']['taxonTree']['genus']
        except KeyError:
            try:
                genus = name['genus']
                scientific_name = genus
                family = name['family']
            except KeyError:
                family = name['family']
                scientific_name = family
                genus = None
        #print(query[3], genus, family, author)
        return query[3], scientific_name, family, genus

async def get_kew_name(sema, query, api, session):
    """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息
        
        sema: 异步并发数限制
        query: (simple_name, rank, author, raw_name)
        api: KEW 的数据接口地址
        seesion：发起异步协程请求时的 session
        return：raw_name, scientificName, family, genus
    """
    name = await check_kew_search(sema, query, api, session)
    if not name:
        return  query[3], " ".join(["".join(["!", query[0]]), query[2]]).strip(), None, None
    else:
        scientific_name = " ".join([name["name"], name["authors"]])
        family = name['family']
        try:
            genus = name['genus']
        except KeyError:
            genus = None
        #print(query[3], genus, family, author)
        return query[3], scientific_name, family, genus

async def check_col_search(sema, query, api, session):
    """ 对 COL 返回对结果逐一进行检查

    return: 返回最能满足 query 条件的学名 dict，由于 COL 各级别返回的数据有差异，所以返回
        的 dict 需要有针对性的进行处理，各级别返回样式：
        {"family_c":"樟科","phylum_c":"被子植物门","superfamily":null,"kingdom":"Plantae","record_id":"F20171000000190","phylum":"Angiospermae","kingdom_c":"植物界","family":"Lauraceae","class":"Magnoliopsida","class_c":"木兰纲","order_c":"樟目","order":"Laurales","superfamily_c":null}
        {"phylum":"Angiospermae","genus":"Rhododendron","species":"delavayi","infraspecies":"puberulum","family":"Ericaceae","kingdom":"Plantae","class":"Magnoliopsida","order":"Ericales"}
        {"accepted_name_info":{"searchCodeStatus":"accepted name","namecode":"T20171000080711","scientificName":"Rhododendron delavayi var. puberulum","author":"Xiang Chen & Xun Chen","Refs":[{"[1]":"Seed 29(1): 66 (2010)"}],"Distribution":"Guizhou(贵州省)","taxonTree":{"phylum":"Angiospermae","genus":"Rhododendron","species":"delavayi","infraspecies":"puberulum","family":"Ericaceae","kingdom":"Plantae","class":"Magnoliopsida","order":"Ericales"},"chineseName":"","searchCode":"T20171000080711","CommonNames":[],"SpecialistInfo":[{"E-Mail":"docxfjin@163.com","Address":"No.16 Xuelin Street, Jianggan District, Hangzhou, Zhejiang 310036(310036 浙江省杭州市江干区学林街16号)","name":"Jin Xiaofeng(金孝锋)","Institution":"Herbarium, College of Life and Environmental Sciences,Hangzhou Normal University(杭州师范大学生命与环境科学学院)"}]},"name_code":"T20171000080711","name_status":"accepted name","scientific_name":"Rhododendron delavayi var. puberulum"}
    """
    async with sema:
        results = await col_search(query[0], query[1], api, session)
        if results == None or results == []:
            return None
        else:
            names = []
            for num, res in enumerate(results):
                if query[1] is Filters.specific or query[1] is Filters.infraspecific:
                    if res['scientific_name'] == query[0] and res['accepted_name_info']['author'] != "":
                        # col 返回的结果中，没有命名人 list，额外自行添加
                        # 由于 COL 返回但结果中无学名的命名人，因此只能通过其接受名
                        # 的 author 字段获得命名人，但接受名可能与检索学名不一致，所以此
                        # 处暂且只能在确保检索学名为接受名后，才能添加命名人
                        if res['name_status'] == 'accepted name':
                            results[num]['author_team'] = get_author_team(res['accepted_name_info']['author'])
                            names.append(res)
                elif query[1] is Filters.generic and res['accepted_name_info']['taxonTree']['genus'] == query[0]:
                    # col 接口目前尚无属一级的内容返回，这里先取属下种及种下一级的分类阶元返回
                    return res['accepted_name_info']['taxonTree']
                elif query[1] is Filters.familial and res['family'] == query[0]:
                    return res
            authors = get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                print("{0} 在中国生物物种名录中可能是异名、不存在或缺乏有效命名人，请手动核实\n".format(query[-1]))
                return None
            # 如果只检索到一个结果或者检索数据命名人缺失，默认使用第一个同名结果
            elif len(names) == 1 or authors == []:
                name = names[0]
            else:
                # 提取出API返回的多个名称的命名人序列，并将其编码
                aut_codes = code_authors(authors)                
                std_teams = {n: code_authors(r['author_team']) for n, r in enumerate(names)}
                #开始比对原命名人与可选学名的命名人的比对结果
                scores = contrast_code(aut_codes, std_teams)
                #print(scores)
                name = names[scores[0][1]]
                #if std_teams[scores[0][1]] > 10000000000:
                #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                # 但不一定是真符合
        return name

async def check_kew_search(sema, query, api, session):
    """ 对 KEW 返回结果逐一进行检查

    return: 返回最满足 query 条件的学名 dict
    """
    async with sema:
        results = await kew_search(query[0], query[1], api, session)
        if results == None or results == []:
            # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
            return None
        else:
            names = []
            for num, res in enumerate(results):
                if res["name"] == query[0]:
                    names.append(res)
            authors = get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                print(query)
                return None
            # 如果只检索到一个结果或者检索数据命名人缺失，默认使用第一个同名结果
            elif len(names) == 1 or authors == []:
                name = names[0]
            else:
                # 提取出API返回的多个名称的命名人序列，并将其编码
                aut_codes = code_authors(authors)
                std_teams = {}
                for n, r in enumerate(names):
                    t = []
                    for a in r["authorTeam"]:
                        t.append(a["name"])
                    std_teams[n] = code_authors(t)
                #开始比对原命名人与可选学名的命名人的比对结果
                scores = contrast_code(aut_codes, std_teams)
                #print(scores)
                name = names[scores[0][1]]
                #if std_teams[scores[0][1]] > 10000000000:
                #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                # 但不一定是真符合
        return name

async def col_search(query, filters, api, session):
    params = build_col_params(query, filters)
    url = build_url(api, filters.value['col'], params)
    resp = await search(url, session)
    if resp['code'] == 200:
        try:
            # 先尝试返回种及种下物种的信息
            return resp['data']['species']
        except KeyError:
            # 出错后，确定可以返回科的信息
            return resp['data'] ['familes']
    elif resp['code'] == 400:
        print("\n参数不合法：{url}\n".format(url))
        return None
    elif resp['code'] == 401:
        print("\n密钥错误：{url}\n".format(url))
        return None

async def kew_search(query, filters, api, session):
    params = build_kew_params(query, filters)
    resp = await search(build_url(api, 'search', params), session)
    if 'results' in resp:
        return resp['results']
    else:
        return None

async def search(url, session):
    try:
        while True:
            #print(url)
            async with session.get(url, timeout=60) as resp:
                if resp.status == 429:
                    await asyncio.sleep(3)
                else:
                    response = await resp.json()
                    break
    except:  #如果异步请求出错，改为正常的 Get 请求以尽可能确保有返回结果
        response = await normal_request(url)
    if response == None:
        print(url, "未能联网核查，请检查网络连接！")
    return response  # 返回 None 表示网络有问题

async def normal_request(url):
    try:
        while True:
            rps = requests.get(url)
            #print(rps.status_code)
            if rps.status_code == 429:
                await asyncio.sleep(3)
            else:
                return rps.json()
    except:
        return None

def build_col_params(query, filters):
    params = {'apiKey':'42ad0f57ae46407686d1903fd44aa34c'}
    if filters is Filters.familial:
        params['familyName'] = query
    elif filters is Filters.commonname:
        params['commonName'] = query
    else:
        params['scientificName'] = query
    params['page'] = 1
    return params

def build_kew_params(query, filters):
    params = {'perPage': 500, 'cursor': '*'}
    if query:
        params['q'] = format_kew_query(query)
    if filters:
        params['f'] = format_kew_filters(filters)
    return params

def build_url(api, method, params):
    return '{base}/{method}?{opt}'.format(
           base = api,
           method = method,
           opt = urllib.parse.urlencode(params)
    )

def format_kew_query(query):
    if isinstance(query, dict):
        terms = [k.value + ':' + v for k, v in query.items()]
        return ",".join(terms)
    else:
        return query

def format_kew_filters(filters):
    if isinstance(filters, list):
        terms = [f.value['kew'] for f in filters]
        return ",".join(terms)
    else:
        return filters.value['kew']

def contrast_code(raw_code, std_codes):
    """ 将一个学名的命名人和一组学名的命名人编码进行比较，以确定最匹配的

    raw_code: 一个学名命名人列表经code_author编码返回的列表
              如["Hook. f.", "Thomos."]编码后获得[12113, 141123]

    std_code: 一组包含多个API返回结果的值序号及其命名人编码的对应字典
              如 {0:[4322], 1:[1234，27685]}

    return: 返回一个与原命名人匹配亲近关系排列的list，
            如[(0, 1）, (1249, 0)]，其中元组首位为该名称的匹配度，
            值越小越匹配，元组第二个元素是该值在API返回值中的序号
    """
    for k, names_code in std_codes.items():
        k_score = []
        for name in names_code:
            name_scores = []
            for aut in raw_code:
                name_scores.append(max(aut, name)%min(aut, name))
            k_score.append(min(name_scores))
        std_codes[k] = sum(k_score)//len(names_code)
    # 开始从比对结果中，结果将取命名人偏差最小的API返回结果
    # std_teams中可能存在多个最优，而程序无法判定采用哪一个比如原始数据
    # 命名人为(A. K. Skvortsov et Borodina) A. J. Li，而ipni返回
    # 的标准名称中存在命名人分别为 A. K. Skvortsov 和 
    # Borodina et A. J. Li 两个同名学名，其std_teams值都将为最小偏差
    # 值 0， 此时程序将任选一个其实这里也可以考虑将其标识，等再考虑考虑，
    # 有的时候ipni数据也有可能有错，比如 Phaeonychium parryoides 就存
    # 在这个问题，但这种情况应该是小比率，对于结果的帅选逻辑，可以修改下方逻辑
    scores = [(x, y) for y, x in std_codes.items()]
    scores.sort(key=lambda s:s[0])
    return scores

def code_authors(authors):
    """
    authors: 一个学名命名人的 list
    return: 返回学名中每个命名人的正整数转码 list
            该转码是对姓名字母排序信息墒的一维表达
    """
    aut_codes = []
    for aut in authors:
        aut = aut.replace(".", "")
        aut = aut.replace("-", " ")
        code_author = 1
        for i, letter in enumerate(aut):
            n = ord(letter)
            if n == 32:
                code_author = code_author
            elif aut[i-1] == letter:
                pass
            elif n < 91:
                code_author = code_author * (ord(letter)-64)
            elif aut[i-1] == " " and n > 96:
                code_author = code_author * (ord(letter)-96)
            else:
                code_author = code_author * abs((ord(aut[i-1])-n))
        aut_codes.append(code_author)
    return aut_codes

def get_author_team(authors):
    """ 提取学名命名人中，各个命名人的名字

    authors: 一个学名的命名人字符串

    return: 返回包含authors 中所有人名list，返回的 list 人名排序不一定与 authors
            相同，对于 Hook. f. 目前只能提取出 Hook. ，程序仍需进一步完善，不过对于
            学名之间的人名比较，已经足够用了
    """
    p4 = re.compile(r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+")
    p3 = re.compile(r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+")
    p2 = re.compile(r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+")
    p1 = re.compile(r"\b[A-Z][A-Za-z\.-]+")
    author_team = []
    for p in (p4, p3, p2, p1):
        aus = p.findall(authors)
        author_team = author_team + aus
        for author in aus:
            authors = authors.replace(author, "", 1)
    return author_team

if __name__ == "__main__":
    table = pd.read_excel(r"/Users/xuzhoufeng/Downloads/lbg-不合格.xlsx")
    start = time.time()
    stdnames = pd.DataFrame({'scientificName':run(table["学名"])[0]})
    table = pd.concat([table, stdnames], axis=1)
    table.to_excel(r"/Users/xuzhoufeng/Downloads/lbg.xlsx")
    end = time.time()
    print("Execution Time: ", end - start)

# KEW API beta
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Glycine+&f=f_generic
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Lauraceae+&f=f_familial
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Glycine+max&f=f_specific
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Thalictrum+aquilegiifolium+var.+sibiricum&f=f_infraspecific

# sp2000.org.cn API V1
# GET http://www.sp2000.org.cn/api/family/familyName/familyID/Poaceae/42ad0f57ae46407686d1903fd44aa34c
# GET http://www.sp2000.org.cn/api/taxon/familyID/taxonID/F20171000000256/42ad0f57ae46407686d1903fd44aa34c
# GET http://www.sp2000.org.cn/api/taxon/scientificName/taxonID/Poaceae%20annua/42ad0f57ae46407686d1903fd44aa34c
# GET http://www.sp2000.org.cn/api/taxon/commonName/taxonID/早熟禾/42ad0f57ae46407686d1903fd44aa34c
# GET http://www.sp2000.org.cn/api/taxon/species/taxonID/T20171000041825/42ad0f57ae46407686d1903fd44aa34c


# sp2000.org.cn API V2
# http://www.sp2000.org.cn/api/v2/getFamiliesByFamilyName?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyName=Lauraceae&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByFamilyId?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyId=F20171000000256&page=2
# http://www.sp2000.org.cn/api/v2/getSpeciesByScientificName?apiKey=42ad0f57ae46407686d1903fd44aa34c&scientificName=Rhododendron%20delavayi&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByCommonName?apiKey=42ad0f57ae46407686d1903fd44aa34c&commonName=%E6%97%A9%E7%86%9F%E7%A6%BE&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByNameCode?apiKey=42ad0f57ae46407686d1903fd44aa34c&nameCode=T20171000041825&page=1