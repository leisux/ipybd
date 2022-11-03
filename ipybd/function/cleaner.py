import asyncio
from email.errors import NoBoundaryInMultipartDefect
import json
import os
import re
import unicodedata
import urllib
from datetime import date
from types import FunctionType, MethodType
from typing import Union
import warnings

import aiohttp
import arrow
import pandas as pd
import requests
from ipybd.function.api_terms import Filters
from thefuzz import fuzz, process
from tqdm import tqdm


PARENT_PATH = os.path.dirname(os.path.dirname(__file__))
STD_OPTIONS_ALIAS_PATH = os.path.join(PARENT_PATH, 'lib', 'std_options_alias.json')
ADMIN_DIV_LIB_PATH = os.path.join(PARENT_PATH, 'lib', 'chinese_admin_div.json')

SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'http://beta.ipni.org/api/1'
POWO_API = 'https://powo.science.kew.org/api/2'
TROPICOS_API = 'https://services.tropicos.org/Name'


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
        self.cache = {'ipni': {}, 'col': {}, 'powo': {}, 'tropicosName': {}, 'tropicosAccepted': {}, 'tropicosSynonyms': {}}
        self.style = style

    def get(self, action, typ=list, mark=False):
        if self.querys == {}:
            self.querys = self.build_querys()
        if isinstance(action, str):
        # results 只包含有检索有结果的
            results = self.__build_cache_and_get_results(action)
        else:
            results = self.native_get(self.querys, action)
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
        mark: 如果为 True，没有获得结果的检索词会被当成结果返回并以!标记
              如果为 None，没有检索结果则返回由 None 组成的与其他结果等长的元组

        return: 按照 self.names 中的元素顺序排列的检索结果 list，list 中的元素
                由元组组成。
        """

        result_len = len(list(results.values())[0])
        for name in self.querys:
            if mark:
                # 无法格式化的/检索无结果/检索失败，用英文!标注
                if self.querys[name] is None or name not in results or results[name] is None:
                    try:
                        results[name] = ["".join(["!", name])]
                    except TypeError:
                        if pd.isnull(name):
                            results[name] = [None]
                        else:
                            # 如果 name 不是 None, 说明检索词有错误
                            results[name] = ["".join(["!", str(name)])]
                    results[name].extend([None]*(result_len - 1))

            else:
                if self.querys[name] is None or name not in results or results[name] is None:
                    results[name] = [None] * result_len
            results[name] = tuple(results[name])
        return [results[w] for w in self.names]

    # 以下多个方法用于组装 get 协程
    # 跟踪协程的执行，并将执行结果生成缓存

    def __build_cache_and_get_results(self, action, leftover_querys=None):
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
                **self.cache['ipni'],
                **self.cache['col'],
                **self.cache['powo']},
            'colTaxonTree': self.cache['col'],
            'colName': self.cache['col'],
            'colSynonyms': self.cache['col'],
            'colAccepted': self.cache['col'],
            'ipniName': self.cache['ipni'],
            'ipniReference': self.cache['ipni'],
            'powoName': self.cache['powo'],
            'powoAccepted': self.cache['powo'],
            'powoImages': self.cache['powo'],
            'tropicosName': self.cache['tropicosName'],
            'tropicosAccepted': self.cache['tropicosAccepted'],
            'tropicosSynonyms': self.cache['tropicosSynonyms']
        }
        results = {}
        cache = cache_mapping[action]
        if cache:
            if leftover_querys:
                names = leftover_querys
            else:
                names = self.querys
            action_func = {
                # 注意 stdName 的 col 函数置于元组最后，
                # 以避免 ipni/powo 中与 col 同名的字段
                # 被 col 函数解析。
                'stdName': (self.ipni_name, self.powo_name, self.tropicos_name, self.col_name),
                'colTaxonTree': self.col_taxontree,
                'colName': self.col_name,
                'colSynonyms': self.col_synonyms,
                'colAccepted': self.col_accepted,
                'ipniName': self.ipni_name,
                'ipniReference': self.ipni_reference,
                'powoName': self.powo_name,
                'powoAccepted': self.powo_accepted,
                'powoImages': self.powo_images,
                'tropicosName': self.tropicos_name,
                'tropicosAccepted': self.tropicos_accepted,
                # 'tropicosSynonyms': self.tropicos_synonyms
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
            if not leftover_querys:
                # 如果没有缓存，所有检索词执行一次 web 搜索
                search_terms = self.querys
        # 为防止 search_terms 不存在，这里的条件判断应放置在后面
        if not leftover_querys and search_terms:
            # 若leftover_querys 是 None, 说明 web 请求是首次发起，执行一次递归检索
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
            'colAccepted': self.get_col_name,
            'ipniName': self.get_ipni_name,
            'ipniReference': self.get_ipni_name,
            'powoName': self.get_powo_name,
            'powoAccepted': self.get_powo_name,
            'powoImages': self.get_powo_name,
            'tropicosName': self.get_tropicos_name,
            'tropicosAccepted': self.get_tropicos_accepted

        }
        self.pbar = tqdm(total=len(search_terms), desc=action, ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sema = asyncio.Semaphore(500)
        tasks = self.build_tasks(get_action[action], search_terms)
        results = loop.run_until_complete(tasks)
        # 修复 Windows 下出现的 RuntimeErro: Event loop is closed
        # 为什么注销 close 会管用，我也没完全搞清楚
        # 猜测可能是 asyncio 会自动关闭 loop
        # 暂且先这样吧！
        # loop.close()
        self.pbar.close()
        for res in results:
            try:
                self.cache[res[-1]][res[0]] = res[1]
            # 如果检索失败，则不写入缓存
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
                # query 值为 None 的将不参与web get
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
            返回的 iamges 通常是由最多三个 url 构成的元组
        """
        try:
            images = [image['fullsize'] for image in query_result['images']]
        except (KeyError, TypeError):
            # 如果结果中没有 images 信息，或者检索结果为空
            raise ValueError
        return images

    def powo_accepted(self, query_result):
        try:
            query_result = query_result['synonymOf']
        except KeyError:
            # 如果没有名称处理，默认将本名称作为接受名返回
            # 有些名字可能属于 unsolved 状态，也会被作为接受名返回
            pass
        except TypeError:
            # 检索结果为空，则没有接受名处理
            return None,
        try:
            return " ".join([query_result['name'], query_result['author']]),
        except (KeyError, TypeError):
            # 对于原变种，返回的结果中没有 author 属性，或者 author 属性为 None， 先直接返回 name
            return query_result['name'],

    def powo_name(self, query_result):
        if query_result:
            scientific_name = query_result["name"]
            author = query_result["author"]
            family = query_result['family']
            ipni_lsid = query_result['fqId']
            return scientific_name, author, family, ipni_lsid
        else:
            return None, None, None, None

    def col_accepted(self, query_result):
        try:
            scientific_name = query_result['accepted_name_info']['scientificName']
            author = query_result['accepted_name_info']['author']
            return ' '.join([scientific_name, author]),
        except (KeyError, TypeError):
            return None,

    def col_synonyms(self, query_result):
        try:
            synonyms = [
                synonym['synonym'] for synonym
                in query_result['accepted_name_info']['Synonyms']
            ]
            return synonyms
        except (KeyError, TypeError):
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
        except TypeError:
            return None, None, None, None, None, None
        return genus, family, order, _class, phylum, kingdom

    def col_name(self, query_result):
        try:  # 种及种下检索结果
            col_name_code = query_result['name_code']
            family = query_result['accepted_name_info']['taxonTree']['family']
            author = query_result['author']
            scientific_name = query_result['scientific_name']
        except KeyError:
            try:  # 属的检索结果
                scientific_name = query_result['genus']
                author = None
                family = query_result['family']
                col_name_code = None
            except KeyError:  # 科的检索结果
                family = query_result['family']
                author = None
                scientific_name = family
                col_name_code = query_result['record_id']
        except TypeError:
            return None, None, None, None
        return scientific_name, author, family, col_name_code

    def ipni_name(self, query_result):
        try:
            scientific_name = query_result["name"]
            author = query_result["authors"]
            family = query_result['family']
            ipni_lsid = query_result['fqId']
            # print(query[-1], genus, family, author)
        except TypeError:
            return None, None, None, None
        return scientific_name, author, family, ipni_lsid

    def ipni_reference(self, query_result):
        try:
            result = []
            keys = ['publishingAuthor', 'publication', 'referenceCollation', 'publicationYear', 'publicationYearNote', 'referenceRemarks', 'reference', 'bhlLink']
            for key in keys:
                try:
                    info = query_result[key]
                    if info != 'not_stated':
                        result.append(str(info).strip())
                    else:
                        result.append(None)
                except KeyError:
                    result.append(None)
            try:
                result.append(query_result['linkedPublication']['fqId'])
            except KeyError:
                result.append(None)
        except TypeError:
            return None, None, None, None, None, None, None, None, None
        return result

    def tropicos_name(self, query_result):
        if query_result:
            scientific_name = query_result['ScientificName']
            author = query_result['Author']
            family = query_result['Family']
            name_id = query_result['NameId']
            return scientific_name, author, family, name_id
        else:
            return None, None, None, None

    def tropicos_accepted(self, query_result):
        try:
            return query_result['AcceptedName']['ScientificNameWithAuthors'],
        except KeyError:
            return query_result['ScientificNameWithAuthors'],
        except TypeError:
            return None,

    def build_url(self, api, method, params):
        return '{base}/{method}?{opt}'.format(
                base=api,
                method=method,
                opt=urllib.parse.urlencode(params)
        )

    def build_querys(self):
        """
        return: simple_name, Filters(platform_rank), authors, raw_name
        """
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            split_name = self._format_name(raw_name)
            if split_name is None:
                raw2stdname[raw_name] = None
                continue
            else:
                if split_name[2] == "" and split_name[3]:
                    simple_name = ' '.join(
                        [split_name[0], split_name[1], split_name[3]]).strip()
                else:
                    simple_name = ' '.join(split_name[:4]).strip()
                raw2stdname[raw_name] = simple_name, split_name[-2], split_name[4], split_name[-1]
        return raw2stdname


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
            print("\n", url, "联网超时，请检查网络连接！")
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

    async def get_name(self, query, session):
        name = await self.get_ipni_name(query, session)
        if name and name[1]:
            return name
        else:
            name = await self.get_powo_name(query, session)
            if name and name[1]:
                return name
            else:
                name = await self.get_tropicos_name(query, session)
                if name and name[1]:
                    return name
                else:
                    return await self.get_col_name(query, session)

    async def get_tropicos_accepted(self, query, session):
        name = await self.check_tropicos_name(query, session)
        if name is None:
            return query[-1], None, 'tropicosAccepted'
        elif name:
            api = '/'.join([TROPICOS_API, str(name['NameId'])])
            accepted_name = await self.tropicos_search(api, '', Filters.acceptedname, session)
            if accepted_name:
                return query[-1], accepted_name[0], 'tropicosAccepted'
            elif accepted_name is None:
                # 如果查无处理结果，返回默认值
                return query[-1], name, 'tropicosAccepted'


    async def get_tropicos_name(self, query, session):
        name = await self.check_tropicos_name(query, session)
        if name or name is None:
            return query[-1], name, 'tropicosName'


    async def check_tropicos_name(self, query, session):
        names = await self.tropicos_search(TROPICOS_API, query[0], query[1], session)
        if not names:
            return names
        else:
            authors = self.get_author_team(query[2])
            # 如果有结果，但检索名的命名人缺失，则默认返回第一个accept name
            if authors == []:
                for name in names:
                    if name['NomenclatureStatusName'] in ["nom. cons.", "Legitimate"]:
                        return name
                for name in names:
                    if name['NomenclatureStatusName'] == "No opinion":
                        return name
                return names[0]
            else:
                for name in names:
                    try:
                        name['authorTeam'] = self.get_author_team(name['Author'])
                    except:
                        name['Author'] = None
                        name['authorTeam'] = []
                std_teams = [r['authorTeam'] for r in names]
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_authors(authors, std_teams)
                index = self._get_best_name(scores)
                if index is not None:
                    return names[index]
                else:
                    return None

    async def tropicos_search(self, api, query, filters, session):
        params = self._build_tropicos_params(query, filters)
        url = self.build_url(api, filters.value['tropicos'], params)
        resp = await self.async_request(url, session)
        try:
            resp[0]['Error']
            return None
        except KeyError:
            return resp
        except TypeError:
            return False

    def _build_tropicos_params(self, query, filters):
        params = {}
        if filters in [Filters.familial, Filters.infrafamilial, Filters.generic, Filters.infrageneric, Filters.specific, Filters.infraspecific]:
            # tropicos 可能对 "." 字符无法正常获取
            # 这里需要对学名种的点字符替换为 ASCII 十六进制编码
            # 否则将会返回 404 错误
            params['name'] = query.replace('.', '%2e')
            params['type'] = 'exact'
        else:
            pass
        params['apikey'] = '48304127-1eae-4a64-8f4a-5a35d95b65ce'
        params['format'] = 'json'
        return params

    async def get_col_name(self, query, session):
        name = await self.check_col_name(query, session)
        if name or name is None:
            return query[-1], name, 'col'

    async def check_col_name(self, query, session):
        """ 对 COL 返回的结果逐一进行检查

        return: 返回最能满足 query 条件的学名 dict
        """
        results = await self.col_search(query[0], query[1], session)
        # print(results)
        if not results:
            return results
        else:
            names = []
            for res in results:
                if query[1] is Filters.specific or query[1] is Filters.infraspecific:
                    if res['scientific_name'] == query[0]:
                        try:
                            res['author_team'] = self.get_author_team(res['author'])
                        except KeyError:
                            res['author_team'] = []
                        finally:
                            names.append(res)
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
            if names == []:
                return None
            # 若检索词命名人缺失，默认使用第一个同名接受名
            elif authors == []:
                for name in names:
                    if name['name_status'] == 'accepted name':
                        return name
                return names[0]
            else:
                std_teams = [r['author_team'] for r in names]
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_authors(authors, std_teams)
                # print(scores)
                index = self._get_best_name(scores)
                if index is not None:
                    return names[index]
                else:
                    return None

    async def col_search(self, query, filters, session):
        params = self._build_col_params(query, filters)
        url = self.build_url(SP2000_API, filters.value['col'], params)
        # print(url)
        resp = await self.async_request(url, session)
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
            return False
        except TypeError:
            print("\n网络中断:{0}\n".format(url))
            return False

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

    async def get_ipni_name(self, query, session):
        name = await self.check_ipni_name(query, session)
        if name or name is None:
            return query[-1], name, 'ipni'

    async def check_ipni_name(self, query, session):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        results = await self.kew_search(query[0], query[1], IPNI_API, session)
        if not results:
            return results
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    names.append(res)
            authors = self.get_author_team(query[2])
            if names == []:
                # print(query)
                return None
            # 检索词缺命名人，默认使用第一个同名结果
            elif authors == []:
                return names[0]
            else:
                std_teams = []
                for r in names:
                    author_team = [a["name"] for a in r["authorTeam"]]
                    if author_team:
                        std_teams.append(author_team)
                    else:
                        # ipni 一些学名的检索返回会有 authorTeam = []
                        # 但 authors 却有值的情况，此时可以基于 authors
                        # 生成可用于比对的 authorTeam
                        try:
                            std_teams.append(self.get_author_team(r['authors']))
                        except KeyError:
                            # ipni 有些标注为 auct.not_stated 的名称，没有任何命名人信息
                            r['authors'] = None
                            std_teams.append([])
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_authors(authors, std_teams)
                index = self._get_best_name(scores)
                if index is not None:
                    return names[index]
                else:
                    return None

    async def get_powo_name(self, query, session):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: KEW 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_powo_name(query, session)
        if name or name is None:
            return query[-1], name, 'powo'

    async def check_powo_name(self, query, session):
        """ 对 KEW 返回结果逐一进行检查

        return: 返回最满足 query 条件的学名 dict
        """
        results = await self.kew_search(query[0], query[1], POWO_API, session)
        if not results:
            # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
            return results
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    try:
                        res['authorTeam'] = self.get_author_team(res['author'])
                    except KeyError:
                        # 如果查询的结果中没有命名人信息,则补充空值
                        # 如果匹配结果只有这一个结果，采用该结果
                        # 如果匹配结果有多个，该结果后续将因 autorTeam 为空排除
                        res['author'] = None
                        res['authorTeam'] = []
                    names.append(res)
            authors = self.get_author_team(query[2])
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                # print(query)
                return None
            # 如果有结果，但检索名的命名人缺失，则默认返回第一个accept name
            elif authors == []:
                for name in names:
                    if name['accepted'] == True:
                        return name
                return names[0]
            else:
                std_teams = [r['authorTeam'] for r in names]
                # 开始比对原命名人与可选学名的命名人的比对结果
                scores = self.contrast_authors(authors, std_teams)
                index = self._get_best_name(scores)
                if index is not None:
                    return names[index]
                else:
                    return None

    async def kew_search(self, query, filters, api, session):
        params = self._build_kew_params(query, filters)
        resp = await self.async_request(self.build_url(api, 'search', params), session)
        try:
            return resp['results']
        except TypeError:
            # 网络中断，返回 False
            return False
        except KeyError:
            # 检索不到，返回 None
            return None
    
    def native_get(self, querys, names):
        """
            querys: build_querys 形成的待查询名称及其解构信息组成的字典
            names: 由学名组成的 Series, 用于被比较和提取
            return: 返回 None, 检索结果会直接写入 self.cache
        """
        results = {} 
        for query in tqdm(querys.values()):
            if query is None:
                continue
            homonyms = names[names.str.startswith(query[0])]
            if not homonyms.empty:
                name = self.check_native_name(query, homonyms)
                if name:
                    results[query[-1]] = name 
                else:
                    continue
            else:
                continue
        return results

    def check_native_name(self, query, similar_names):
        author_teams = []
        homonym = []
        for name in similar_names:
            split_name = self._format_name(name)
            name = self.built_name_style(split_name, 'apiName')
            if name[0] == query[0]:
                author_team = self.get_author_team(name[1])
                author_teams.append(author_team)
                homonym.append(name)
            else:
                continue
        if homonym:
            org_author_team = self.get_author_team(query[2])
            # 如果查询名称有命名人, 或者匹配名称没有命名人, 返回匹配但同名结果第一个
            if not org_author_team:
                return homonym[0]
            # 如果查询名称和可匹配名称均不缺少命名人, 进行命名人比较，确定最优
            scores = self.contrast_authors(org_author_team, author_teams)
            index = self._get_best_name(scores) 
            if index is not None:
                return homonym[index]
            else:
                return None
        else:
            return None

    def _build_kew_params(self, query, filters):
        params = {'perPage': 500, 'cursor': '*'}
        if query:
            params['q'] = self._format_kew_query(query)
        if filters:
            params['f'] = self._format_kew_filters(filters)
        return params

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

    def _format_name(self, raw_name):
        """ 将手写学名转成规范格式

            raw_name: 各类动植物学名字符串，目前仅支持:
                        属名 x 种名 种命名人 种下等级 种下加词 种下命名人
                        这类学名格式的清洗，
                        其中杂交符、种命名人、种下等级、种下命名人均可缺省。
            return: 命名人的各个组成部分构成的元组
                    如果无法提取合法的学名，则返回 None
        """
        species_pattern = re.compile(
            r"((?:!×\s?|×\s?|!)?[A-Z][a-zàäçéèêëöôùûüîï-]+)\s*(×\s+|X\s+|x\s+|×)?([a-zàâäèéêëîïôœùûüÿç][a-zàâäèéêëîïôœùûüÿç-]+)?\s*(.*)")
        subspecies_pattern = re.compile(
            r"(^[\"\'A-Z\(\.].*?[^A-Z-\s]\s*(?=$|var.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.))?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.)?\s*([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s*([\"\'（A-Z\(].*?[^A-Z-])?$")
        try:
            species_split = species_pattern.findall(raw_name)[0]
        except BaseException:
            return None
        subspec_split = subspecies_pattern.findall(species_split[3])[0]

        genus = species_split[0]
        if species_split[1] == "":
            species = species_split[2]
        else:
            species = " ".join(['×', species_split[2]])
        if subspec_split[2] == "":
            authors = species_split[3]
            taxon_rank = ""
            infraspecies = ""
            first_authors = ""
            if species_split[2] != "":
                platform_rank = Filters.specific
            elif genus.lower().endswith((
                "aceae", "idae", "umbelliferae", "labiatae", "compositae", "gramineae",
                    "leguminosae")):
                platform_rank = Filters.familial
            else:
                platform_rank = Filters.generic
        else:
            infraspecies = subspec_split[2]
            if infraspecies != species:
                taxon_rank = subspec_split[1]
                first_authors = subspec_split[0].strip()
                authors = subspec_split[3].strip()
                platform_rank = Filters.infraspecific
            else:
                # 原变种等种下加词和种加词一致的，种下和种命名人一致
                # 这里将其作为种一级的名称进行处理
                authors = subspec_split[0].strip()
                if authors:
                    pass
                else:
                    authors = subspec_split[3].strip()
                taxon_rank = ""
                first_authors = ""
                infraspecies  = ""
                platform_rank = Filters.specific
        return genus, species, taxon_rank, infraspecies, authors, first_authors, platform_rank, raw_name
    
    def fill_blank_name(self, pattern):
        if pattern == 'simpleName':
            return None
        elif pattern == 'apiName':
            return None, None
        elif pattern == 'scientificName':
            return None
        elif pattern == 'plantSplitName':
            return None, None, None, None, None
        elif pattern == 'fullPlantSplitName':
            return None, None, None, None, None, None
        elif pattern == 'animalSplitName':
            return None, None, None, None
        else:
            raise ValueError("学名处理参数错误，不存在{}".format(pattern))

    def built_name_style(self, split_name, pattern):
        if split_name is None:
            return self.fill_blank_name(pattern)
        if pattern == 'simpleName':
            if split_name[2] == "" and split_name[3]:
                simple_name = ' '.join(
                    [split_name[0], split_name[1], split_name[3]]).strip()
            else:
                simple_name = ' '.join(split_name[:4]).strip()
            return simple_name
        elif pattern == 'apiName':
            if split_name[2] == "" and split_name[3]:
                simple_name = ' '.join(
                    [split_name[0], split_name[1], split_name[3]]).strip()
            else:
                simple_name = ' '.join(split_name[:4]).strip()
            author = split_name[4]
            return (simple_name, author) if author else (simple_name, None)
        elif pattern == 'scientificName':
            if split_name[2] == "" and split_name[3]:
                simple_name = ' '.join(
                    [split_name[0], split_name[1], split_name[3]]).strip()
            else:
                simple_name = ' '.join(split_name[:4]).strip()
            author = split_name[4]
            return ' '.join([simple_name, author]) if author else simple_name
        elif pattern == 'plantSplitName':
            return tuple(e if e != '' else None for e in split_name[:5])
        elif pattern == 'fullPlantSplitName':
            elements = (split_name[0], split_name[1], split_name[5],
                        split_name[2], split_name[3], split_name[4])
            return tuple(e if e != '' else None for e in elements)
        elif pattern == 'animalSplitName':
            elements = (split_name[0], split_name[1],
                        split_name[3], split_name[4])
            return tuple(e if e != '' else None for e in elements)
        else:
            raise ValueError("学名处理参数错误，不存在{}".format(pattern))

    def format_latin_names(self, pattern):
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            split_name = self._format_name(raw_name)
            raw2stdname[raw_name] = self.built_name_style(split_name, pattern)
        return [raw2stdname[name] for name in self.names]

    def _get_best_name(self, scores):
        """
        scores: 由 contrast_authors 返回的比对结果

        return: 返回最佳匹配名称的序号，如果没有，则返回 None
        """
        scores.sort(key=lambda s:s[0], reverse=True)
        if scores[0][0]:
            # 这里默认没有得分相同的名字
            # 但现实可能会存在这种情况
            # 如果真存在这种情况，就需要去优化 contrast_authors
            return scores[0][1]
        else:
            return None

    def contrast_authors(self, author_team, author_teams):
        """ 将一个学名的命名人和一组学名的命名人编码进行比较，以确定最匹配的

        author_team: 一个学名命名人列表, 如["Hook. f.", "Thomos."], 不可以为 []

        author_teams: 一组包含多个学名命名人列表的的列表，一般来自于多个同名拉丁名的命名人, 可以为 [[]], 不可以为 None

        return: 返回一个与原命名人匹配亲近关系排列的list
        """
        raw_team = [self.clean_author(author) for author in author_team]
        s_teams_score = []
        for n, std_team in enumerate(author_teams):
            std_team = [self.clean_author(author) for author in std_team]
            score = []
            for r_author in raw_team:
                match = process.extract(r_author, std_team, scorer=fuzz.token_sort_ratio)
                try:
                    best_ratio = max(match, key=lambda v:v[1])
                    # 这里要求一个命名人的姓的首字母，必须要在比对的名称之中
                    # 否则即便匹配对比较高，也不会认为是同一个人
                    # 比如 Regel Wall. 与 Regel 匹配度就会被强制转为 0
                    # 主要是因为不管是中西方人名，命名人的姓都是非常重要的
                    # 通常不应该丢失，这里需要注意的可能有一些中国命名人的姓
                    # 是写在前面的,不过中文名字各部分一般不会省略，因此不影响
                    # 判断
                    if r_author.split()[-1][0] in best_ratio[0]:
                        score.append(best_ratio[1])
                    else:
                        score.append(0)
                except ValueError:
                    # author_teams 有些参与比对的学名，命名人可能为 []
                    score.append(0)
            s_team_score = sum(score)/len(score)
            s_teams_score.append((s_team_score, n))
        return s_teams_score

    def clean_author(self, author):
        aut = author.replace(".", " ")
        aut = aut.replace("-", " ")
        aut = aut.replace("'", " ")
        aut = aut.replace("  ", " ")
        return aut.strip()

    def strip_accents(self, text):
        """尽最大可能将字符串中衍生的拉丁字母转换为英文字母

        Args:
            text (str): 需要处理的字符串，比如 'PančićDiklić & V.NikolićØ的'

        Returns:
            str: 转换后的字符串，注意 text 中某些字符，可能由于无法转换为英文字母而被删除
        """
        # 统一一些组合字符的不同写法，以使其等价，比如 é 和 e\u0301
        # 这里 normalize 的模式必须设置为 NFD 而非 NFC，否则后续decode
        # 方法将无法给一些非 ascii 字符分配一个合适的 ascii 字符
        text = unicodedata.normalize('NFD', text)
        # 将命名人中的不同字符尽可能转化为 a-ZA-Z
        # 比如 PančićDiklić & V.Nikolić 转换为 PancicDiklic & V.Nikolic
        # 注意：字符串中的一些特殊字符可能无法转换，比如字符 Ø， 这些字符将被从字符串中删除
        ascii_text = text.encode('ascii', 'ignore').decode('utf-8')
        return ascii_text

    def ascii_authors(self, authors, discard=True):
        # strip_accents 并不能将所有字符转换为 ascii
        # 这些字符在返回的结果中会被删除
        pinyin = {'ß': 'ss', 'æ': 'ae', 'Ø': 'O', 'ø': 'o', 'þ': 'th', 'ð': 'd',
                  'Ɖ': 'D', 'ł': 'l', 'đ': 'd', 'ı': 'i', 'Р': 'R', 'Т': 'T'}
        # 先尽可能的将特殊文本转换为大小写英文字母
        authors = authors.translate(str.maketrans(pinyin))
        if discard:
            # 然后再进行字符转换，其中有些字母可能仍然无法转换
            ascii_authors = self.strip_accents(authors)
        else:
            # 如果仍然存在无法转换为英文的字母，则在 authors 中予以保留该字符
            chars = [self.strip_accents(word) if self.strip_accents(
                word) else word for word in authors]
            ascii_authors = ''.join(chars)
            #print(f'\n 命名人中存在特殊字符，程序目前无法识别 {ascii_authors} \n')
        return ascii_authors

    def get_author_team(self, authors):
        """ 提取学名命名人中，各个命名人的名字

        authors: 一个学名的命名人字符串

        return: 返回包含authors 中所有人名list 或 []
        """
        try:
            authors = self.ascii_authors(authors)
        # authors 为空
        except AttributeError:
            return []
        # 命名人可能是有一至多个部分组成，这里通过四种模式猜测可能的名称组成形式
        p = re.compile(
            r"(?:^|\(\s*|\s+et\s+|\s+ex\s+|\&\s*|\,\s*|\)\s*|\s+and\s+|\[\s*|\（\s*|\）\s*|\，\s*|\{\s*|\}\s*)([^\s\&\(\)\,\;\.\-\?\，\（\）\[\]\{\}][^\&\(\)\,\;\，\（\）\[\]\{\}]+?(?=\s+ex\s+|\s+et\s+|\s*\&|\s*\,|\s*\)|\s*\(|\s+and\s+|\s+in\s+|\s*\）|\s*\（|\s*\，|\s*\;|\s*\]|\s*\[|\s*\}|\s*\{|\s*$))")
        author_team = p.findall(authors)
        return author_team

    def __call__(self, mark=True):
        """
        这里定义了对名称进行在线比对后，单纯返回学名，该采用哪种样式的逻辑
        不管检索结果如何，程序都会返回与相应样式名称匹配的 DataFrame
        对于检索结果中，有部分名称没有返回值，这些名称默认将使用"!"标注
        对于检索结果中，所有的名称都没有返回值，则直接返回以对应列数 None 组成的 DataFrame
        """
        if self.style == 'scientificName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
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
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
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
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            self._format_name(name[0].strip())[:4] + (name[1],)
                            if name[1] else self.built_name_style(self._format_name(name[0].strip()), 'plantSplitName')
                            if name[0] else (None, None, None, None, None)
                            for name in results
                        ]
                    )
                else:
                    return pd.DataFrame([[None, None, None, None, None]] * len(self.names))
            else:
                results = self.format_latin_names(pattern="plantSplitName")
                return pd.DataFrame(results)
        elif self.style == 'fullPlantSplitName':
            # 该模式在这里刻意不提供在线名称比对
            # 我们不是很赞成对植物学名进行包含种下命名人和种命名人的拆分
            # 但进行要素全拆分，有的时候又是必须，
            # 所以这里暂时只将其作为一个拆分功能，供用户进行学名拆分
            results = self.format_latin_names(pattern="fullPlantSplitName")
            return pd.DataFrame(results)
        elif self.style == 'animalSplitName':
            results = self.format_latin_names(pattern="animalSplitName")
            return pd.DataFrame(results)
        else:
            print("\n学名处理参数有误，不存在{}\n".format(self.style))
            return pd.DataFrame(self.names)


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
            for m, d in zip(self.df.iloc[:, 0], self.duplicated)
        ]
        return marks

    def __call__(self):
        self.df.iloc[:, 0] = self.mark_duplicate()
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
