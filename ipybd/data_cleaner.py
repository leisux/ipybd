import os
import re
import time
from datetime import date, timedelta
import json
import requests
import urllib
from ipybd.api_terms import Filters
import asyncio
import aiohttp
import pandas as pd
from tqdm import tqdm

SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'http://beta.ipni.org/api/1'
POWO_API = 'http://www.plantsoftheworldonline.org/api/2'

class BioName:
    def __init__(self, names):
        if isinstance(names, str):
            self.names = [names]
        else:
            self.names = names
        self.action = {
                       'stdName':self.get_name,
                       'colTaxonTree':self.get_col_taxonTree,
                       'colName':self.get_col_name,
                       'ipniName':self.get_ipni_name,
                       'powoName':self.get_powo_name,
                       'powoAccepted':self.get_powo_accepted,
                       'colSynonyms':self.get_col_synonyms,
                       'ipniReference':self.get_ipni_reference,
                       'powoImages':self.get_powo_images
                       }
        self.querys = self.build_querys(self.names)
        self.sema = asyncio.Semaphore(500)

    def get(self, action):
        self.pbar = tqdm(total=len(self.querys), desc=action, ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [asyncio.ensure_future(
            self.get_track(self.action[action], self.querys[rawname]))
            for rawname in self.querys if self.querys[rawname] != None]
        session = loop.run_until_complete(self.creat_session())
        result = loop.run_until_complete(asyncio.gather(*tasks))
        loop.run_until_complete(session.close())
        loop.close()
        res_len = len(result[0]) - 1
        results = {}
        for res in result:
            results[res[0]] = res[1:]
        # 无法格式化的原值用英文感叹号标注
        for name in self.querys:
            if self.querys[name] == None:
                try:
                    results[name] = ["".join(["!", name])]
                except TypeError:
                    results[name] = ["".join(["!", str(name)])]
                results[name].extend([None]*(res_len-1))
                results[name] = tuple(results[name])
        self.pbar.close()
        return [results[w] for w in self.names]

    async def get_track(self, func, param):
        result = await func(param)
        self.pbar.update(1)
        return result

    async def creat_session(self):
        return aiohttp.ClientSession()

    async def get_powo_images(self, query):
        name = await self.check_powo_name(query)
        if not name:
            return query[-1], None
        else:
            try:
                images = [image['fullsize'] for image in name['images']]
            except KeyError:
                return query[-1], None
        return query[-1], images

    async def get_col_synonyms(self, query):
        name = await self.check_col_name(query)
        if not name:
            return  query[-1], None
        else:
            try:
                return query[-1], [synonym['synonym'] for synonym in name['accepted_name_info']['Synonyms']]
            except KeyError:
                return query[-1], None

    async def get_powo_accepted(self, query):
        name = await self.check_powo_name(query)
        if not name:
            return query[-1], None, None
        else:
            try:
                name = name['synonymOf']
            except KeyError:
                pass
        return query[-1], name['name'], name['author']

    async def get_col_taxonTree(self, query):
        name = await self.check_col_name(query)
        if not name:
            return query[-1], None, None, None, None, None
        else:
            try:
                genus = name['accepted_name_info']['taxonTree']['genus']
                family = name['accepted_name_info']['taxonTree']['family']
                order = name['accepted_name_info']['taxonTree']['order']
                _class = name['accepted_name_info']['taxonTree']['class']
                phylum = name['accepted_name_info']['taxonTree']['phylum']
                kingdom = name['accepted_name_info']['taxonTree']['kingdom']
            except KeyError:
                try:
                    genus = name['genus']
                    family = name['family']
                    order = name['order']
                    _class = name['class']
                    phylum = name['phylum']
                    kingdom = name['kingdom']
                except:
                    genus = None
                    family = name['family']
                    order = name['order']
                    _class = name['class']
                    phylum = name['phylum']
                    kingdom = name['kingdom']
            return query[-1], genus, family, order, _class, phylum, kingdom

    async def get_ipni_reference(self, query):
        name = await self.check_ipni_name(query)
        if not name:
            return query[-1], None, None, None, None
        else:
            publishing_author = name['publishingAuthor']
            publication_year = name['publicationYear']
            publication = name['publication']
            reference = name['reference']
        return query[-1], publishing_author, publication_year, publication, reference

    async def get_name(self,query):
        name = await self.get_col_name(query)
        if not name[1]:
            name = await self.get_ipni_name(query)
            if not name[1]:
                # 如果检索无有效结果，用英文感叹号标注
                name[1] = "".join(["!", query[-1]]).strip()
        return name

    async def get_col_name(self, query):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: COL V2 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_col_name(query)
        if not name:
            return  query[-1], None, None, None
        else:
            try:  # 种及种下检索结果
                scientific_name = name['scientific_name']
                author = name['accepted_name_info']['author']
                family = name['accepted_name_info']['taxonTree']['family']
            except KeyError:
                try:  # 属的检索结果
                    scientific_name = name['genus']
                    author = None
                    family = name['family']
                except KeyError:  #科的检索结果
                    family = name['family']
                    author = None
                    scientific_name = family
                    genus = None
            #print(query[-1], genus, family, author)
            return query[-1], scientific_name, author, family

    async def check_col_name(self, query):
        """ 对 COL 返回对结果逐一进行检查

        return: 返回最能满足 query 条件的学名 dict
        """
        async with self.sema:
            results = await self.col_search(query[0], query[1])
            if results == None or results == []:
                return None
            else:
                names = []
                for num, res in enumerate(results):
                    if query[1] is Filters.specific or query[1] is Filters.infraspecific:
                        if res['scientific_name'] == query[0] and res['accepted_name_info']['author'] != "":
                            # col 返回的结果中，没有 author team，需额外自行添加
                            # 由于 COL 返回但结果中无学名的命名人，因此只能通过其接受名的
                            # author 字段获得命名人，但接受名可能与检索学名不一致，所以
                            # 此处暂且只能在确保检索学名为接受名后，才能添加命名人
                            if res['name_status'] == 'accepted name':
                                results[num]['author_team'] = self.get_author_team(res['accepted_name_info']['author'])
                                names.append(res)
                    elif query[1] is Filters.generic and res['accepted_name_info']['taxonTree']['genus'] == query[0]:
                        # col 接口目前尚无属一级的内容返回，这里先取属下种及种下一级的分类阶元返回
                        return res['accepted_name_info']['taxonTree']
                    elif query[1] is Filters.familial and res['family'] == query[0]:
                        return res
                authors = self.get_author_team(query[2])
                # 如果搜索名称和返回名称不一致，标注后待人工核查
                if names == []:
                    #print("{0} 在中国生物物种名录中可能是异名、不存在或缺乏有效命名人，请手动核实\n".format(query[-1]))
                    return None
                # 如果只检索到一个结果或者检索数据命名人缺失，默认使用第一个同名结果
                elif len(names) == 1 or authors == []:
                    name = names[0]
                else:
                    # 提取出API返回的多个名称的命名人序列，并将其编码
                    aut_codes = self.code_authors(authors)                
                    std_teams = {n: self.code_authors(r['author_team']) for n, r in enumerate(names)}
                    #开始比对原命名人与可选学名的命名人的比对结果
                    scores = self.contrast_code(aut_codes, std_teams)
                    #print(scores)
                    name = names[scores[0][1]]
                    #if std_teams[scores[0][1]] > 10000000000:
                    #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                    # 但不一定是真符合
            return name
    
    async def col_search(self, query, filters):
        params = self.build_col_params(query, filters)
        url = self.build_url(SP2000_API, filters.value['col'], params)
        resp = await self.async_request(url)
        try:
            if resp['code'] == 200:
                try:
                    # 先尝试返回种及种下物种的信息
                    return resp['data']['species']
                except KeyError:
                    # 出错后，确定可以返回科的信息
                    return resp['data'] ['familes']
            elif resp['code'] == 400:
                print("\n参数不合法：{0}\n".format(url))
                return None
            elif resp['code'] == 401:
                print("\n密钥错误：{0}\n".format(url))
                return None
            else:
                return None
        except KeyError:
            print("\nInternal Server Error: {0}\n".format(url))
            return None
        except TypeError:
            print("\n返回类型错误:{0}\n".format(url))

    async def get_ipni_name(self, query):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: KEW 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_ipni_name(query)
        if not name:
            return  query[-1], None, None, None
        else:
            scientific_name = name["name"]
            author = name["authors"]
            family = name['family']
            #print(query[-1], genus, family, author)
            return query[-1], scientific_name, author, family

    async def get_powo_name(self, query):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: KEW 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_powo_name(query)
        if not name:
            return  query[-1], None, None, None
        else:
            scientific_name = name["name"]
            author = name["author"]
            family = name['family']
            #print(query[-1], genus, family, author)
            return query[-1], scientific_name, author, family

    async def check_ipni_name(self, query):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        async with self.sema:
            results = await self.kew_search(query[0], query[1], IPNI_API)
            if results == None or results == []:
                # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
                return None
            else:
                names = []
                for num, res in enumerate(results):
                    if res["name"] == query[0]:
                        names.append(res)
                authors = self.get_author_team(query[2])
                # 如果搜索名称和返回名称不一致，标注后待人工核查
                if names == []:
                    #print(query)
                    return None
                # 如果只检索到一个结果，或者检索词缺乏命名人，默认使用第一个同名结果
                elif len(names) == 1 or authors == []:
                    name = names[0]
                else:
                    # 提取出API返回的多个名称的命名人序列，并将其编码
                    aut_codes = self.code_authors(authors)
                    std_teams = {}
                    for n, r in enumerate(names):
                        t = []
                        for a in r["authorTeam"]:
                            t.append(a["name"])
                        std_teams[n] = self.code_authors(t)
                    #开始比对原命名人与可选学名的命名人的比对结果
                    scores = self.contrast_code(aut_codes, std_teams)
                    #print(scores)
                    name = names[scores[0][1]]
                    #if std_teams[scores[0][1]] > 10000000000:
                    #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                    # 但不一定是真符合
            return name

    async def check_powo_name(self, query):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        async with self.sema:
            results = await self.kew_search(query[0], query[1], POWO_API)
            if results == None or results == []:
                # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
                return None
            else:
                names = []
                for num, res in enumerate(results):
                    if res["name"] == query[0]:
                        res['authorTeam'] = self.get_author_team(res['author'])
                        names.append(res)
                authors = self.get_author_team(query[2])
                # 如果搜索名称和返回名称不一致，标注后待人工核查
                if names == []:
                    #print(query)
                    return None
                # 如果只检索到一个结果，默认使用这个同名结果
                elif len(names) == 1:
                    name = names[0]
                # 如果有多个结果，但检索名的命名人缺失，则默认返回第一个accept name
                elif authors == []:
                    name = names[0]
                    for n in names:
                        if n['accepted'] == True:
                          return n
                else:
                    # 提取出API返回的多个名称的命名人序列，并将其编码
                    aut_codes = self.code_authors(authors)
                    std_teams = {n: self.code_authors(r['authorTeam']) for n, r in enumerate(names)}
                    #开始比对原命名人与可选学名的命名人的比对结果
                    scores = self.contrast_code(aut_codes, std_teams)
                    name = names[scores[0][1]]
                    #if std_teams[scores[0][1]] > 10000000000:
                    #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                    # 但不一定是真符合
            return name

    async def kew_search(self, query, filters, api):
        params = self.build_kew_params(query, filters)
        resp = await self.async_request(self.build_url(api, 'search', params))
        if 'results' in resp:
            return resp['results']
        else:
            return None

    async def async_request(self, url):
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
            response = await self.normal_request(url)
        if response == None:
            print(url, "联网超时，请检查网络连接！")
        return response  # 返回 None 表示网络有问题

    async def normal_request(self, url):
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

    def format(self, p = 'scientificName'):
        std_names = self.build_querys(self.names)
        if p == 'simpleName':
            return [std_names[name][0] if name != None else None for name in self.names]
        elif p == 'scientificName':
            return [' '.join([std_names[name][0], std_names[name][2]]) if name !=None else None for name in self.names]

    def build_col_params(self, query, filters):
        params = {'apiKey':'42ad0f57ae46407686d1903fd44aa34c'}
        if filters is Filters.familial:
            params['familyName'] = query
        elif filters is Filters.commonname:
            params['commonName'] = query
        else:
            params['scientificName'] = query
        params['page'] = 1
        return params

    def build_kew_params(self, query, filters):
        params = {'perPage': 500, 'cursor': '*'}
        if query:
            params['q'] = self.format_kew_query(query)
        if filters:
            params['f'] = self.format_kew_filters(filters)
        return params

    def build_url(self, api, method, params):
        return '{base}/{method}?{opt}'.format(
               base = api,
               method = method,
               opt = urllib.parse.urlencode(params)
        )

    def format_kew_query(self, query):
        if isinstance(query, dict):
            terms = [k.value + ':' + v for k, v in query.items()]
            return ",".join(terms)
        else:
            return query

    def format_kew_filters(self, filters):
        if isinstance(filters, list):
            terms = [f.value['kew'] for f in filters]
            return ",".join(terms)
        else:
            return filters.value['kew']

    def build_querys(self, names):
        raw2stdname = dict.fromkeys(names)
        for raw_name in raw2stdname:
            raw2stdname[raw_name] = self.format_name(raw_name)
        return raw2stdname

    def format_name(self, raw_name):
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

    def contrast_code(self, raw_code, std_codes):
        """ 将一个学名的命名人和一组学名的命名人编码进行比较，以确定最匹配的

        raw_code: 一个学名命名人列表经code_author编码返回的列表
                  如["Hook. f.", "Thomos."]编码后获得[12113, 141123]

        std_code: 一组包含API多个返回结果的值序号及其命名人编码的对应字典
                  如 {0:[4322], 1:[1234，27685]}

        return: 返回一个与原命名人匹配亲近关系排列的list，
                如[(0, 1）, (1249, 0)]，其中元组首位为该名称的匹配度，
                值越小越匹配，元组第二个元素是该值在API返回值中的序号
        """
        for k, authorship in std_codes.items():
            k_score = []
            # 计算学名命名人每个人名与待选学名命名人的匹配度
            for author in raw_code:
                scores = []
                for name in authorship:
                    scores.append(max(author, name)%min(author, name))
                # 每个人名取匹配度分数最低的分值
                k_score.append(min(scores))
            std_codes[k] = (sum(k_score)//len(raw_code)+1)*2**abs(len(raw_code)-len(authorship))
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

    def code_authors(self, authors):
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
                if n == 32:  # 排除空格
                    code_author = code_author
                elif aut[i-1] == letter and i != 0: #避免前后字母序号差相减等于 0 
                    pass
                elif n < 91:  # 人名中的大写字母
                    code_author = code_author * (ord(letter)-64)
                elif aut[i-1] == " " and n > 96:  #人名之中的小写首字母
                    code_author = code_author * (ord(letter)-96)
                else:
                    code_author = code_author * abs((ord(aut[i-1])-n))
            aut_codes.append(code_author)
        return aut_codes

    def get_author_team(self, authors):
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

    def __call__(self):
        choose = input("\n是否执行拼写检查，在线检查将基于 sp2000.org.cn、ipni.org 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会惠耗费较长时间（y/n）\n")
        if choose.strip() == 'y':
            return pd.DataFrame([' '.join([name[0], name[1]]).strip() for name in self.get('stdName')])
        else:
            return pd.DataFrame(self.format())


class AdminDiv:
    """中国省市县行政区匹配

    本程序只会处理中国的行政区,最小行政区划到县级返回的字段值形式为“中国,北京,北京市,朝阳区”，
    程序不能保证百分百匹配正确；
    对于只有“白云区”、“东区”等孤立的容易重名的地点描述，程序最终很可能给予错误的匹配，需要人工
    核查，匹配结果前有“!”标志；
    对于“碧江”、"路南县"（云南省）这种孤立的现已撤销的地点描述但在其他省市区还有同名或者其他地
    区名称被包括其中的行政区名称（中国,贵州省,铜仁市,碧江区，中国,湖南省,益阳市,南县）；程序一
    定会给出错误匹配且目前并不会给出任何提示；
    对于“四川省南川”、“云南碧江”这种曾经的行政区归属，程序会匹配字数多的行政区且这种状况下不会
    给出提示，如前者会匹配“中国,四川省”，对于字数一致的，则匹配短的行政区，但会标识，如后者可能
    匹配“!中国,云南省”
    """

    def __init__(self, address):
        self.org_address = address
        self.region_mapping = dict.fromkeys(self.org_address)

    def format_chinese_admindiv(self):
        new_region = []
        dfm_stdregion = pd.read_excel(os.path.dirname(__file__) + "/./xzqh.xlsx")["MergerName"]
        #country_split = re.compile(r"([\s\S]*?)::([\s\S]*)")
        for raw_region in tqdm(self.region_mapping, desc="行政区划", ascii=True):
            if pd.isnull(raw_region):
                continue
            score = (0, 0)  # 分别记录匹配的字数和匹配项的长度
            region = raw_region.rstrip(":")
            for stdregion in dfm_stdregion:
                each_score = 0  # 记录累计匹配的字数
                i = 0  # 记录 region 参与匹配的起始字符位置
                j = 0  # 记录 stdregion 参与匹配的起始字符位置
                while i < len(region)-1 and j < len(stdregion)-1: # 单字无法匹配
                    k = 2  # 用于初始化、递增可匹配的字符长度
                    n = stdregion[j:].find("::"+region[i:i+k])
                    m = 0  # 记录最终匹配的字符数
                    if n != -1:
                        # 白云城矿区可能会错误的匹配“中国,内蒙古自治区,白云鄂博矿区”
                        if region[-2] in stdregion:
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
                    if self.region_mapping[raw_region] in stdregion:
                        pass
                    # 优先匹配字符短的行政区，避免“河北”匹配“中国,天津,天津市,河北区
                    elif len(stdregion) < score[1]:
                        score = each_score, len(stdregion)
                        self.region_mapping[raw_region] = "!"+stdregion
                elif each_score > score[0]:
                    score = each_score, len(stdregion)
                    self.region_mapping[raw_region] = stdregion
            if score == (0, 0):
                # 如果没有匹配到，又是中国的行政区，英文!标识 
                if "中国" in raw_region:
                    self.region_mapping[raw_region] = "!" + raw_region
                else:
                    self.region_mapping[raw_region] = raw_region
            else:
                continue
            #print(raw_region, self.region_mapping[raw_region])
        #为提升生成效率， 先用复杂的列表推导式处理
        new_region = [(self.region_mapping[region].split("::") if self.region_mapping[region] is not None else self.region_mapping[region]) for region in self.org_address]
        [(region.extend([None]*(4-len(region))) if region is not None and len(region) < 4 else region) for region in new_region] #注意浅拷贝陷阱
        self.country = [(region[0] if region is not None else None) for region in new_region]
        self.stateProvince = [(region[1] if region is not None else None) for region in new_region]
        self.city = [(region[2] if region is not None else None) for region in new_region]
        self.county = [(region[3] if region is not None else None) for region in new_region]

    def __call__(self):
        self.format_chinese_admindiv()
        return pd.DataFrame({
                            'country':self.country, 
                            'stateProvince':self.stateProvince, 
                            'city':self.city, 
                            'county':self.county
                            })


class  NumericalInterval:
    def __init__(self, column, column2=None, form="float", min_num=0, max_num=8848):
        """
            column: 可迭代对象，数据列
            column2: 数据列2，可迭代对象
            form: title 数值的数值类型，支持 float 和 int
            min_num: 数值区间的低值
            max_num: 数值区间的高值
        """
        self.column = column
        self.column2 = column2
        self.form = form
        self.min_num = min_num
        self.max_num = max_num
    
    def format_number(self):
        """
        return: 如果出现 keyerro，返惠列表参数错误, 否则返回处理好的table
        care: 对于“-20-30“ 的值，无法准确划分为 -20和30，会被划分为 20和30
        """
        float_pattern = re.compile(r"^[+-]?\d+[\.\d]*|\d+[\.\d]*")
        int_pattern = re.compile(r"^[+-]?\d+|\d+")
        if self.form == "float":
            pattern = float_pattern
        elif self.form == "int":
            pattern = int_pattern
        else:
            raise ValueError
        try:
            lst_title = [pattern.findall(str(value)) if not pd.isnull(value) else [] for value in self.column]
            value_title = []
            if self.column2 is None:
                for i, v in enumerate(tqdm(lst_title, desc="数值处理", ascii=True)):
                    if len(v) == 1 and self.min_num<= float(v[0]) <= self.max_num:
                        value_title.append(float(v[0]))
                    else:
                        if pd.isnull(self.column[i]):
                            value_title.append(None)
                        else:
                            value_title.append("!" + str(self.column[i]))
                self.column = pd.Series(value_title)
            else:
                lst_title2 = [pattern.findall(str(value)) if not pd.isnull(value) else [] for value in self.column2]
                for p, q in zip(tqdm(lst_title, desc="数值区间", ascii=True), tqdm(lst_title2, desc="数值区间", ascii=True)):
                    merge_value = p+q
                    if len(merge_value) == 2 and self.min_num<= float(merge_value[0]) <= self.max_num and self.min_num <= float(merge_value[1]) <= self.max_num:
                        if float(merge_value[0])<= float(merge_value[1]):
                            p.insert(0, merge_value[0])
                            q.insert(0, merge_value[1])
                        elif float(merge_value[1]) == 0:  # 系统默认补0造成的高值低于低值，处理为同值
                            p.insert(0, merge_value[0])
                            q.insert(0, merge_value[0])
                        else:
                            p.insert(0, merge_value[1])
                            q.insert(0, merge_value[0])
                    elif len(merge_value) == 1 and self.min_num <= float(merge_value[0]) <= self.max_num:
                        p.insert(0, merge_value[0])
                        q.insert(0, merge_value[0])
                    else:
                        p.insert(0, "!")
                        q.insert(0, "!")
                self.column = pd.Series([float(lst_title[i][0]) if lst_title[i][0] != "!" else "".join(["!", str(self.column[i])]) if not pd.isnull(self.column[i]) else self.column[i] for i in range(len(lst_title))])
                self.column2 = pd.Series([float(lst_title2[i][0]) if lst_title2[i][0] != "!" else "".join(["!", str(self.column2[i])]) if not pd.isnull(self.column2[i]) else self.column[i] for i in range(len(lst_title2))])

        except KeyError:
            return print("列表参数有误\n")

    def __call__(self):
        self.format_number()
        if self.column2 is None:
            return pd.DataFrame(self.column)
        else:
            return pd.DataFrame({"min_num":self.column, "max_num":self.column2})


class GeoCoordinate:
    def __init__(self, coordinates):
        # coordinates 为包含经度和纬度的数据列，为可迭代对象
        self.coordinates = coordinates

    def format_coordinates(self):
        new_lng = [None]*len(self.coordinates)
        new_lat = [None]*len(self.coordinates)
        gps_p_1 = re.compile(r"[NESWnesw][^A-Za-z,，；;]*[0-9][^A-Za-z,，；;]+")  # NSWE 前置经纬度
        gps_p_2 = re.compile(r"[0-9][^A-Za-z,，；;]+[NESWnesw]")  # NSWE 后置经纬度
        gps_p_3 = re.compile(r"[+-]?\d+[\.\d]*")  # 十进制经纬度
        gps_p_num = re.compile(r"[\d\.]+")
        gps_p_NSEW = re.compile(r"[NESWnesw]")
        for i in tqdm(range(len(self.coordinates)), desc="经纬度", ascii=True):
            try:
                gps_elements = gps_p_1.findall(self.coordinates[i])  #提取坐标，并将其列表化，正常情况下将有两个元素组成列表
                if len(gps_elements) != 2:  #通过小数点个数和列表长度初步判断是否是合格的坐标
                    gps_elements = gps_p_2.findall(self.coordinates[i])
                    if len(gps_elements) != 2:
                        gps_elements = gps_p_3.findall(self.coordinates[i])
                        #print(gps_elements)
                        if len(gps_elements) == 2 and abs(float(gps_elements[0])) <= 90 and abs(float(gps_elements[1])) <= 180:
                            new_lng[i] = round(float(gps_elements[1]), 6)
                            new_lat[i] = round(float(gps_elements[0]), 6)
                            continue
                        else:
                            #print(gps_elements ,type(gps_elements[1]))
                            #如果值有错误，则保留原值，如果是数值型值，考虑到已无法恢复，则触发错误不做任何保留                            
                            new_lat[i] = "!" + gps_elements[0]
                            new_lng[i] = "!" + gps_elements[1]
                            continue
                direct_fir = gps_p_NSEW.findall(gps_elements[0])[0]   #单个单元格内，坐标第一个值的方向指示
                direct_sec = gps_p_NSEW.findall(gps_elements[1])[0]  #单个单元格内，坐标第二个值的方向指示
                gps_fir_num = gps_p_num.findall(gps_elements[0])  #获得由坐标中的度分秒值组成的数列
                gps_sec_num = gps_p_num.findall(gps_elements[1])
                #print(i, " ", direct_fir, direct_sec, gps_fir_num, gps_sec_num)
                if direct_fir in "NSns" and direct_sec in "EWew" and float(gps_fir_num[0]) <= 90 and float(gps_sec_num[0]) <= 180:  #判断哪一个数值是纬度数值，哪一个数值是经度数值
                    direct_fir_seq = 1
                elif direct_fir in "EWew" and direct_sec in "NSns" and float(gps_sec_num[0]) <= 90 and float(gps_fir_num[0]) <= 180:
                    direct_fir_seq = 0
                else:
                    new_lng[i] = "!" + gps_elements[1]
                    new_lat[i] = "!" + gps_elements[0]
                    continue
                direct = {"N":1, "S":-1, "E":1, "W":-1, "n":1, "s":-1, "e":1, "w":-1}
                if len(gps_fir_num) == 3 and len(gps_sec_num) == 3:
                    if int(gps_fir_num[1]) >= 60:
                        new_lng[i] = "!" + gps_elements[1]
                        new_lat[i] = "!" + gps_elements[0]
                        continue
                    if float(gps_fir_num[2]) >= 60 or float(gps_sec_num[2]) >= 60:  #度分表示法写成了度分秒表示法
                        if direct_fir_seq == 1:
                            new_lat[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + float(gps_fir_num[1] + "." + gps_fir_num[2])/60, 6)
                            new_lng[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + float(gps_sec_num[1] + "." + gps_sec_num[2])/60, 6)
                        else:
                            new_lng[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + float(gps_fir_num[1] + "." + gps_fir_num[2])/60, 6)
                            new_lat[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + float(gps_sec_num[1] + "." + gps_sec_num[2])/60, 6)
                    else:                                                                        #度分秒表示法
                        if direct_fir_seq == 1:
                            new_lat[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + int(gps_fir_num[1])/60 + float(gps_fir_num[2])/3600, 6)
                            new_lng[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + int(gps_sec_num[1])/60 + float(gps_sec_num[2])/3600, 6)
                        else:
                            new_lng[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + int(gps_fir_num[1])/60 + float(gps_fir_num[2])/3600, 6)
                            new_lat[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + int(gps_sec_num[1])/60 + float(gps_sec_num[2])/3600, 6)
                elif len(gps_fir_num) == 2 and len(gps_sec_num) == 2:             #度分表示法
                    if float(gps_fir_num[1]) >= 60:
                        new_lng[i] = "!" + gps_elements[1]
                        new_lat[i] = "!" + gps_elements[0]
                        continue
                    if direct_fir_seq ==1:
                        new_lat[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + float(gps_fir_num[1])/60, 6)
                        new_lng[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + float(gps_sec_num[1])/60, 6)
                    else:
                        new_lng[i] = direct[direct_fir]*round(int(gps_fir_num[0]) + float(gps_fir_num[1])/60, 6)
                        new_lat[i] = direct[direct_sec]*round(int(gps_sec_num[0]) + float(gps_sec_num[1])/60, 6)
                elif len(gps_fir_num) == 1 and len(gps_sec_num) == 1:            #度表示法
                    if direct_fir_seq ==1:
                        new_lat[i] = direct[direct_fir]*round(float(gps_fir_num[0]), 6)
                        new_lng[i] = direct[direct_sec]*round(float(gps_sec_num[0]), 6)
                    else:
                        new_lng[i] = direct[direct_fir]*round(float(gps_fir_num[0]), 6)
                        new_lat[i] = direct[direct_sec]*round(float(gps_sec_num[0]), 6)
                elif len(gps_fir_num) < 4 and len(gps_sec_num) < 4:  #处理度分/度分秒表示法中，纬度、经度最后一项正好为0被省略导致经纬度不等长的问题
                    if False not in [f() for f in [(lambda i=i:float(i)<60) for i in gps_fir_num[1:]+gps_sec_num[1:]]]:
                        if (lambda n = min(gps_fir_num, gps_sec_num)[-1]:"." not in n)():
                            if direct_fir_seq == 1:
                                new_lat[i] = direct[direct_fir]*round(sum([float(gps_fir_num[i])/pow(60, i) for i in range(len(gps_fir_num))]),6)
                                new_lng[i] = direct[direct_sec]*round(sum([float(gps_sec_num[i])/pow(60, i) for i in range(len(gps_sec_num))]),6)
                            else:
                                new_lng[i] = direct[direct_fir]*round(sum([float(gps_fir_num[i])/pow(60, i) for i in range(len(gps_fir_num))]),6)
                                new_lat[i] = direct[direct_sec]*round(sum([float(gps_sec_num[i])/pow(60, i) for i in range(len(gps_sec_num))]),6)
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
                             "decimalLatitude":self.lat, 
                             "decimalLongitude":self.lng
                             })


