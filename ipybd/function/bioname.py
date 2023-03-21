
import asyncio
import re
import unicodedata
import urllib
from typing import Union
from ipybd.function.cleaner import ifunc

import aiohttp
import pandas as pd
import requests
from ipybd.function.api_terms import Filters
from thefuzz import fuzz, process
from tqdm import tqdm


SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'http://beta.ipni.org/api/1'
POWO_API = 'https://powo.science.kew.org/api/2'
TROPICOS_API = 'https://services.tropicos.org/Name'


@ifunc
class BioName:
    def __init__(self, names: Union[list, pd.Series, tuple], style='scientificName'):
        self.names = names
        self.querys = {}
        self.cache = {'ipni': {}, 'col': {}, 'powo': {}, 'tropicosName': {
        }, 'tropicosAccepted': {}, 'tropicosSynonyms': {}}
        self.style = style

    def get(self, action, typ=list, mark=False):
        if self.querys == {}:
            self.querys = self.build_querys()
        if isinstance(action, str):
            # results 只包含检索过的
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
                # print(results)
                # 无法格式化的/检索无结果/检索失败，用英文!标注
                if self.querys[name] is None or name not in results or set(results[name]) == {None}:
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
                if self.querys[name] is None or name not in results or set(results[name]) == {None}:
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
                **self.cache['powo'],
                **self.cache['tropicosName'],
                **self.cache['col'],
                },
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
            keys = ['publishingAuthor', 'publication', 'referenceCollation', 'publicationYear',
                    'publicationYearNote', 'referenceRemarks', 'reference', 'bhlLink']
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
                        name['authorTeam'] = self.get_author_team(
                            name['Author'])
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
                            res['author_team'] = self.get_author_team(
                                res['author'])
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
                            std_teams.append(
                                self.get_author_team(r['authors']))
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
                infraspecies = ""
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
        scores.sort(key=lambda s: s[0], reverse=True)
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
                match = process.extract(
                    r_author, std_team, scorer=fuzz.token_sort_ratio)
                try:
                    best_ratio = max(match, key=lambda v: v[1])
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
