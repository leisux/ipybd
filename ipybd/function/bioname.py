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
from Levenshtein import distance
from tqdm import tqdm


SP2000_API = 'http://www.sp2000.org.cn/api/v2'
IPNI_API = 'https://www.ipni.org/api/1'
POWO_API = 'https://powo.science.kew.org/api/2'
TROPICOS_API = 'http://services.tropicos.org/Name'


@ifunc
class BioName:
    """Scientific name parser and validator using multiple botanical databases.

    Provides functionality to parse, standardize, and validate scientific names
    against IPNI, POWO, Tropicos, and COL databases. Supports batch processing
    with async API calls and intelligent authorship matching.

    Args:
        names: List, Series, or tuple of scientific names to process.
        style: Output format for scientific names. Options include:
            - 'scientificName': Full name with author (e.g., "Abies alba Mill.")
            - 'simpleName': Name without author (e.g., "Abies alba")
            - 'apiName': Tuple of (name, author)
            - 'plantSplitName': Tuple split into (genus, species, rank, infraspecies, author)
            - 'fullPlantSplitName': Full split including first authors
            - 'animalSplitName': Tuple split for animal names

    Attributes:
        names: Original input names.
        querys: Parsed query dictionary mapping raw names to structured queries.
        cache: Cache for API results from multiple databases.
        style: Current output style setting.

    Example:
        >>> names = BioName(['Abies alba Mill.', 'Pinus sylvestris L.'])
        >>> results = names.get('stdName')
    """

    def __init__(self, names: Union[list, pd.Series, tuple], style='scientificName'):
        """Initialize BioName with scientific names.

        Args:
            names: List, Series, or tuple of scientific names.
            style: Output format style (default 'scientificName').
        """
        self.names = names
        self.querys = {}
        self.cache = {'ipni': {}, 'col': {}, 'powo': {}, 'tropicos': {
        }, 'tropicosAccepted': {}, 'tropicosSynonyms': {}}
        self.style = style
    
    def get_best_names(self):
        """Extract best authorship information for each name in self.names.

        Queries multiple databases (powo, tropicos, ipni, col) to find the
        best matching scientific name with authorship information.

        Returns:
            Dictionary mapping original names to tuples of:
            (simpleName, authorship, similar_authorship, degree)
        """
        tasks = self.querys
        names = {}
        while tasks:
            querys, tasks = tasks, {}
            for org_name, keywords in querys.items():
                if keywords:
                    try:
                        authorship, similar_authorship, degree = self._get_best_authorship(org_name, keywords[2])
                        names[org_name] = keywords[0], authorship, similar_authorship, degree
                    except KeyError as error:
                        database = str(error)[1:-1]
                        try:
                            tasks[database][org_name] = keywords
                        except KeyError:
                            tasks[database] = {}
                            tasks[database][org_name] = keywords
            if tasks:
                new_tasks = {}
                for database, querys in tasks.items():
                    self.web_get(database+'Name', querys)
                    new_tasks.update(querys)
                tasks = new_tasks
        return names
            
    def _get_best_authorship(self, name, authorship, databases={'powo':'author', 'tropicos':'Author', 'ipni':'authors', 'col':'author'}):
        """Find best authorship match across databases.

        Args:
            name: Scientific name to match.
            authorship: Original authorship string.
            databases: Mapping of database names to their author field names.

        Returns:
            Tuple of (authorship, similar_authorship, degree) where degree
            is a string like 'S3', 'H2', 'E0' indicating match quality.
        """
        for dgr in ('S', 'H', 'M', 'L', 'E'):
            for database in databases:
                try:
                    degree = self.cache[database][name]['match_degree']
                except TypeError:
                    degree = None
                    continue
                except KeyError:
                    raise KeyError(database)
                if degree[0] == dgr:
                    try:
                        similar_authorship = self.cache[database][name][databases[database]]
                        similar_authorship = self.format_authorship(similar_authorship)
                    except KeyError:
                        similar_authorship = None
                    degree = ''.join([database[0].upper(), degree])
                    authorship = self.format_authorship(authorship)
                    break
                else:
                    degree = None
            if degree:
                break
        if degree is None:
            similar_authorship = None
            authorship = self.format_authorship(authorship)
        return authorship, similar_authorship, degree
    
    def get(self, action, typ=list, mark=False):
        """Execute a query action and return results.

        Args:
            action: Query action - can be:
                - 'bestName': Get best names with authorship
                - 'colTaxonTree', 'colName', 'colSynonyms', 'colAccepted': COL queries
                - 'ipniName', 'ipniReference': IPNI queries
                - 'powoName', 'powoAccepted', 'powoImages': POWO queries
                - 'tropicosName', 'tropicosAccepted': Tropicos queries
                - pd.Series: Native name matching against provided library
                - tuple: Native matching with strict mode
            typ: Return type - list or dict (default list).
            mark: If True, mark failed queries with '!' prefix.

        Returns:
            Query results in specified type, or empty list/dict if no results.
        """
        if self.querys == {}:
            self.querys = self.build_querys()
        if isinstance(action, pd.Series):
            results = self.native_get(self.querys, action)
        elif isinstance(action, tuple):
            results = self.native_get(self.querys, action[0], strict=True)
        elif action == 'bestName':
            results = self.get_best_names()
        elif isinstance(action, str):
            # results 只包含检索过的
            results = self.get_query_results(action)
        else:
            raise TypeError('action must be str or pd.Series')
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
        """Assemble and format query results into a list.

        Args:
            results: Dictionary of results from self.cache.
            mark: If True, failed queries are marked with '!' prefix.
                If None, failed queries return tuples of None matching result length.

        Returns:
            List of results ordered by self.names, where each element is a tuple.
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
    def get_query_results(self, action, leftover=None):
        """Build query cache and return query results.

        Args:
            action: Query action string (e.g., 'stdName', 'colName').
            leftover: Search terms without cache, requiring web query.
                Dictionary derived from self.querys.

        Returns:
            Dictionary of results {raw_name: result}.
            Returns empty dict if no results found.
            Results are also written to self.cache during retrieval.
        """
        cache_mapping = {
            'stdName': {
                **self.cache['ipni'],
                **self.cache['powo'],
                **self.cache['tropicos'],
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
            'tropicosName': self.cache['tropicos'],
            'tropicosAccepted': self.cache['tropicosAccepted'],
            'tropicosSynonyms': self.cache['tropicosSynonyms']
        }
        cache = cache_mapping[action]
        results, search_terms = {}, {}
        if cache:
            names = leftover if leftover else self.querys
            results, search_terms = self.get_cache_results(names, cache, action)
        elif not leftover:
            # 如果没有缓存，所有检索词执行一次 web 搜索
            results = {}
            search_terms = self.querys
        # 为防止 search_terms 不存在，这里的条件判断应放置在后面
        if not leftover and search_terms:
            # 若leftover 是 None, 说明 web 请求是首次发起，执行一次递归检索
            # 若search_terms 并非 self.querys，说明 get 请求是由程序本身自动发起
            # 执行结束后，将不再继续执行递归
            self.web_get(action, search_terms)
            # 这里的递归最多只执行一次
            sub_results = self.get_query_results(
                action, search_terms)
            results.update(sub_results)
        return results
    
    def get_cache_results(self, names, cache, action):
        """Extract results from cache and identify terms needing web lookup.

        Args:
            names: Dictionary of search terms.
            cache: Cache dictionary to extract results from.
            action: Action string determining which parsing function to use.

        Returns:
            Tuple of (results_dict, search_terms_dict).
            results_dict contains cached results.
            search_terms_dict contains terms that need web queries.
        """
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
        results, search_terms = {}, {}
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
        return results, search_terms

    def get_cache_result(self, query_result, get_result):
        """Extract specific data from cached query result.

        Args:
            query_result: Raw query result from cache.
            get_result: Function or tuple of functions to extract specific data.
                When tuple, functions are tried in order until one succeeds.

        Returns:
            Extracted data in format determined by the get_result function.
            Returns None if no function succeeds.
        """
        try:
            return get_result(query_result)
        # func 是 tuple 时触发
        except TypeError:
            for func in get_result:
                try:
                    # 遇到首个有正常返回值后，停止循环
                    return self.get_cache_result(query_result, func)
                # 若多个 API 返回结果的 keys 通用，这里可能不会触发 KeyError,目
                # 前已知 col 和 ipni/powo 部分keys 通用，且 col 不存在属查询，
                # family 检索和 species 返回的数据结构也不一致，因此其内部需要
                # 处理相关 KeyError 错误，与这里的处理会有冲突，因此该函数 func
                # 中 col 的处理函数应该至于最后，以避免 ipni/powo 的数据被 col
                # 处理函数处理。
                except KeyError:
                    continue

    def web_get(self, action, search_terms):
        """Query web APIs to retrieve name information.

        Args:
            action: Action string describing the operation to perform.
            search_terms: Search conditions as dict from self.querys.
                Format: raw_name: (simpleName, rank, author, raw_name)

        Returns:
            None. Results are written directly to self.cache.
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
            # 如果在线检索失败，则不写入缓存
            except TypeError:
                pass

    async def build_tasks(self, action_func, search_terms):
        """Build async tasks for concurrent API requests.

        Args:
            action_func: Function to call for each search term.
            search_terms: Dictionary of search terms.

        Returns:
            List of results from asyncio.gather.
        """
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
        """Fetch single record with semaphore control.

        Args:
            func: Async function to call.
            param: Parameters for the function.
            session: aiohttp session.

        Returns:
            Result from the async function call.
        """
        async with self.sema:
            result = await func(param, session)
            self.pbar.update(1)
            return result


    # 以下多个方法用于对 Api 返回结果进行有针对性的处理
    # 并根据具体调用的方法，返回用户所需要的数据
    def powo_images(self, query_result):
        """Parse images from POWO cache result.

        POWO returns thumbnail and fullsize URLs for images.
        Each name has at most three images.

        Args:
            query_result: POWO query result dictionary.

        Returns:
            Tuple of fullsize image URLs (up to 3).

        Raises:
            ValueError: If no images in result or result is empty.
        """
        try:
            images = [image['fullsize'] for image in query_result['images']]
        except (KeyError, TypeError):
            # 如果结果中没有 images 信息，或者检索结果为空
            raise ValueError
        return images

    def powo_accepted(self, query_result):
        """Extract accepted name from POWO query result.

        Args:
            query_result: POWO query result dictionary.

        Returns:
            Tuple of (accepted_name_with_author,) or (None,) if no accepted name.
        """
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
        """Extract name details from POWO query result.

        Args:
            query_result: POWO query result dictionary.

        Returns:
            Tuple of (scientific_name, author, family, ipni_lsid, match_degree).
            Returns (None, None, None, None, None) if query_result is empty.
        """
        if query_result:
            scientific_name = query_result["name"]
            author = query_result["author"]
            family = query_result['family']
            ipni_lsid = query_result['fqId']
            degree = query_result['match_degree']
            return scientific_name, author, family, ipni_lsid, degree
        else:
            return None, None, None, None, None

    def col_accepted(self, query_result):
        """Extract accepted name from COL query result.

        Args:
            query_result: COL query result dictionary.

        Returns:
            Tuple of (accepted_name_with_author,) or (None,) if no accepted name.
        """
        try:
            scientific_name = query_result['accepted_name_info']['scientificName']
            author = query_result['accepted_name_info']['author']
            return ' '.join([scientific_name, author]),
        except (KeyError, TypeError):
            return None,

    def col_synonyms(self, query_result):
        """Extract synonyms from COL query result.

        Args:
            query_result: COL query result dictionary.

        Returns:
            List of synonym names.

        Raises:
            ValueError: If no synonyms found in result.
        """
        try:
            synonyms = [
                synonym['synonym'] for synonym
                in query_result['accepted_name_info']['Synonyms']
            ]
            return synonyms
        except (KeyError, TypeError):
            raise ValueError

    def col_taxontree(self, query_result):
        """Extract taxonomic hierarchy from COL query result.

        Args:
            query_result: COL query result dictionary.

        Returns:
            Tuple of (genus, family, order, class, phylum, kingdom).
            Returns (None, None, None, None, None, None) if result is empty.
        """
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
        """Extract name details from COL query result.

        Handles species, subspecies, genus, and family level results.

        Args:
            query_result: COL query result dictionary.

        Returns:
            Tuple of (scientific_name, author, family, col_name_code, degree).
            Returns (None, None, None, None, None) if result is empty.
        """
        try:  # 种及种下检索结果
            degree = query_result['match_degree']
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
            return None, None, None, None, None
        return scientific_name, author, family, col_name_code, degree

    def ipni_name(self, query_result):
        """Extract name details from IPNI query result.

        Args:
            query_result: IPNI query result dictionary.

        Returns:
            Tuple of (scientific_name, author, family, ipni_lsid, match_degree).
            Returns (None, None, None, None, None) if result is empty.
        """
        try:
            scientific_name = query_result["name"]
            author = query_result["authors"]
            family = query_result['family']
            ipni_lsid = query_result['fqId']
            degree = query_result['match_degree']
            # print(query[-1], genus, family, author)
        except TypeError:
            return None, None, None, None, None
        return scientific_name, author, family, ipni_lsid, degree

    def ipni_reference(self, query_result):
        """Extract publication references from IPNI query result.

        Args:
            query_result: IPNI query result dictionary.

        Returns:
            List of reference information:
            [publishingAuthor, publication, referenceCollation, publicationYear,
             publicationYearNote, referenceRemarks, reference, bhlLink, linkedPublicationId]
            Returns [None,...] if result is empty.
        """
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
        """Extract name details from Tropicos query result.

        Args:
            query_result: Tropicos query result dictionary.

        Returns:
            Tuple of (scientific_name, author, family, name_id, match_degree).
            Returns (None, None, None, None, None) if result is empty.
        """
        if query_result:
            scientific_name = query_result['ScientificName']
            author = query_result['Author']
            family = query_result['Family']
            name_id = query_result['NameId']
            degree = query_result['match_degree']
            return scientific_name, author, family, name_id, degree
        else:
            return None, None, None, None, None

    def tropicos_accepted(self, query_result):
        """Extract accepted name from Tropicos query result.

        Args:
            query_result: Tropicos query result dictionary.

        Returns:
            Tuple of (accepted_name_with_authors,) or (None,) if no accepted name.
        """
        try:
            return query_result['AcceptedName']['ScientificNameWithAuthors'],
        except KeyError:
            return query_result['ScientificNameWithAuthors'],
        except TypeError:
            return None,

    async def get_name(self, query, session):
        """Get standardized name by querying multiple databases.

        Tries IPNI, POWO, Tropicos, and COL in order until a valid result is found.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, name_result, database) or last attempt's result.
        """
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

    async def get_col_name(self, query, session):
        """Get name from COL (Catalogue of Life) database.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, result, 'col').
        """
        name = await self.check_col_name(query, session)
        if name or name is None:
            return query[-1], name, 'col'

    async def get_ipni_name(self, query, session):
        """Get name from IPNI (International Plant Names Index) database.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, result, 'ipni').
        """
        name = await self.check_ipni_name(query, session)
        if name or name is None:
            return query[-1], name, 'ipni'

    async def get_powo_name(self, query, session):
        """Get name from KEW POWO (Plants of the World Online) database.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, result, 'powo').
        """
        name = await self.check_powo_name(query, session)
        if name or name is None:
            return query[-1], name, 'powo'

    async def get_tropicos_name(self, query, session):
        """Get name from Tropicos database.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, result, 'tropicos').
        """
        name = await self.check_tropicos_name(query, session)
        if name or name is None:
            return query[-1], name, 'tropicos'

    async def get_tropicos_accepted(self, query, session):
        """Get accepted name from Tropicos database.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Tuple of (raw_name, accepted_name, 'tropicosAccepted').
        """
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

    def native_get(self, querys, org_lib, strict=False):
        """Match queries against native library without web requests.

        Args:
            querys: Dictionary from build_querys with name and structure info.
            org_lib: Series of scientific names for matching.
            strict: If True, only exact matches are returned.

        Returns:
            Dictionary of matched results {raw_name: matched_name}.
        """
        results = {}
        lib_names = self._get_simple_names(org_lib)
        for query in tqdm(querys.values()):
            if query is None:
                continue
            homonyms = self.find_similar(query[0], org_lib, lib_names, strict)
            if not homonyms.empty:
                name = self.check_native_name(query, homonyms)
                if name:
                    results[query[-1]] = name
                else:
                    continue
            else:
                continue
        return results
    
    def find_similar(self, name, org_lib, lib_names, strict):
        """Find similar names in library using fuzzy matching.

        Args:
            name: Name to match.
            org_lib: Original series of names.
            lib_names: Series of simplified names for comparison.
            strict: If True, only exact matches are returned.

        Returns:
            Series of matching names from org_lib.
        """
        if strict:
            series = org_lib[lib_names==name]
        else:
            # 这里可以进一步提高效率，绝大多数情况下，并不需要为每个名字计算字符距离
            dist = lib_names.apply(self._fuzzy_similarity, args=(name,))
            series = org_lib[dist < 4]
        return series

    def _strict_similarity(self, name_with_authors, name_without_authors):
        """Check strict similarity between names.

        Args:
            name_with_authors: Name including authorship.
            name_without_authors: Name without authorship.

        Returns:
            True if names match exactly, False otherwise.
        """
        name = self.format_latin_name(name_with_authors, 'simpleName')
        return True if name == name_without_authors else False

    def _get_simple_names(self, series):
        """Extract simple names from scientific names series.

        Parses scientific names into genus, species, and other components.

        Args:
            series: Series of scientific names.

        Returns:
            Series of simplified names (genus + species only).
        """
        sp = r"((?:!×\s?|×\s?|!)?[A-Z][a-zàäçéèêëöôùûüîï-]+)\s*(×\s+|X\s+|x\s+|×)?([a-zàâäèéêëîïôœùûüÿç][a-zàâäèéêëîïôœùûüÿç-]+)?\s*(.*)"
        ssp = r"(^[\"\'（A-ZŠÁÅČ\(\.].*?[^A-Z-\s]\s*(?=$|var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.|lusus\s|\[unranked\]|×|monstr\.|proles\s))?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.|lusus\s|\[unranked\]|×|monstr\.|proles\s)?\s*([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s*([\"\'（A-ZÅÁŠČ\(].*?[^A-Z-])?$"
        species = series.str.extract(sp)
        subsp = species[3].str.extract(ssp)
        species = pd.concat([species[[0, 1, 2]], subsp], axis=1)
        species.columns = range(len(species.columns))
        subsp = species.apply(self.__format_subspecies, axis=1)
        species = species[0].str.cat([species[1], species[2], subsp], sep=' ', na_rep='').str.replace('  ', ' ').str.strip()
        return species

    def __format_subspecies(self, subsp):
        """Format subspecies/infraspecies name.

        Args:
            subsp: Tuple of parsed subspecies components.

        Returns:
            Formatted subspecies name string.
        """
        if pd.notna(subsp[5]) and subsp[5] != subsp[2]:
            try: 
                return ' '.join([subsp[4], subsp[5]])
            except TypeError:
                # print(subsp)
                return subsp[5]

    def _fuzzy_similarity(self, name, name_without_authors):
        """Calculate fuzzy similarity distance between names.

        Args:
            name: Name to compare.
            name_without_authors: Reference name without authorship.

        Returns:
            Levenshtein distance between names, or None if name is null.
        """
        if pd.isnull(name_without_authors):
            return None
        else:
            # name = self.format_latin_name(name, 'simpleName')
            if name:
                return distance(name, name_without_authors)
            else:
                return None
    
    def check_native_name(self, query, similar_names):
        """Check and select best match from similar native names.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            similar_names: Series of similar names found in library.

        Returns:
            Best matching name tuple with match degree, or None.
        """
        homonym = []
        for name in similar_names:
            name = self.format_latin_name(name, 'apiName')
            homonym.append(name)
        if homonym:
            org_author_team = self.get_author_team(query[2], nested=True)
            # 如果查询名称没有命名人, 或者匹配名称没有命名人, 尽可能返回一个同名结果
            if not org_author_team:
                if len(homonym) == 1:
                    return homonym[0] + ('E0',) if homonym[0][0] == query[0] else homonym[0] + ('e0',)
                else:
                    homo = [hom for hom in homonym if hom[0] == query[0]]
                    return homo[0] + ('E0',) if homo else homonym[0] + ('e0',)
            # 如果查询名称和可匹配名称均不缺少命名人, 进行命名人比较，确定最优
            return self.get_similar_name(query[0], org_author_team, homonym, (0,1))
        else:
            return None

    async def check_tropicos_name(self, query, session):
        """Find best matching Tropicos name for query.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Best matching Tropicos name dict with match_degree, or None.
        """
        names = await self.tropicos_search(TROPICOS_API, query[0], query[1], session)
        if not names:
            return names
        else:
            authors = self.get_author_team(query[2], nested=True)
            # 如果有结果，但检索名的命名人缺失，则默认返回第一个accept name
            if authors == []:
                for name in names:
                    if name['NomenclatureStatusName'] in ["nom. cons.", "Legitimate"]:
                        name['match_degree'] = 'E0'
                        return name
                for name in names:
                    if name['NomenclatureStatusName'] == "No opinion":
                        name['match_degree'] = 'E0'
                        return name
                names[0]['match_degree'] = 'E0'
                return names[0]
            else:
                return self.get_similar_name(query[0], authors, names, ('ScientificName', 'Author'))

    async def check_col_name(self, query, session):
        """Find best matching COL name for query.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Best matching COL name dict, or None.
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
                        names.append(res)
                # col 接口目前尚无属一级的内容返回，这里先取属下种及种
                # 下一级的分类阶元返回。
                elif query[1] is Filters.generic:
                    try:
                        if res['accepted_name_info']['taxonTree']['genus'] == query[0]:
                            res['accepted_name_info']['taxonTree']['match_degree'] = 'E0'
                            return res['accepted_name_info']['taxonTree']
                    except TypeError:
                        continue
                elif query[1] is Filters.familial and res['family'] == query[0]:
                    res['match_degree'] = 'E0'
                    return res
            authors = self.get_author_team(query[2], nested=True)
            if names == []:
                return None
            # 若检索词命名人缺失，默认使用第一个同名接受名
            elif authors == []:
                for name in names:
                    if name['name_status'] == 'accepted name':
                        name['match_degree'] = 'E0'
                        return name
                names[0]['match_degree'] = 'E0'
                return names[0]
            else:
                return self.get_similar_name(query[0], authors, names, ('scientific_name', 'author'))

    async def check_ipni_name(self, query, session):
        """Find best matching IPNI name for query.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Best matching IPNI name dict, or None.
        """
        results = await self.kew_search(query[0], query[1], IPNI_API, session)
        if not results:
            return results
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    names.append(res)
            authors = self.get_author_team(query[2], nested=True)
            if names == []:
                # print(query)
                return None
            # 检索词缺命名人，默认使用第一个同名结果
            elif authors == []:
                names[0]['match_degree'] = 'E0'
                return names[0]
            else:
                return self.get_similar_name(query[0], authors, names, ('name', 'authors'))

    async def check_powo_name(self, query, session):
        """Find best matching POWO name for query.

        Args:
            query: Query tuple (simple_name, rank, author, raw_name).
            session: aiohttp session.

        Returns:
            Best matching POWO name dict, or None.
        """
        results = await self.kew_search(query[0], query[1], POWO_API, session)
        if not results:
            # 查无结果或者未能成功查询，返回带英文问号的结果以被人工核查
            return results
        else:
            names = []
            for res in results:
                if res["name"] == query[0]:
                    names.append(res)
            authors = self.get_author_team(query[2], nested=True)
            # 如果搜索名称和返回名称不一致，标注后待人工核查
            if names == []:
                # print(query)
                return None
            # 如果有结果，但检索名的命名人缺失，则默认返回第一个accept name
            elif authors == []:
                for name in names:
                    if name['accepted'] == True:
                        name['match_degree'] = 'E0'
                        return name
                names[0]['match_degree'] = 'E0'
                return names[0]
            else:
                return self.get_similar_name(query[0], authors, names, ('name', 'author'))


    async def tropicos_search(self, api, query, filters, session):
        """Search Tropicos API for scientific name.

        Args:
            api: Tropicos API base URL.
            query: Search query string.
            filters: Filter enum for taxonomic rank.
            session: aiohttp session.

        Returns:
            List of matching names, None if error, or False if no results.
        """
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
        """Build query parameters for Tropicos API.

        Args:
            query: Search query string.
            filters: Filter enum for taxonomic rank.

        Returns:
            Dictionary of API parameters.
        """
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

    async def col_search(self, query, filters, session):
        """Search COL (Catalogue of Life) API.

        Args:
            query: Search query string.
            filters: Filter enum for taxonomic rank.
            session: aiohttp session.

        Returns:
            List of matching species/families, None if error, False if network issue.
        """
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
        """Build query parameters for COL API.

        Args:
            query: Search query string.
            filters: Filter enum for taxonomic rank.

        Returns:
            Dictionary of API parameters.
        """
        params = {'apiKey': '42ad0f57ae46407686d1903fd44aa34c'}
        if filters is Filters.familial:
            params['familyName'] = query
        elif filters is Filters.commonname:
            params['commonName'] = query
        else:
            params['scientificName'] = query
        params['page'] = 1
        return params

    async def kew_search(self, query, filters, api, session):
        """Search KEW API (IPNI or POWO).

        Args:
            query: Search query string.
            filters: Filter enum for taxonomic rank.
            api: API base URL (IPNI_API or POWO_API).
            session: aiohttp session.

        Returns:
            List of results, None if not found, False if network error.
        """
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

    def _build_kew_params(self, query, filters):
        """Build query parameters for KEW APIs.

        Args:
            query: Search query string or dict.
            filters: Filter enum or list of filters.

        Returns:
            Dictionary of API parameters.
        """
        params = {'perPage': 500, 'cursor': '*'}
        if query:
            params['q'] = self._format_kew_query(query)
        if filters:
            params['f'] = self._format_kew_filters(filters)
        return params

    def _format_kew_query(self, query):
        """Format query string for KEW API.

        Args:
            query: Query string or dict of field:value pairs.

        Returns:
            Formatted query string.
        """
        if isinstance(query, dict):
            terms = [k.value + ':' + v for k, v in query.items()]
            return ",".join(terms)
        else:
            return query

    def _format_kew_filters(self, filters):
        """Format filters for KEW API.

        Args:
            filters: Filter enum or list of filter enums.

        Returns:
            Formatted filter string for API.
        """
        if isinstance(filters, list):
            terms = [f.value['kew'] for f in filters]
            return ",".join(terms)
        else:
            return filters.value['kew']

    def build_url(self, api, method, params):
        """Build complete URL with query parameters.

        Args:
            api: API base URL.
            method: API method/endpoint.
            params: Dictionary of query parameters.

        Returns:
            Complete URL string.
        """
        return '{base}/{method}?{opt}'.format(
            base=api,
            method=method,
            opt=urllib.parse.urlencode(params)
        )

    def build_querys(self):
        """Parse and build query dictionary from input names.

        Returns:
            Dictionary mapping raw_name to tuple of
            (simple_name, Filters(rank), authors, raw_name).
            Returns None for names that cannot be parsed.
        """
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            split_name = self.parse_name(raw_name)
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
        """Perform async HTTP GET request with retry on rate limiting.

        Args:
            url: URL to fetch.
            session: aiohttp session.

        Returns:
            JSON response or None if network timeout.
        """
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
        """Fallback synchronous GET request.

        Used when async request fails.

        Args:
            url: URL to fetch.

        Returns:
            JSON response or None on error.
        """
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

    
    def format_latin_names(self, pattern):
        """Format all names according to pattern.

        Args:
            pattern: Output format (simpleName, scientificName, apiName, etc.).

        Returns:
            List of formatted names.
        """
        raw2stdname = dict.fromkeys(self.names)
        for raw_name in raw2stdname:
            raw2stdname[raw_name] = self.format_latin_name(raw_name, pattern)
        return [raw2stdname[name] for name in self.names]
    
    def format_latin_name(self, raw_name, pattern):
        """Format a single scientific name according to pattern.

        Args:
            raw_name: Raw scientific name string.
            pattern: Output format (simpleName, scientificName, apiName, etc.).

        Returns:
            Formatted name in specified pattern.
        """
        split_name = self.parse_name(raw_name)
        return self.built_name_style(split_name, pattern)

    def parse_name(self, raw_name):
        """Parse scientific name into component parts.

        Supports format: genus x species author rank infraspecies infraspecific_author

        Args:
            raw_name: Scientific name string to parse. Supports hybrid symbols,
                author names, and infraspecific ranks (var., subsp., f., etc.).

        Returns:
            Tuple of (genus, species, taxon_rank, infraspecies, authors,
            first_authors, platform_rank, raw_name).
            Returns None if name cannot be parsed.
        """
        species_pattern = re.compile(
            r"((?:!×\s?|×\s?|!)?[A-Z][a-zàäçéèêëöôùûüîï-]+)\s*(×\s+|X\s+|x\s+|×)?([a-zàâäèéêëîïôœùûüÿç][a-zàâäèéêëîïôœùûüÿç-]+)?\s*(.*)")
        subspecies_pattern = re.compile(
            r"(^[\"\'（A-ZŠÁÅČ\(\.].*?[^A-Z-\s]\s*(?=$|var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.|lusus\s|\[unranked\]|×|monstr\.|proles\s))?(var\.|subvar\.|subsp\.|ssp\.|f\.|fo\.|subf\.|form\.|forma|nothosp\.|cv\.|cultivar\.|lusus\s|\[unranked\]|×|monstr\.|proles\s)?\s*([a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï][a-zàäçéèêëöôùûüîï-]+)?\s*([\"\'（A-ZÅÁŠČ\(].*?[^A-Z-])?$")
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

    def built_name_style(self, split_name, pattern):
        """Build formatted name from parsed components.

        Args:
            split_name: Tuple of parsed name components from parse_name().
            pattern: Output format (simpleName, scientificName, apiName,
                plantSplitName, fullPlantSplitName, animalSplitName).

        Returns:
            Formatted name string or tuple in specified pattern.
            Returns None values for pattern if split_name is None.
        """
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

    def fill_blank_name(self, pattern):
        """Return blank values for a given pattern.

        Used when name cannot be parsed.

        Args:
            pattern: Output format pattern.

        Returns:
            None or tuple of Nones matching pattern structure.
        """
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


    def get_similar_name(self, orgname, authors_group, names, index):
        """Select best matching name from candidates based on author similarity.

        Args:
            orgname: Original name's simple name.
            authors_group: Author team from original name, e.g., [["Hook. f.", "Thomson"], ["Wall."]].
            names: List of candidate names with their authors.
            index: Tuple of (name_key, author_key) to access name and author in each name dict.

        Returns:
            Best matching name from candidates with match_degree set.
            Returns None if no suitable match found.
        """
        length = len(names)
        new_names = list(map(self.__get_degree, (orgname for _ in range(length)), names, (index for _ in range(length)), (authors_group for _ in range(length))))
        if len(new_names) == 1:
            return new_names[0]
        else:
            degree_level = ['S3', 'S2', 'S1', 'H3', 'H2', 'H1', 'M3', 'M2', 'M1', 'E3', 'E2', 'E1', 'E0','s3', 's2', 's1', 'h3', 'h2', 'h1', 'm3', 'm2', 'm1', 'e3', 'e2', 'e1', 'e0', 'L3', 'L2', 'L1', 'L0', 'l3', 'l2', 'l1', 'l0']
            new_names.sort(key=lambda d: degree_level.index(d[-1]) if isinstance(d, tuple) else degree_level.index(d['match_degree']))
            try:
                degree1 = new_names[0][-1]
                degree2 = new_names[1][-1]
                if degree1 == degree2 and degree1[0] in ['S', 'H', 'M']:
                    print(f'\n{orgname} 在比较集中在 {degree1} 级可能有多个同名结果\n')
            except KeyError:
                degree1 = new_names[0]['match_degree']
                degree2 = new_names[1]['match_degree']
            return new_names[0]

        # author_teams = []
        # for name in names:
        #     try:
        #         authors = self.get_author_team(name[index[1]])
        #         author_teams.append(authors)
        #     except KeyError:
        #         author_teams.append([])
        # # 先根据整体的相似度获得最相似的命名人索引
        # author_team = []
        # for authors in authors_group:
        #     if authors:
        #         author_team.extend(authors)
        # scores = self.get_similar_scores(author_team, author_teams)
        # scores.sort(key=lambda s: s[0], reverse=True)
        # 得分最高的可能并不一定是最匹配的，
        # 比如['Kunze', 'Chi'] 与 [['Kunze', 'Holttum'],['Kunze', 'Ching']]
        # 得分都是 50，但是按照排序会选择第一个
        # if len(scores) > 1:
        #     name1 = names[scores[0][1]]
        #     name2 = names[scores[1][1]]
        #     name1 = self.__get_degree(orgname, name1, index, authors_group)
        #     name2 = self.__get_degree(orgname, name2, index, authors_group)
        #     degree_level = ['S3', 'S2', 'S1', 'H3', 'H2', 'H1', 'M3', 'M2', 'M1', 'E3', 'E2', 'E1', 'E0', 'L3', 'L2', 'L1', 'L0']
        #     try:
        #         degree1 = name1[-1]
        #         degree2 = name2[-1]
        #     except KeyError:
        #         degree1 = name1['match_degree']
        #         degree2 = name2['match_degree']
        #     if degree_level.index(degree1.upper()) < degree_level.index(degree2.upper()):
        #         return name1
        #     elif degree_level.index(degree1.upper()) > degree_level.index(degree2.upper()):
        #         return name2
        #     elif degree1.isupper():
        #         return name1
        #     else:
        #         return name2
        # else:
        #     name = names[scores[0][1]]
        #     return self.__get_degree(orgname, name, index, authors_group)
    
    def __get_degree(self, orgname, name, index, authors_group):
        """Calculate match degree for a name against author group.

        Args:
            orgname: Original name.
            name: Candidate name dict to evaluate.
            index: Tuple of keys to access name and author in name dict.
            authors_group: Target author team to match against.

        Returns:
            Name dict with match_degree added.
        """
        try:
            authors_group2 = self.get_author_team(name[index[1]], nested=True)
            degree = self.get_similar_degree(authors_group.copy(), authors_group2)
            name['match_degree'] = degree if orgname == name[index[0]] else degree.lower()
        except KeyError:
            name['match_degree'] = 'E0' if orgname == name[index[0]] else 'e0'
        except TypeError:
            degree = degree if orgname == name[index[0]] else degree.lower()
            name = name + (degree,)
        return name
    
    def get_similar_scores(self, author_team, author_teams):
        """Compare one author's team against multiple candidates.

        Args:
            author_team: Single author team list, e.g., ["Hook. f.", "Thomos."].
            author_teams: List of author teams to compare against.

        Returns:
            List of (score, index) tuples sorted by match score descending.
        """
        s_teams_score = []
        for n, std_team in enumerate(author_teams):
            score = self._caculate_similar_score(author_team, std_team)[0]
            s_team_score = sum(score)/len(score)
            s_teams_score.append((s_team_score, n))
        return s_teams_score

    def _caculate_similar_score(self, author_team1, author_team2):
        """Calculate similarity scores between two author teams.

        Args:
            author_team1: Author team list, e.g., ["Hook. f.", "Thomos."]. Cannot be empty.
            author_team2: Author team list to compare against. Can be empty.

        Returns:
            Tuple of (scores_list, degrees_list) with length matching author_team1.
        """
        scores = []
        degrees = []
        for author in author_team1:
            match = process.extract(
                author, author_team2, scorer=fuzz.token_sort_ratio)
            try:
                best_ratio = match[0]
            except IndexError:
                # author_team2 可能为 []
                scores.append(0)
                degrees.append(0)
                continue
            is_matched = self._is_same_author(author, best_ratio[0])
            if is_matched:
                scores.append(best_ratio[1])
                degrees.append(is_matched)
            elif len(match) > 1 and match[1][1] >= fuzz.token_sort_ratio(
                match[1][0], best_ratio[0]):
                is_matched = self._is_same_author(author, match[1][0])
                if is_matched:
                    scores.append(match[1][1])
                    degrees.append(is_matched)
                else:
                    scores.append(0)
                    if best_ratio[1] < 100:
                        degrees.append(best_ratio[1]//25)
                    else:
                        degrees.append(3)
            else:
                scores.append(0)
                if best_ratio[1] < 100:
                    degrees.append(best_ratio[1]//25)
                else:
                    degrees.append(3)

        return scores, degrees

    def get_similar_degree(self, authors_group1, authors_group2):
        """Compare authorship between two names and return similarity degree.

        Args:
            authors_group1: First author team, e.g., [["Hook. f.", "Thomson"], ["Regel"]].
            authors_group2: Second author team, e.g., [["Wall."]].

        Returns:
            String degree code:
            - 'S0'-'S3': Same publication, authors match
            - 'H0'-'H3': Same publication, some authors omitted
            - 'M0'-'M3': Possibly same, needs verification
            - 'L0'-'L3': Different publications or conflicting authors
            - 'E0'-'E3': Author spelling error, cannot compare
        """
        try:
            degree, similar = self._is_same_authorship(authors_group1, authors_group2)
            degree_translate = {3: 'S', 2: 'H', 1: 'M', 0: 'L'}
            degree = degree_translate[degree] + str(round(similar))
        except ValueError as e:
            degree = str(e)
        return degree

    def _is_same_authorship(self, authors_group1, authors_group2):
        """Compare authorship between two names using pattern matching.

        Args:
            authors_group1: First author team, e.g., [["Hook. f.", "Thomson"], ["Regel"]].
            authors_group2: Second author team, e.g., [["Wall."]].

        Returns:
            Tuple of (degree, similar):
            - degree (int): Match level (0-3)
              3: Identical author组合
              2: One has fewer authors (some omitted)
              1: Authors similar but relationship unclear
              0: Different authors
            - similar (int): Confidence score (0-3)

        Raises:
            ValueError: Authors cannot be compared.
        """
        authors1, authors2 = sorted([authors_group1, authors_group2], key=lambda v: len(v))
        comb = len(authors1), len(authors2)
        # a => a
        if comb == (1, 1):
            degree, similar = self._is_same_authors(authors_group1[0], authors_group2[0])
        elif comb == (1, 3):
            # a => a ex b
            if authors2[0] is None:
                degree1, similar1 = self._is_same_authors(authors1[0], authors2[1])
                degree2, similar2 = self._is_same_authors(authors1[0], authors2[-1])
                degree, similar = self._a_vs_aexb(degree1, degree2, similar1, similar2)
            # a => (a)b
            elif authors2[-1] is None:
                degree2, similar = self._is_same_authors(authors1[0], authors2[1])
                degree = self._a_vs_ab(degree2)
            else:
                raise ValueError('E0')
        elif comb == (3, 3):
            # a ex b => a ex b
            if authors1[0] is None and authors2[0] is None:
                degree1, similar1 = self._is_same_authors(authors1[1], authors2[1])
                degree2, similar2 = self._is_same_authors(authors1[-1], authors2[-1])
                degree, similar = self._aexb_vs_aexb(degree1, degree2, similar1, similar2)
            # a ex b => (a)b
            elif authors1[0] is None and authors2[-1] is None or authors1[-1] is None and authors2[0] is None:
                similar, degree = 0, 0
            # (a)b => (a)b
            elif authors1[-1] is None and authors2[-1] is None:
                degree1, similar1 = self._is_same_authors(authors1[0], authors2[0])
                degree2, similar2 = self._is_same_authors(authors1[1], authors2[1])
                degree, similar = self._ab_vs_ab(degree1, degree2, similar1, similar2)
            else:
                raise ValueError('E0')
        # 复杂的命名人组合 
        elif comb == (1, 4):
            if authors2[0] is None:
                del authors2[1]
                degree2, similar = self._is_same_authorship(authors1, authors2)
            elif authors2[-1] is None:
                degree2, similar = self._is_same_authorship(authors1, authors2[2:-1])
            else:
                degree2, similar = self._is_same_authorship(authors1, [None]+authors2[2:])
            degree = self._a_vs_ab(degree2)
        elif comb == (3, 4):
            if authors1[0] is None:
                if authors2[0] is None:
                    del authors2[1]
                    degree2, similar = self._is_same_authorship(authors1, authors2)
                elif authors2[-1] is None:
                    degree2, similar = 0, 0
                else:
                    degree2, similar = self._is_same_authorship(authors1, [None]+authors2[2:])
                degree = self._a_vs_ab(degree2)
            else:
                if authors2[0] is None:
                    authors11, authors21 = authors1[:1], authors2[1:2]
                    del authors2[1]
                    authors12, authors22 = authors1[1:-1], authors2
                elif authors2[-1] is None:
                    authors11, authors21 = authors1[:1], [None]+authors2[:2]
                    authors12, authors22 = authors1[1:-1], authors2[2:-1]
                else:
                    authors11, authors21 = authors1[:1], [None]+authors2[:2]
                    authors12, authors22 = authors1[1:-1], [None]+authors2[2:]
                degree1, similar1 = self._is_same_authorship(authors11, authors21)
                degree2, similar2 = self._is_same_authorship(authors12, authors22)
                degree, similar = self._ab_vs_ab(degree1, degree2, similar1, similar2)
        elif comb == (4, 4):
            authors11, authors12 = authors1[:2], authors1[2:]
            authors21, authors22 = authors2[:2], authors2[2:]
            for authors in (authors11, authors12, authors21, authors22):
                if None in authors:
                    authors.remove(None)
                else:
                    authors.insert(0, None)
            degree1, similar1 = self._is_same_authorship(authors11, authors21)
            degree2, similar2 = self._is_same_authorship(authors12, authors22)
            degree, similar = self._ab_vs_ab(degree1, degree2, similar1, similar2)
        else:
            raise ValueError('E0')
        return degree, similar
    
    def _a_vs_aexb(self, degree1, degree2, similar1, similar2):
        """Compare a vs a ex b author pattern.

        Args:
            degree1: Degree from first comparison.
            degree2: Degree from second comparison.
            similar1: Similarity from first comparison.
            similar2: Similarity from second comparison.

        Returns:
            Tuple of (degree, similar).
        """
        if degree1 == 0 and degree2 == 0:
            return 0, max(similar1, similar2)
        elif degree1 == 0:
            return degree2, similar2
        elif degree2 == 0:
            return 1, similar1
        elif degree2 == 3:
            raise ValueError('E' + str(min(similar1, similar2)))
        elif degree1 == 3 and degree2 > 0:
            raise ValueError('E' + str(min(similar1, similar2)))
        else:
            return 1, similar1
            
    def _a_vs_ab(self, degree2):
        """Compare a vs (a)b author pattern.

        Args:
            degree2: Degree from comparing b parts.

        Returns:
            Degree int (0 or 1).
        """
        if degree2 > 0:
            return 1
        else:
            return 0
    
    def _aexb_vs_aexb(self, degree1, degree2, similar1, similar2):
        """Compare a ex b vs a ex b author pattern.

        Args:
            degree1: Degree from first author comparison.
            degree2: Degree from second author comparison.
            similar1: Similarity from first comparison.
            similar2: Similarity from second comparison.

        Returns:
            Tuple of (degree, similar).
        """
        if degree1 == 0:
            return 0, similar1
        elif degree2 == 0:
            return 0, similar2
        elif degree2 == 1:
            return 1, similar2
        elif degree1 == 1:
            return 1, similar1
        elif degree2 == 3:
            return 3, min(similar1, similar2) 
        else:
            return 2, min(similar1, similar2)

    def _ab_vs_ab(self, degree1, degree2, similar1, similar2):
        """Compare (a)b vs (a)b author pattern.

        Args:
            degree1: Degree from first part comparison.
            degree2: Degree from second part comparison.
            similar1: Similarity from first comparison.
            similar2: Similarity from second comparison.

        Returns:
            Tuple of (degree, similar).
        """
        if degree1 == 0:
            return 0, similar1
        elif degree2 == 0:
            return 0, similar2
        elif degree1 == 1:
            return 1, similar1
        elif degree2 == 1:
            return 1, similar2
        elif degree1 == 3 and degree2 == 3:
            return 3, min(similar1, similar2)
        else:
            return 2, min(similar1, similar2) 

    def _is_same_authors(self, authors1, authors2):
        """Evaluate similarity between two author names.

        Args:
            authors1: First author list, e.g., ["Hook. f.", "Thomson"].
            authors2: Second author list, e.g., ["Wall."].

        Returns:
            Tuple of (degree, similar):
            - degree (int): 0-3 indicating match quality
              3: Each author in authors1 matches one in authors2
              2: Some authors missing in one group
              1: Some different authors in both groups
              0: No matching authors
            - similar (int): 0-3 indicating confidence based on key author matches.
        """
        scores, similar_degrees = self._caculate_similar_score(authors2, authors1)
        # score= sum(scores)/len(scores)
        if set(scores) == {0}: 
            degree = 0
            similar = max(similar_degrees)
        elif 0 in scores:
            similar_degrees = [similar_degrees[i] for i in range(len(scores)) if scores[i] != 0]
            if len(scores)-scores.count(0) >= len(authors1):
                degree = 2
                similar = min(similar_degrees)
            else:
                degree = 1
                similar = min(similar_degrees)
        elif len(authors1) == len(authors2):
            degree = 3
            similar = min(similar_degrees)
        else:
            degree = 2
            similar = min(similar_degrees)
        return degree, similar
    
    def _is_same_author(self, org_author1, org_author2):
        """Calculate similarity between two individual authors.

        Args:
            org_author1: First author name string.
            org_author2: Second author name string.

        Returns:
            int indicating match quality:
            3: Same person
            2: Probably same person, possible spelling difference
            1: Possibly same person, needs verification
            0: Different people
        """
        author1 = self._clean_author_for_caculate(org_author1)
        author2 = self._clean_author_for_caculate(org_author2)
        split_author1, split_author2 = author1.split(), author2.split()
        lname1, lname2 = split_author1[-1], split_author2[-1]
        if len(lname1) > len(lname2):
            org_author1, org_author2 = org_author2, org_author1
            author1, author2 = author2, author1
            split_author1, split_author2 = split_author2, split_author1
            lname1, lname2 = lname2, lname1
        fname1 = split_author1[0] if len(split_author1) > 1 else None
        fname2 = split_author2[0] if len(split_author2) > 1 else None
        # 若姓名中有四个起始字符一致，极可能是同一个人，字符起始字母通常是大写
        if lname1[:4] in author2 or lname2[:4] in author1:
            is_matched = self.__is_same_lastname(lname1, lname2, org_author1.split()[-1], fname1, fname2)
        # 前置字符允许一定的顺序倒置,这可能会不可避免的有误判, 比如 Mask. 和 Maks.
        elif set(lname1[:4]) == set(lname2[:4]) and lname1[0] == lname2[0]:
            is_matched = self.__is_same_suffix(lname1, lname2, org_author1.split()[-1])
        # 允许对姓氏中的元音进行省略简写，这里不区分大小写
        elif self._del_author_aeiou(lname1)[:4] == self._del_author_aeiou(lname2)[:4]:
            is_matched = self.__is_lastname_abbreviation(lname1)
        # 允许姓氏有一定的字符错误或丢失, 这可能会不可避免的有误判, 比如 Walp. 和 Wall.
        # 对于并不等长的字符,也可能有一定的误差, 比如 Bge. 和 Berge, Bunge 就难以区分
        elif fuzz.token_sort_ratio(lname1[:4], lname2[:4]) > 50 and lname1[0] == lname2[0]:
            is_matched = self.__is_same_suffix(lname1, lname2, org_author1.split()[-1], strloss=True)
        # elif 这里未来还可以补充首字母变体，比如 U V I L G C 之间等
        else:
            is_matched = 0
        # 对名进行约束，以尽可能避免姓氏相同的人被误判
        is_matched = self.__is_same_name(fname1, fname2, author1, author2, split_author1, split_author2, is_matched)
        return is_matched
    
    def __is_same_name(self, fname1, fname2, author1, author2, split_author1, split_author2, lastname_matched):
        """Compare given names to validate last name match.

        Args:
            fname1: First given name or None.
            fname2: Second given name or None.
            author1: First full author string.
            author2: Second full author string.
            split_author1: First author split into parts.
            split_author2: Second author split into parts.
            lastname_matched: Result from last name comparison.

        Returns:
            Match quality int (0-3).
        """
        if lastname_matched:
            if fname1 and fname2:
                if fname1[0] in author2 and fname2[0] in author1:
                    if len(split_author1) == len(split_author2):
                        if split_author1[1][0] in author2 and split_author2[1][0] in author1:
                            is_matched = 3
                        else:
                            is_matched = 0
                    else:
                        is_matched = 1
                else:
                    is_matched = 0
            else:
                is_matched = lastname_matched
        else:
            is_matched = 0
        return is_matched
    
    def __is_same_lastname(self, lname1, lname2, org_lname1, fname1, fname2):
        """Check if last names match considering common suffixes.

        Args:
            lname1: First last name (shortened).
            lname2: Second last name (shortened).
            org_lname1: Original first last name.
            fname1: First given name or None.
            fname2: Second given name or None.

        Returns:
            Match quality int (0-3).
        """
        if lname2.startswith(lname1[:4]):
            is_matched = self.__is_same_suffix(lname1, lname2, org_lname1, strloss=False)
        else:
            is_matched = 0
        if is_matched == 0:
            if len(lname1) > 3 and fname2 and fname2.startswith(lname1[:4]):
                is_matched = 1
            elif len(lname2) > 3 and fname1 and fname1.startswith(lname2[:4]):
                is_matched = 1
            else:
                is_matched = 0
        return is_matched

    def __is_same_suffix(self, lname1, lname2, org_lname1, strloss=None):
        """Compare last name suffixes for similarity.

        Args:
            lname1: First last name.
            lname2: Second last name.
            org_lname1: Original first last name.
            strloss: If False, strict matching; otherwise allow losses.

        Returns:
            Match quality int (0-3).
        """
        if lname1 == lname2:
            is_matched = 3
        elif lname2[-3:] in ('ung', 'ang', 'ing', 'ong', 'eng') and lname1[-3:] not in ('ung', 'ang', 'ing', 'ong', 'eng') and len(lname2)-len(lname1) < 3:
            is_matched = 0
        elif len(lname1) > 4:
            suffix1, suffix2 = lname1[4:], lname2[4:]
            if fuzz.token_sort_ratio(suffix1, suffix2[:len(suffix1)]) >= 50:
                if strloss is False:
                    is_matched = 3
                else:
                    is_matched = 2
            elif len(lname1) == 5:
                if strloss is None:
                    is_matched = 0
                else:
                    is_matched = 2
            elif self._del_author_aeiou(suffix1) in self._del_author_aeiou(suffix2):
                is_matched = 2
            else:
                is_matched = 0
        elif len(lname1) == 4:
            if strloss is False:
                is_matched = 3
            else:
                is_matched = 2
        elif len(lname1) == 1:
            if lname1 == 'L':
                if lname2 in ("Lin", "Linn") or lname2.startswith("Linn"):
                    is_matched = 3
                else:
                    is_matched = 0
            else:
                is_matched = 0
        elif len(lname2) - len(lname1) > 2:
            if strloss is False:
                if org_lname1.endswith('.'):
                    is_matched = 3
                else:
                    is_matched = 1
            else:
                if org_lname1.endswith('.'):
                    is_matched = 2
                else:
                    is_matched = 1
        else:
            if strloss is False:
                if org_lname1.endswith('.'):
                    is_matched = 3
                else:
                    is_matched = 1
            elif len(lname1) == 2:
                # Ha, Hfa, Hfae
                is_matched = 1
            elif strloss is None and len(lname2) == 3:
                is_matched = 2
            else:
                is_matched = 1
            
        return is_matched
    
    def __is_lastname_abbreviation(self, lname1):
        """Check if last name is an abbreviation.

        Args:
            lname1: Last name to check.

        Returns:
            Match quality int (1-3) based on abbreviation patterns.
        """
        short_name = self._del_author_aeiou(lname1)
        if len(short_name) == 1:
            is_matched = 1
        elif len(short_name) == 2 and lname1[:2] in ['Ch', 'Sh', 'Zh']:
            is_matched = 1
        elif len(short_name) == 2 and lname1[-3:] in ('ang', 'ing', 'ong', 'eng'):
            is_matched = 2
        elif len(short_name) == 3 and lname1[-3:] in ('ang', 'ing', 'ong', 'eng'):
            is_matched = 2
        else:
            is_matched = 3
        return is_matched

    def _clean_author_for_caculate(self, author):
        """Clean author name for similarity calculation.

        Normalizes punctuation, converts special characters, and handles
        common abbreviations like 'de Candolle' -> 'DC'.

        Args:
            author: Author name string.

        Returns:
            Cleaned author string.
        """
        aut = author.replace("-", "")\
                    .replace(".", " ")\
                    .replace("'", " ")\
                    .replace("  ", " ")\
                    .strip()\
                    .replace('de Candolle', 'DC')\
                    .replace('C Muell', 'Müll Hal')\
                    .replace('B S G', 'Bruch, Schimper & Guembel')
        aut = aut.replace(' f', '') if aut.endswith(' f') else aut
        aut = aut.replace(' p p', '') if aut.endswith(' p p') else aut
        return aut
    
    def _del_author_aeiou(self, author):
        """Remove vowels from author name for comparison.

        Args:
            author: Author name string.

        Returns:
            Author name with vowels removed (lowercased).
        """
        author = author.replace('un', '') if 'un' in author[1:] and not author.endswith('un') else author
        author = author.replace('in', '') if 'in' in author[1:] and not author.endswith('in') else author
        author = author.replace('on', '') if 'on' in author[1:] and not author.endswith('on') else author
        author = author.replace('en', '') if 'en' in author[1:] and not author.endswith('en') else author
        author = author.replace('an', '') if 'an' in author[1:] and not author.endswith('an') else author
        author = author[0] + re.sub(r'[aeiouy]', '', author[1:])
        return author.lower()

    def get_author_team(self, authors, nested=False):
        """Split authorship string into groups of authors.

        Args:
            authors: Author string, e.g., "Hook. f. & Thomson ex Regel".
            nested: If True, return nested list structure showing
                publication relationships.

        Returns:
            List of author groups. When nested=False:
            ["Hook. f.", "Thomson", "Regel"]
            When nested=True:
            [["Hook. f.", "Thomson"], ["Regel"]]
            Returns empty list if authors is empty or invalid.
        """
        try:
            authors = self.format_authorship(authors)
            authors = self.ascii_authors(authors)
            return self._segment_authorship(authors, nested=nested)
        # authors 为空, 或者拼写有误
        except (AttributeError, ValueError):
            return [] 

    def format_authorship(self, authorship):
        """Normalize authorship string formatting.

        Standardizes separators like &, et, ex, in, and punctuation.

        Args:
            authorship: Author string to format.

        Returns:
            Formatted author string.
        """
        authorship = authorship.replace('&', ' & ')\
                                .replace(' et ', '  & ')\
                                .replace(' ex ', '  ex ')\
                                .replace(' in ', '  in ')\
                                .replace(',', ', ')\
                                .replace(')', ') ')\
                                .replace('）', ') ')\
                                .replace('（', '(')\
                                .replace('. ', '.')\
                                .replace('.&', '. &')\
                                .replace('  ', ' ')
        if authorship.startswith('('):
            if ' in ' in authorship and authorship.find(')') > authorship.find(' in '):
                # authorship 等于 in 之前的字符串加上 ) 后的字符串
                authorship = authorship[:authorship.find(' in ')] + authorship[authorship.find(')'):]
        # 排除 authorship 中 in 后的命名人
        authorship = authorship.split(' in ')[0].strip() if ' in ' in authorship else authorship
        return authorship.strip()

    def ascii_authors(self, authors, discard=True):
        """Convert author names to ASCII characters.

        Handles special characters like ß, æ, Ø, ø, þ, ð.

        Args:
            authors: Author string to convert.
            discard: If True, characters that can't be converted are discarded.
                If False, they're preserved.

        Returns:
            ASCII-converted author string.
        """
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

    def strip_accents(self, text):
        """Convert Latin characters to ASCII equivalents.

        Args:
            text: String to convert, e.g., 'PančićDiklić & V.NikolićØ'.

        Returns:
            ASCII-converted string. Some characters may be deleted
            if they cannot be converted.
        """
        text = unicodedata.normalize('NFD', text)
        # 将命名人中的不同字符尽可能转化为 a-ZA-Z
        # 比如 PančićDiklić & V.Nikolić 转换为 PancicDiklic & V.Nikolic
        # 注意：字符串中的一些特殊字符可能无法转换，比如字符 Ø， 这些字符将被从字符串中删除
        ascii_text = text.encode('ascii', 'ignore').decode('utf-8')
        return ascii_text

    def _segment_authorship(self, authorship, nested=False):
        """Split authorship string into groups.

        Handles patterns like:
        - "Hook. f. & Thomson"
        - "Hook. f. & Thomson ex Regel"
        - "(Hayata) Ching"
        - "(Hayata) Ching ex S.H.Wu"
        - "(Bedd. ex C.B.Clarke & Baker) Ching"

        Args:
            authorship: Author string to segment.
            nested: If True, return nested list showing publication relationships.

        Returns:
            When nested=False: flat list like ["Hook. f.", "Thomson", "Regel"]
            When nested=True: nested structure showing ex/in relationships.
            See docstring examples for details.

        Raises:
            ValueError: If authorship format is invalid.
        """
        p = re.compile(
            r"(?:^|\(\s*|\s+et\s+|\s+ex\s+|\&\s*|\,\s*|\)\s*|\s+and\s+|\[\s*|\（\s*|\）\s*|\，\s*|\{\s*|\}\s*)([^\s\&\(\)\,\;\.\-\?\，\（\）\[\]\{\}][^\&\(\)\,\;\，\（\）\[\]\{\}]+?(?=\s+ex\s+|\s+et\s+|\s*\&|\s*\,|\s*\)|\s*\(|\s+and\s+|\s+in\s+|\s*\）|\s*\（|\s*\，|\s*\;|\s*\]|\s*\[|\s*\}|\s*\{|\s*$))")
        if not nested:
            author_team = p.findall(authorship)
            author_team = self.check_author_team(author_team)
            return author_team
        author_team = authorship.split(')')
        author_team = author_team[0].split(' ex ') + author_team[1:]
        author_team = author_team[:-1] + author_team[-1].split(' ex ')
        if len(author_team) == 1:
            pass
        elif len(author_team) == 2:
            if authorship.startswith('(') and ')' in authorship:
                author_team.append(None)
            elif ' ex ' in authorship:
                author_team.insert(0, None)
            else:
                raise ValueError
        elif len(author_team) == 3 and authorship.startswith('('):
            if ')' in authorship and ' ex ' in authorship:
                if authorship.find(' ex ') > authorship.find(')'):
                    author_team.insert(0, None)
                else:
                    author_team.append(None)
            else:
                raise ValueError
        elif len(author_team) == 4 and authorship.count(' ex ') == 2:
            pass
        else:
            raise ValueError
        # 命名人可能是有一至多个部分组成，这里通过四种模式猜测可能的名称组成形式
        for i, author in enumerate(author_team):
            if author is None:
                continue
            author_team[i] = self.check_author_team(p.findall(author.strip()))
        if [] in author_team:
            raise ValueError
        return author_team
    
    def check_author_team(self, author_team):
        """Filter out non-author elements from author team.

        Removes lowercase-only elements like "comb. nov." or "cons. stat."
        that may have been incorrectly parsed as authors.

        Args:
            author_team: List of author strings.

        Returns:
            Filtered list with non-author elements removed.
        """
        new_author_team = []
        for author in author_team:
            if author.islower() and not author.startswith('hort'):
                continue
            else:
                new_author_team.append(author)
            
        return new_author_team


    def __call__(self, mark=True):
        """Process names and return DataFrame with specified style.

        Optionally performs online verification against IPNI, POWO, Tropicos,
        and COL. Returns DataFrame matching the configured style.

        Args:
            mark: If True, failed queries are marked with '!' prefix.

        Returns:
            DataFrame with processed names in the configured style.
            For failed queries with mark=True, names are prefixed with '!'.
            If all queries fail, returns DataFrame with None values.
        """
        if self.style == 'scientificName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n\n")
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
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n\n")
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
        elif self.style == 'apiName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            (name[0].strip(), name[1])
                            if name[1] else (name[0], None)
                            for name in results
                        ]
                    )
                else:
                    return pd.DataFrame([[None, None]]*len(self.names))
            else:
                return pd.DataFrame(self.format_latin_names(pattern="apiName"))
        elif self.style == 'plantSplitName':
            choose = input(
                "\n是否执行拼写检查，在线检查将基于 IPNI、POWO、Tropicos、COL China 进行，但这要求工作电脑一直联网，同时如果需要核查的名称太多，可能会耗费较长时间（y/n）\n\n")
            if choose.strip() == 'y':
                results = self.get('stdName', mark=mark)
                if results:
                    return pd.DataFrame(
                        [
                            self.parse_name(name[0].strip())[:4] + (name[1],)
                            if name[1] else self.built_name_style(self.parse_name(name[0].strip()), 'plantSplitName')
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

if __name__ == '__main__':
    name = BioName(['Adonis caerulea'])
    table = pd.read_excel(r"/Users/xuzhoufeng/Library/CloudStorage/OneDrive-个人/PDP/noiname/test/Version1.0.0.xlsx")
    names = table['fullName']
    mathced = name.get(names)
    print(mathced)
