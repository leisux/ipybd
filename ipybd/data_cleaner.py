import asyncio
import json
import os
import re
import urllib
from datetime import date
from types import FunctionType, MethodType
from typing import Union

import aiohttp
import arrow
import pandas as pd
import requests
from tqdm import tqdm

from ipybd.api_terms import Filters

HERE = os.path.dirname(__file__)
STD_OPTIONS_ALIAS_PATH = os.path.join(HERE, 'lib', 'std_options_alias.json')
ADMIN_DIV_LIB_PATH = os.path.join(HERE, 'lib', 'chinese_admin_div.json')

SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'http://beta.ipni.org/api/1'
POWO_API = 'http://www.plantsoftheworldonline.org/api/2'


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
                except (AttributeError, TypeError):
                    return obj(*args, **kwargs)
        return handler
    elif isinstance(obj, MethodType):
        pass
    else:
        raise ValueError('model value error: {}'.format(obj))


@ifunc
class BioName:
    def __init__(self, names: Union[list, pd.Series, tuple], style='scientificName'):
        self.names = names
        self.querys = {}
        self.cache = {'ipni': {}, 'col': {}, 'powo': {}}
        self.style = style

    def get(self, action, typ=list, mark=False):
        if self.querys == {}:
            self.querys = self.build_querys()
        results = self.__build_cache_and_get_results(action)
        if results:
            if typ is list:
                return self._results2list(results, mark)
            elif typ is dict:
                return results
        else:
            if typ is list:
                return []
            elif typ is dict:
                return {}

    def _results2list(self, results: dict, mark):
        """ 对 get 的结果进行组装

        results: 从 self.cache 中解析得到的结果字典, 每个元素都为元组
        mark: 如果为 True，没有获得结果的检索词会被虽结果返回并以!标记
              如果为 None，没有检索结果则返回由 None 组成的与其他结果等长的元组

        return: 按照 self.names 中的元素顺序排列的检索结果 list，list 中的元素
                由元组组成。
        """

        result_len = len(list(results.values())[0])
        for name in self.querys:
            if mark:
                # 无法格式化的/检索无结果的原值，用英文!标注
                if self.querys[name] is None or name not in results:
                    try:
                        results[name] = ["".join(["!", name])]
                    except TypeError:
                        if name:
                            # 如果 name 不是 None, 说明检索词有错误
                            results[name] = ["".join(["!", str(name)])]
                        else:
                            results[name] = [None]
                    results[name].extend([None]*(result_len - 1))
            else:
                if self.querys[name] is None or name not in results:
                    results[name] = [None] * result_len
            results[name] = tuple(results[name])
        return [results[w] for w in self.names]

    # 以下多个方法用于组装 get 协程
    # 跟踪协程的执行，并将执行结果生成缓存

    def __build_cache_and_get_results(self, action, need_querys=None):
        """ 构建查询缓存、返回查询结果

        action: 要进行的查询操作描述字符串
        need_querys: 没有缓存，需要进行 WEB 查询的检索词
                     由 self.querys 部分元素组成解字典

         返回检索结果字典 results，字典由原始检索词:检索结果组成
               若没有任何结果，返回 {}
               检索过程中，会一并生成 self.names 在相应平台的检索返回内容缓存
        """
        cache_mapping = {
            'stdName': {
                **self.cache['col'],
                **self.cache['ipni']},
            'colTaxonTree': self.cache['col'],
            'colName': self.cache['col'],
            'colSynonyms': self.cache['col'],
            'ipniName': self.cache['ipni'],
            'ipniReference': self.cache['ipni'],
            'powoName': self.cache['powo'],
            'powoAccepted': self.cache['powo'],
            'powoImages': self.cache['powo']}
        results = {}
        cache = cache_mapping[action]
        if cache:
            if need_querys:
                names = need_querys
            else:
                names = self.querys
            action_func = {
                # 注意 stdName 的 col 函数置于元组最后，
                # 以避免 ipni/powo 中与 col 同名的字段
                # 被 col 函数解析。
                'stdName': (self.ipni_name, self.col_name),
                'colTaxonTree': self.col_taxontree,
                'colName': self.col_name,
                'colSynonyms': self.col_synonyms,
                'ipniName': self.ipni_name,
                'ipniReference': self.ipni_reference,
                'powoName': self.powo_name,
                'powoAccepted': self.powo_accepted,
                'powoImages': self.powo_images
            }
            # 如果存在缓存，则直接从缓存数据中提取结果
            # 如果没有缓存，则先生成缓存，再取数据
            search_terms = {}
            for org_name, query in names.items():
                try:
                    results[org_name] = self.get_cache_result(
                        cache[org_name],
                        action_func[action]
                    )
                except KeyError:
                    # 缓存中不存在 org_name 检索结果时触发
                    if query:
                        # 如果检索词是合法的，加入检索项
                        search_terms.update({org_name: query})
                except ValueError:
                    # 如果有检索结果，但缓存结果中相应结果不存在特定数据
                    # 则不写入 results
                    pass
        else:
            if not need_querys:
                # 如果没有缓存，所有检索词执行一次 web 搜索
                search_terms = self.querys
        # 未防止 search_terms 不存在，这里的条件判断应放置在后面
        if not need_querys and search_terms:
            # 若need_querys 是 None, 说明 web 请求是首次发起，执行一次递归检索
            # 若search_terms 并非 self.querys，说明 get 请求是由程序本身自动发起
            # 执行结束后，将不再继续执行递归
            self.web_get(action, search_terms)
            # 这里的递归最多只执行一次
            sub_results = self.__build_cache_and_get_results(
                action, search_terms)
            results.update(sub_results)
        return results

    def get_cache_result(self, query_result, get_result):
        """ 从检索缓存中提取数据

        query_result: raw_name 的检索结果
        get_result: 从检索结果中提取特定检索结果的方法，
                    可能是一个方法，也可能是多个方法组成的元组
        return: 返回的结果样式，由检索方法决定

        """
        try:
            return get_result(query_result)
        # func 是 tuple 时触发
        except TypeError:
            for func in get_result:
                try:
                    # 遇到首个有正常返回值后，停止循环
                    return self.get_cache_result(query_result, func)
                    break
                # 若多个 API 返回结果的 keys 通用，这里可能不会触发 KeyError,目
                # 前已知 col 和 ipni/powo 部分keys 通用，且 col 不存在属查询，
                # family 检索和 species 返回的数据结构也不一致，因此其内部需要
                # 处理相关 KeyError 错误，与这里的处理会有冲突，因此该函数 func
                # 中 col 的处理函数应该至于最后，以避免 ipni/powo 的数据被 col
                # 处理函数处理。
                except KeyError:
                    continue

    def web_get(self, action, search_terms):
        """ 检索 WEB API，获得名称检索结果

        action: str 类型，用于说明要执行的操作
        search_terms: 搜索条件, 由self.querys 的全部或部分元素组成的字典
                      元素样式为：raw_name:(simpleName, rank ,author, raw_name)
        return: 返回 None, 检索结果会直接写入 self.cache
        """
        get_action = {
            'stdName': self.get_name,
            'colTaxonTree': self.get_col_name,
            'colName': self.get_col_name,
            'colSynonyms': self.get_col_name,
            'ipniName': self.get_ipni_name,
            'ipniReference': self.get_ipni_name,
            'powoName': self.get_powo_name,
            'powoAccepted': self.get_powo_name,
            'powoImages': self.get_powo_name
        }
        self.pbar = tqdm(total=len(search_terms), desc=action, ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sema = asyncio.Semaphore(500, loop=loop)
        tasks = self.build_tasks(get_action[action], search_terms)
        results = loop.run_until_complete(tasks)
        loop.close()
        self.pbar.close()
        for res in results:
            try:
                self.cache[res[-1]][res[0]] = res[1]
            except TypeError:
                pass

    async def build_tasks(self, action_func, search_terms):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.web_get_track(
                    action_func,
                    self.querys[rawname],
                    session
                )
                for rawname in search_terms if self.querys[rawname]
            ]
            return await asyncio.gather(*tasks)

    async def web_get_track(self, func, param, session):
        async with self.sema:
            result = await func(param, session)
            self.pbar.update(1)
            return result

    # 以下多个方法用于对 Api 返回结果进行有针对性的处理
    # 并根据具体调用的方法，返回用户所需要的数据

    def powo_images(self, query_result):
        """ 解析 self.cache['powo'] 中的图片

            powo 接口获得的图片有缩略图和原图 url
            每个名字的图片有且仅有三张
            返回的 iamges 是由三个 url 构成的元组
        """
        try:
            images = [image['fullsize'] for image in query_result['images']]
        except KeyError:
            # 如果结果中没有 images 信息
            # 抛出值错误异常供调用程序捕获
            raise ValueError
        return images

    def powo_accepted(self, query_result):
        try:
            query_result = query_result['synonymOf']
        except KeyError:
            # 如果没有名称处理，默认将本名称作为接受名返回
            # 有些名字可能属于 unsolved 状态，也会被作为接受名返回
            pass
        return " ".join([query_result['name'], query_result['author']]),

    def powo_name(self, query_result):
        scientific_name = query_result["name"]
        author = query_result["author"]
        family = query_result['family']
        return scientific_name, author, family

    def col_synonyms(self, query_result):
        try:
            synonyms = [
                synonym['synonym'] for synonym
                in query_result['accepted_name_info']['Synonyms']
            ]
            return synonyms
        except KeyError:
            raise ValueError

    def col_taxontree(self, query_result):
        try:
            genus = query_result['accepted_name_info']['taxonTree']['genus']
            family = query_result['accepted_name_info']['taxonTree']['family']
            order = query_result['accepted_name_info']['taxonTree']['order']
            _class = query_result['accepted_name_info']['taxonTree']['class']
            phylum = query_result['accepted_name_info']['taxonTree']['phylum']
            kingdom = query_result['accepted_name_info']['taxonTree']['kingdom']
        except KeyError:
            try:
                genus = query_result['genus']
                family = query_result['family']
                order = query_result['order']
                _class = query_result['class']
                phylum = query_result['phylum']
                kingdom = query_result['kingdom']
            except BaseException:
                genus = None
                family = query_result['family']
                order = query_result['order']
                _class = query_result['class']
                phylum = query_result['phylum']
                kingdom = query_result['kingdom']
        return genus, family, order, _class, phylum, kingdom

    def col_name(self, query_result):
        try:  # 种及种下检索结果
            family = query_result['accepted_name_info']['taxonTree']['family']
            author = query_result['accepted_name_info']['author']
            scientific_name = query_result['scientific_name']
        except KeyError:
            try:  # 属的检索结果
                scientific_name = query_result['genus']
                author = None
                family = query_result['family']
            except KeyError:  # 科的检索结果
                family = query_result['family']
                author = None
                scientific_name = family
        return scientific_name, author, family

    def ipni_name(self, query_result):
        scientific_name = query_result["name"]
        author = query_result["authors"]
        family = query_result['family']
        # print(query[-1], genus, family, author)
        return scientific_name, author, family

    def ipni_reference(self,query_result):
        publishing_author = query_result['publishingAuthor']
        publication_year = query_result['publicationYear']
        publication = query_result['publication']
        reference = query_result['reference']
        return publishing_author, publication_year, publication, reference

    async def get_name(self, query, session):
        name = await self.get_col_name(query, session)
        if name:
            return name
        else:
            return await self.get_ipni_name(query, session)

    # 以下多个方法用于请求相应 API 接口
    # 以获取api返回，并对返回结果的合理性做必要的判断

    async def get_col_name(self, query, session):
        name = await self.check_col_name(query, session)
        if name:
            return query[-1], name, 'col'

    async def check_col_name(self, query, session):
        """ 对 COL 返回对结果逐一进行检查

        return: 返回最能满足 query 条件的学名 dict
        """
        results = await self.col_search(query[0], query[1], session)
        # print(results)
        if results is None or results == []:
            return None
        else:
            names = []
            for num, res in enumerate(results):
                if query[1] is Filters.specific or query[1] is Filters.infraspecific:
                    try:
                        if res['scientific_name'] == query[0] and res['accepted_name_info']['author'] != "":
                            # col 返回的结果中，没有 author team，需额外自行添加
                            # 由于 COL 返回但结果中无学名的命名人，因此只能通过
                            # 其接受名的 author 字段获得命名人，但接受名可能与
                            # 检索学名不一致，所以此处暂且只能在确保检索学名为
                            # 接受名后，才能添加命名人。
                            # 因此对于 col 虽有数据，但却是异名的名字，会返回None
                            if res['name_status'] == 'accepted name':
                                results[num]['author_team'] = self.get_author_team(
                                    res['accepted_name_info']['author'])
                                names.append(res)
                    # COL 可能 'accepted_name_info' 属性为None
                    except TypeError:
                        continue
                # col 接口目前尚无属一级的内容返回，这里先取属下种及种
                # 下一级的分类阶元返回。
                elif query[1] is Filters.generic:
                    try:
                        if res['accepted_name_info']['taxonTree']['genus'] == query[0]:
                            return res['accepted_name_info']['taxonTree']
                    except TypeError:
                        continue
                elif query[1] is Filters.familial and res['family'] == query[0]:
                    return res
            authors = self.get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                # print("{0} 在中国生物物种名录中可能是异名、不存在或缺乏有效命名人，请手动核实\n".format(query[-1]))
                return None
            # 检索只有一个结果或者检索词命名人缺失，默认使用第一个同名结果
            elif len(names) == 1 or authors == []:
                name = names[0]
            else:
                # 提取出API返回的多个名称的命名人序列，并将其编码
                aut_codes = self.code_authors(authors)
                std_teams = {
                    n: self.code_authors(r['author_team'])
                    for n, r in enumerate(names)
                }
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_code(aut_codes, std_teams)
                # print(scores)
                name = names[scores[0][1]]
                # if std_teams[scores[0][1]] > 10000000000:
                #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一
                # 组值总有最优,但不一定是真符合
        return name

    async def get_ipni_name(self, query, session):
        name = await self.check_ipni_name(query, session)
        if name:
            return query[-1], name, 'ipni'

    async def check_ipni_name(self, query, session):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        results = await self.kew_search(query[0], query[1], IPNI_API, session)
        if results is None or results == []:
            # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
            return None
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    names.append(res)
            authors = self.get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                # print(query)
                return None
            # 检索只有一个结果，或者检索词缺命名人，默认使用第一个同名结果
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
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_code(aut_codes, std_teams)
                # print(scores)
                name = names[scores[0][1]]
                # if std_teams[scores[0][1]] > 10000000000:
                #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一
                # 组值总有最优，但不一定是真符合
        return name

    async def get_powo_name(self, query, session):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: KEW 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_powo_name(query, session)
        if name:
            return query[-1], name, 'powo'

    async def check_powo_name(self, query, session):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        results = await self.kew_search(query[0], query[1], POWO_API, session)
        if results is None or results == []:
            # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
            return None
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    try:
                        res['authorTeam'] = self.get_author_team(res['author'])
                    except KeyError:
                        # 如果查询的结果中没有命名人信息,则补充空值
                        # 如果匹配结果只有这一个结果，采用该结果
                        # 如果匹配结果多余一个，该结果将因 autorTeam 为空排除
                        res['author'] = None
                        res['authroTeam'] = []
                    names.append(res)
            authors = self.get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                # print(query)
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
                std_teams = {
                    n: self.code_authors(
                        r['authorTeam']) for n,
                    r in enumerate(names) if r['authorTeam']}
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_code(aut_codes, std_teams)
                # print(query[-1], scores)
                name = names[scores[0][1]]
                # if std_teams[scores[0][1]] > 10000000000:
                #   author = ...这里可以继续对最优值进行判断和筛选，毕竟一组值总有最优，
                # 但不一定是真符合
        return name

    async def col_search(self, query, filters, session):
        params = self._build_col_params(query, filters)
        url = self.build_url(SP2000_API, filters.value['col'], params)
        # print(url)
        resp = await self.async_request(url, session)
        # print(resp)
        try:
            if resp['code'] == 200:
                try:
                    # 先尝试返回种及种下物种的信息
                    return resp['data']['species']
                except KeyError:
                    # 出错后，确定可以返回科的信息
                    return resp['data']['familes']
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
            return None

    async def kew_search(self, query, filters, api, session):
        params = self._build_kew_params(query, filters)
        resp = await self.async_request(self.build_url(api, 'search', params), session)
        try:
            return resp['results']
        except (TypeError, KeyError):
            return None

    async def async_request(self, url, session):
        try:
            while True:
                # print(url)
                async with session.get(url, timeout=60) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(3)
                    else:
                        response = await resp.json()
                        # print(response)
                        break
        except BaseException:  # 如果异步请求出错，改为正常的 Get 请求以尽可能确保有返回结果
            response = await self.normal_request(url)
        if not response:
            print(url, "联网超时，请检查网络连接！")
        return response  # 返回 None 表示网络有问题

    async def normal_request(self, url):
        try:
            while True:
                rps = requests.get(url)
                # print(rps.status_code)
                if rps.status_code == 429:
                    await asyncio.sleep(3)
                else:
                    return rps.json()
        except BaseException:
            return None

    def _build_col_params(self, query, filters):
        params = {'apiKey': '42ad0f57ae46407686d1903fd44aa34c'}
        if filters is Filters.familial:
            params['familyName'] = query
        elif filters is Filters.commonname:
            params['commonName'] = query
        else:
            params['scientificName'] = query
        params['page'] = 1
        return params

    def _build_kew_params(self, query, filters):
        params = {'perPage': 500, 'cursor': '*'}
        if query:
            params['q'] = self._format_kew_query(query)
        if filters:
            params['f'] = self._format_kew_filters(filters)
        return params

    def build_url(self, api, method, params):
        return '{base}/{method}?{opt}'.format(
               base=api,
               method=method,
               opt=urllib.parse.urlencode(params)
        )

    def _format_kew_query(self, query):
        if isinstance(query, dict):
            terms = [k.value + ':' + v for k, v in query.items()]
            return ",".join(terms)
        else:
            return query

    def _format_kew_filters(self, filters):
        if isinstance(filters, list):
            terms = [f.value['kew'] for f in filters]
            return ",".join(terms)
        else:
            return filters.value['kew']

    def build_querys(self):
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            split_name = self._format_name(raw_name)
            if split_name is None:
                raw2stdname[raw_name] = None
                continue
            else:
                if split_name[2] == "" and split_name[3]:
                    simple_name = ' '.join([split_name[0], split_name[1], split_name[3]]).strip()
                else:
                    simple_name = ' '.join(split_name[:4]).strip()
                raw2stdname[raw_name] = simple_name, split_name[-2], split_name[4], split_name[-1]
        return raw2stdname

    def format_latin_names(self, pattern):
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            split_name = self._format_name(raw_name)
            if split_name is None:
                raw2stdname[raw_name] = None
                continue
            if pattern == 'simpleName':
                if split_name[2] == "" and split_name[3]:
                    simple_name = ' '.join([split_name[0], split_name[1], split_name[3]]).strip()
                else:
                    simple_name = ' '.join(split_name[:4]).strip()
                raw2stdname[raw_name] = simple_name
            elif pattern == 'scientificName':
                if split_name[2] == "" and split_name[3]:
                    simple_name = ' '.join([split_name[0], split_name[1], split_name[3]]).strip()
                else:
                    simple_name = ' '.join(split_name[:4]).strip()
                author = split_name[4]
                raw2stdname[raw_name] = ' '.join([simple_name, author]) if author else simple_name
            elif pattern == 'plantSplitName':
                raw2stdname[raw_name] = split_name[:-2]
            elif pattern == 'animalSplitName':
                raw2stdname[raw_name] = (split_name[0], split_name[1], split_name[3], split_name[4])
            else:
                raise ValueError("学名处理参数错误，不存在{}".format(pattern))
        return [raw2stdname[name] for name in self.names]

    def _format_name(self, raw_name):
        """ 将手写学名转成规范格式

            raw_name: 各类动植物学名，目前仅支持:
                      属名 x 种名 种命名人 种下加词 种下命名人
                      这类学名格式的清洗，
                      其中杂交符、种命名人、种下命名人均可缺省。
            return: 去除命名人的各个组成部分, Filters定义的学名等级, 原始名称提取的命名人, raw_name
                    目前仍有个别命名人十分复杂的名称，无法准确提取命名人，使用时需注意
                    如果无法提取合法的学名，则返回 None
        """
        species_pattern = re.compile(
            r"(!?\b[A-Z][a-zàäçéèêëöôùûüîï-]+)\s*([×Xx])?\s*([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s*(.*)")
        subspecies_pattern = re.compile(
            r"\b([A-Z\(].*?[^A-Z])?\s*(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form|cv\.|cultivar\.)?\s*\b([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)\s*([（A-Z\(].*?[^A-Z])?$")
        try:
            species_split = species_pattern.findall(raw_name)[0]
        except BaseException:
            return None
        subspec_split = subspecies_pattern.findall(species_split[3])

        genus = species_split[0]
        if species_split[1] == "":
            species = species_split[2]
        else:
            species = " ".join([species_split[1], species_split[2]])
        if subspec_split == []:
            author = species_split[3]
            taxon_rank = ""
            infraspecies = ""
            if species_split[2] != "":
                platform_rank = Filters.specific
            elif genus.lower().endswith((
                "aceae", "idae", "umbelliferae", "labiatae", "compositae", "gramineae",
                    "leguminosae")):
                platform_rank = Filters.familial
            else:
                platform_rank = Filters.generic
        else:
            taxon_rank = subspec_split[0][1]
            infraspecies = subspec_split[0][2]
            author = subspec_split[0][3]
            platform_rank = Filters.infraspecific
        return genus, species, taxon_rank, infraspecies, author, platform_rank, raw_name

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
                    scores.append(max(author, name) % min(author, name))
                # 每个人名取匹配度分数最低的分值
                k_score.append(min(scores))
            std_codes[k] = (
                sum(k_score)//len(raw_code)+1)*2**abs(len(raw_code)-len(authorship))
        # 开始从比对结果中，结果将取命名人偏差最小的API返回结果
        # std_teams 中可能存在多个最优，而程序无法判定采用哪一个比如原始数据
        # 命名人为 (A. K. Skvortsov et Borodina) A. J. Li，而 ipni 返回的标准
        # 名称中存在命名人分别为 A. K. Skvortsov 和 Borodina et A. J. Li 两个
        # 同名学名，其 std_teams 值都将为最小偏差值 0，
        # 此时程序将任选一个其实这里也可以考虑将其标识，等再考虑考虑，
        # 有的时候ipni数据也有可能有错，比如 Phaeonychium parryoides 就存在这
        # 个问题，但这种情况应该是小比率，对于结果的帅选逻辑，可以修改下方逻辑
        scores = [(x, y) for y, x in std_codes.items()]
        scores.sort(key=lambda s: s[0])
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
                elif aut[i-1] == letter and i != 0:  # 避免前后字母序号相减等于 0
                    pass
                elif n < 91:  # 人名中的大写字母
                    code_author = code_author * (ord(letter)-64)
                elif aut[i-1] == " " and n > 96:  # 人名之中的小写首字母
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
        p4 = re.compile(
            r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+")
        p3 = re.compile(
            r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+\s+[A-Z][A-Za-z\.]+")
        p2 = re.compile(r"\b[A-Z][A-Za-z\.-]+\s+[A-Z][A-Za-z\.]+")
        p1 = re.compile(r"\b[A-Z][A-Za-z\.-]+")
        author_team = []
        for p in (p4, p3, p2, p1):
            aus = p.findall(authors)
            author_team = author_team + aus
            for author in aus:
                authors = authors.replace(author, "", 1)
        return author_team

    def __call__(self, mark=True):
        if input("是否有必须对学名做进一步的处理？（y/n）\n") == 'y':
            pass
        elif self.style == 'plantSplitName':
            return pd.DataFrame(self.format_latin_names(pattern="plantSplitName"))
        elif self.style == 'animalSplitName':
            return pd.DataFrame(self.format_latin_names(pattern="animalSplitName"))
        else:
            return pd.DataFrame(self.names)
        if self.style == 'scientificName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 sp2000.org.cn、ipni.org 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            ' '.join([name[0], name[1]]).strip()
                            if name[1] else name[0]
                            for name in results
                        ]
                    )
                else:
                    return pd.DataFrame([None] * len(self.names))
            else:
                return pd.DataFrame(self.format_latin_names(pattern="scientificName"))
        elif self.style == 'simpleName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 sp2000.org.cn、ipni.org 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            name[0].strip()
                            if name[1] else name[0]
                            for name in results
                        ]
                    )
                else:
                    return pd.DataFrame([None]*len(self.names))
            else:
                return pd.DataFrame(self.format_latin_names(pattern="simpleName"))
        elif self.style == 'plantSplitName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 sp2000.org.cn、ipni.org 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            self._format_name(name[0].strip())[:4] + (name[1],)
                            if name[1] else self._format_name(name[0].strip())[:-2]
                            for name in results
                        ]
                    )
                else:
                    return pd.DataFrame([[None, None, None, None, None]] * len(self.names))
            else:
                return pd.DataFrame(self.format_latin_names(pattern="plantSplitName"))
        else:
            raise ValueError("学名处理参数有误，不存在{}".format(self.style))


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
    def __init__(self, names: Union[list, pd.Series, tuple]):
        self.names = names

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
                names_mapping[rec_names] = ", ".join(names)
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
        for stdregion in std_regions:
            each_score = 0  # 记录累计匹配的字数
            i = 0  # 记录 region 参与匹配的起始字符位置
            j = 0  # 记录 stdregion 参与匹配的起始字符位置
            while i < len(region)-1 and j < len(stdregion)-1:  # 单字无法匹配
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
                # 优先匹配短的行政区，避免“河北”匹配“中国,天津,天津市,河北区“
                elif len(stdregion) < score[1]:
                    score = each_score, len(stdregion)
                    self.region_mapping[raw_region] = "!"+stdregion
            elif each_score > score[0]:
                score = each_score, len(stdregion)
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
                 typ=float, min_num=0, max_num=8848):
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
        care: 对于“-20-30“ 的值，无法准确划分为 -20和30，会被划分为 20和30
        """
        pattern = re.compile(r"^[+-]?\d+[\.\d]*|\d+[\.\d]*")
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
            return pd.DataFrame(new_column, dtype=typ)
        except ValueError:
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
        options_mapping = dict.fromkeys(self.column)
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
                if not options_mapping[option]:
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
                            options_mapping[option] = "!" + option
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
            "".join(["!", m]) if d and not pd.isnull(m) else m
            for m, d in zip(self.df[self.df.columns[0]], self.duplicated)
        ]
        return marks

    def __call__(self):
        self.df[self.df.columns[0]] = self.mark_duplicate()
        return self.df


@ifunc
class FillNa:
    def __init__(self, df: Union[pd.DataFrame, pd.Series], fval):
        self.df = df
        self.fval = fval

    def __call__(self):
        return pd.DataFrame(self.df.fillna(self.fval))


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