class  DateTime:
    def __init__(self, datetime):
        self.datetime  = list(datetime)

    def format_datetime(self):
        #print(self.datetime)
        dmy_pattern = re.compile(r"[A-Za-z]+|[0-9]+")
        alias_map = {"JAN":1, "FEB":2, "MAR":3, "APR":4, "APRI":4, "MAY":5, "JUN":6, "JUL":7, "AUG":8, "SEP":9, "SEPT":9, 
                        "OCT":10, "NOV":11, "DEC":12,"Jan":1, "Feb":2, "Mar":3, "Apr":4, "Apri":4, "May":5, "Jun":6, "Jul":7, 
                        "Aug":8, "Sep":9, "Sept":9, "Oct":10, "Nov":11, "Dec":12, "January":1, "February":2, "March":3, "April":4, 
                        "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12, "I":1, "II":2, 
                        "III":3, "IV":4, "V":5, "VI":6, "VII":7, "VIII":8, "IX":9, "X":10, "XI":11, "XII":12}
        for j in tqdm(range(len(self.datetime)), desc="日期处理", ascii=True):
            try:
                timestamp = time.strptime(self.datetime[j], "%Y-%m-%d %H:%M:%S")
            except (TypeError,ValueError):
                #对日期字符串的数值进行拆分提取
                try:
                    date_elements = dmy_pattern.findall(self.datetime[j])
                    if date_elements == []:
                        self.datetime[j] = None
                        continue
                except (TypeError, ValueError):
                    self.datetime[j] = None
                    continue
                date_degree = len(date_elements)
                if date_degree == 6:
                    date_degree = 3
                    date_elements = date_elements[0:3]
                elif date_degree == 1:
                    temp = date_elements[0]
                    if len(temp) == 6:
                        date_degree = 2
                        date_elements[0] = temp[0:4]
                        date_elements.append(temp[4:6])
                    elif len(temp) == 8:
                        date_degree = 2
                        date_elements[0] = temp[0:4]
                        date_elements.append(temp[4:6])
                        if temp[6:8] != "00":
                            date_degree = 3
                            date_elements.append(temp[6:8])

                year, month, day = [], [], []
                HMS = " 00:00:00"
                # 获取单个日期的年月日值，如果单个日期的年月日值有不同的拼写法，则全部转换成整型
                for i in range(date_degree):
                    try:
                        date_elements[i] = int(date_elements[i])
                    except ValueError:
                        #print(date_elements)
                        if date_elements[i] in alias_map:
                            date_elements[i] = alias_map[date_elements[i]]
                        else:
                            self.datetime[j] = "!" + self.datetime[j]
                            break
                if self.datetime[j][0] == "!":
                    continue
                else:
                    # 判断年月日的数值是否符合规范&判断各数值是 年 月 日 中的哪一个
                    for k in range(date_degree):
                        element = date_elements[k]
                        if date_degree == 3:
                            if k == 1:
                                month = element
                            elif element > 2099:
                                self.datetime[j] = "!" + self.datetime[j]
                                break
                            elif element > 999:
                                year = element
                            elif element >31:
                                year = 1900 + element%100
                            elif year != []:
                                day = element
                            elif date_elements[2] > 31:
                                day = element
                            else:
                                self.datetime[j] = "!" + self.datetime[j]
                                break
                        elif date_degree == 2:
                            if element > 2099:
                                self.datetime[j] = "!" + self.datetime[j]
                                break
                            elif element > 999:
                                year = element
                            elif element > 31:
                                year = element%100 + 1900
                            elif element > 12:
                                if year != []:
                                    self.datetime[j] = "!" + self.datetime[j]
                                    break
                                elif month != []:
                                    year = 1900 + element
                                elif date_elements[1] < 13:
                                    year = 1900 + element
                                else:
                                    self.datetime[j] = "!" + self.datetime[j]
                                    break
                            elif element > 0:
                                if year != []:
                                    month = element
                                elif date_elements[1] > 12:
                                    month = element
                                else:
                                    self.datetime[j] = "!" + self.datetime[j]
                                    break
                            else:
                                self.datetime[j] = "!" + self.datetime[j]
                                break
                        elif date_degree ==1:
                            if element > 2099:
                                self.datetime[j] = "!" + self.datetime[j]
                                break
                            elif element > 999:
                                year = element
                            elif element > 31:
                                year = 1900 + element%100
                            else:
                                self.datetime[j] = "!" + self.datetime[j]
                        else:
                            self.datetime[j] = "!" + self.datetime[j]
                            break
                    if self.datetime[j][0] == "!":
                        continue
                    else:
                        if day == []:
                            day = 1
                            HMS = " 00:00:01"
                        if month == []:
                            month =1
                            HMS = " 00:00:02"
                        try:  # 判断该日期是否真实存在
                            date(year,month,day)
                            self.datetime[j] = str(year) + "-" + str(month) + "-" + str(day) + HMS
                        except ValueError:
                            self.datetime[j] = "!" + self.datetime[j]
                            continue
                timestamp = time.strptime(self.datetime[j], "%Y-%m-%d %H:%M:%S")

            if date(timestamp[0], timestamp[1], timestamp[2]) > date.today():
                self.datetime[j] = "!" + self.datetime[j]
            else:
                continue
        return self.datetime

    
    def __call__(self):
        return pd.DataFrame({"dateTime":self.format_datetime()})


class HumanName:
    def __init__(self, names):
        self.names = names
    
    def format_names(self):
        """
        返回以英文逗号分隔的人名字符串，可中英文人名混排“徐洲锋,A. Henry,徐衡”，并以 
        “!“ 标识可能错误写法的字符串，注意尚无法处理“徐洲锋 洪丽林 徐衡” 这样以空格切
        分的中文人名字符串
        """
        names_mapping = dict.fromkeys(self.names)
        pattern = re.compile(r'[\u4e00-\u9fa5\s]*[\u4e00-\u9fa5][\|\d]*|[A-Za-z][A-Za-z\.\s\-]+[a-z][\|\d]*')
        for rec_names in tqdm(names_mapping, desc="人名处理", ascii=True):
            try:
                names = [name.strip().title() for name in pattern.findall(rec_names)]
                for i, name in enumerate(names):
                    if re.search(r"[a-z\u4e00-\u9fa5]\|\d", name):
                        pass
                    elif not re.search(r"[\|\d]", name):
                        pass
                    else:
                        raise ValueError
                    if re.search(u"[\u4e00-\u9fa5]", name):
                        if len(name)<2:
                            raise ValueError
                        else:
                            names[i] = name.replace(" ", "")
                    else:
                        if len(name) < 3:
                            raise ValueError
                        else:
                            en_name = [e + "." if len(e)==1 else e for e in re.split(r"\.\s*", name)]
                            names[i] = " ".join(en_name)
                names_mapping[rec_names] = ", ".join(names)
            except:
                if pd.isnull(rec_names):
                    continue
                else:
                    names_mapping[rec_names] = "!" + str(rec_names)

        return [names_mapping[txt] for txt in self.names]


    def __call__(self):
        return pd.DataFrame(pd.Series(self.format_names()))


class RadioInput:
    def __init__(self, column, title):
        self.column = column
        self.title = title
    
    def format_option(self):
        options_mapping = dict.fromkeys(self.column)
        with open(os.path.dirname(__file__) + "/./std_options_alias.json", "r", encoding="utf-8") as o:
            std2alias = json.load(o)
        std_titles = sorted(list(std2alias[self.title].keys()))
        mana2std = []
        for option in tqdm(options_mapping, desc=self.title, ascii=True):
            if option in std_titles:
                options_mapping[option] = option
            else:
                for k, v in std2alias[self.title].items():
                    if option in v:
                        options_mapping[option] = k
                        break
                if options_mapping[option] is None:
                    if pd.isnull(option):
                        continue
                    else:
                        mana2std.append(option)
        # 手动指定无法自动匹配的可选值
        if mana2std:
            print("\n{0} 内有 {1} 个值需要逐个手动指定，手动指定请输入 1 ，全部忽略请输入 0：\n".format(self.title, len(mana2std)))
            for option in mana2std:
                print("".join(["\n\n", str(option), "=>请将该值对应至以下可选值中的某一个:\n"]))
                for n, m in enumerate(std_titles):
                    strings = str(n+1) + ". " + m
                    if (n+1)%3 > 0:
                        print(strings.ljust(25), end="\t")
                    else:
                        print(strings.ljust(25), end="\n\n")
                while True:
                    n = input("\n\n请输入对应的阿拉伯数字，无法对应请输入 0 :\n\n")
                    if n == '0':
                        options_mapping[option] = "!" + option
                        break
                    else:
                        try:
                            std2alias[self.title][std_titles[int(n)-1]].append(option)
                            options_mapping[option] = std_titles[int(n)-1]
                            break
                        except:
                            print("\n输入的字符有误...\n")

            with open(os.path.dirname(__file__) + "/./std_options_alias.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(std2alias, ensure_ascii=False))

        return [options_mapping[w] for w in self.column]
            

    def __call__(self):
        return pd.DataFrame(pd.Series(self.format_option()))


class UniqueID:
    def __init__(self, *columns):
        # columns 可以包含多个数据列联合判重
        self.df = pd.concat(columns, axis=1)
    
    def mark_duplicate(self):
        self.duplicated = self.df.duplicated(keep=False)
        marks = ["".join(["!", m]) if d and not pd.isnull(m) else m for m, d in zip(self.df[self.df.columns[0]], self.duplicated)]
        return marks
    
    def __call__(self):
        self.df[self.df.columns[0]] = self.mark_duplicate()
        return self.df


class FillNa:
    def __init__(self, df:"Series or DataFrame isinstance", fval):
        self.df = df
        self.fval = fval

    def __call__(self):
        return pd.DataFrame(self.df.fillna(self.fval))


if __name__ == "__main__":
    table = pd.read_excel(r"/Users/xuzhoufeng/Downloads/lbg-不合格.xlsx")
    names = BioName(table["学名"])
    start = time.time()
    stdnames = names.run()
    end = time.time()
    print("Execution Time: ", end - start)


# KEW API beta
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Glycine+&f=f_generic
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Lauraceae+&f=f_familial
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Glycine+max&f=f_specific
# http://beta.ipni.org/api/1/search?perPage=500&cursor=%2A&q=Thalictrum+aquilegiifolium+var.+sibiricum&f=f_infraspecific

# sp2000.org.cn API V1
# http://www.sp2000.org.cn/api/family/familyName/familyID/Poaceae/42ad0f57ae46407686d1903fd44aa34c
# http://www.sp2000.org.cn/api/taxon/familyID/taxonID/F20171000000256/42ad0f57ae46407686d1903fd44aa34c
# http://www.sp2000.org.cn/api/taxon/scientificName/taxonID/Poaceae%20annua/42ad0f57ae46407686d1903fd44aa34c
# http://www.sp2000.org.cn/api/taxon/commonName/taxonID/早熟禾/42ad0f57ae46407686d1903fd44aa34c
# http://www.sp2000.org.cn/api/taxon/species/taxonID/T20171000041825/42ad0f57ae46407686d1903fd44aa34c


# sp2000.org.cn API V2
# http://www.sp2000.org.cn/api/v2/getFamiliesByFamilyName?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyName=Lauraceae&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByFamilyId?apiKey=42ad0f57ae46407686d1903fd44aa34c&familyId=F20171000000256&page=2
# http://www.sp2000.org.cn/api/v2/getSpeciesByScientificName?apiKey=42ad0f57ae46407686d1903fd44aa34c&scientificName=Rhododendron%20delavayi&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByCommonName?apiKey=42ad0f57ae46407686d1903fd44aa34c&commonName=%E6%97%A9%E7%86%9F%E7%A6%BE&page=1
# http://www.sp2000.org.cn/api/v2/getSpeciesByNameCode?apiKey=42ad0f57ae46407686d1903fd44aa34c&nameCode=T20171000041825&page=1
