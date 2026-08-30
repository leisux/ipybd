"""CVH (China Virtual Herbarium) API client.

Provides access to specimen data from CVH database.
"""

from argparse import ArgumentError
import asyncio
import aiohttp
import requests
# Disable SSL verification warnings
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from time import sleep
from tqdm import tqdm
import urllib


QUERY_API = 'https://www.cvh.ac.cn/controller/spms/list.php?'
INFO_API = 'https://www.cvh.ac.cn/controller/spms/detail.php?'
WEB_URL = 'https://www.cvh.ac.cn/spms/detail.php?'


class LinkCVH:
    """Client for CVH (China Virtual Herbarium) API.

    Provides methods to query specimen records with support for
    pagination and detail retrieval.

    Args:
        cache: If True, store results in cache.
        detail: If True, fetch detailed records.
    """

    def __init__(self, cache=True, detail=False):
        self.enable_cache = cache
        self.cache = {}
        self.detail = detail

    def build_cache(self, results):
        """Build cache from query results.

        Args:
            results: List of specimen records.
        """
        for res in results:
            try:
                self.cache[res.pop('collectionID')] = res
            except TypeError:
                pass

    def _unpack_pages_result(self, pages_result):
        """Flatten page results into single list.

        Args:
            pages_result: List of result lists.

        Returns:
            Flattened list of results.
        """
        results = []
        for result in pages_result:
            results.extend(result)
        return results

    def _supplement_info(self, params, results):
        """Add reference URLs and query keywords to results.

        Args:
            params: Query parameters.
            results: List of records to supplement.

        Returns:
            Updated results with references and keywords.
        """
        del params['offset']
        keywords = '，'.join(list(params.values()))
        for result in results:
            result['references'] = 'id='.join([WEB_URL, result['collectionID']])
            result['queryKeywords'] = keywords
        return results

    def get(self, taxonName=None, family=None, genus=None, country=None, stateProvince=None,
            county=None, locality=None, minimumElevation=None, maximumElevation=None,
            recordedBy=None, recordNumber=None, collectedYear=None, institutionCode=None,
            collectionCode=None, identifiedBy=None, dateIdentified=None, withPhoto=False,
            typesOnly=False, hasFruit=False, hasFlower=False, hasMolecularMaterial=False):
        """Query CVH for specimen records.

        Args:
            taxonName: Scientific name to search.
            family: Family name.
            genus: Genus name.
            country: Country name.
            stateProvince: State or province.
            county: County name.
            locality: Locality description.
            minimumElevation: Minimum elevation.
            maximumElevation: Maximum elevation.
            recordedBy: Collector name.
            recordNumber: Collection number.
            collectedYear: Year collected.
            institutionCode: Institution code.
            collectionCode: Collection code.
            identifiedBy: Identifier name.
            dateIdentified: Date identified.
            withPhoto: Only records with photos.
            typesOnly: Only type specimens.
            hasFruit: Only records with fruit.
            hasFlower: Only records with flowers.
            hasMolecularMaterial: Only records with molecular material.

        Returns:
            List of specimen records, or None if caching enabled.
        """
        params = self.build_params(locals())
        headers = self.build_headers()
        pages = self.query(QUERY_API, params, headers)
        pages_result = self.mult_get(QUERY_API, params, headers, range(pages))
        results = self._unpack_pages_result(pages_result)
        if self.detail:
            ids = [specimen['collectionID'] for specimen in results]
            results = self.mult_get(INFO_API, {}, headers, ids)
        # 由于 CVH 返回的结果中不包含小地点和页面的 URL
        # 这里将查询关键词以及页面 URL 一并组装到表格
        # 将查询结果以字典形式缓存，缓存的 key 为 CVH 的 uuid/collectionID
        results = self._supplement_info(params, results)
        if self.enable_cache:
            self.build_cache(results)
        else:
            return results

    def mult_get(self, api, params, headers, pages_or_ids):
        """Query API for multiple pages or IDs.

        Args:
            api: API endpoint URL.
            params: Query parameters.
            headers: HTTP headers.
            pages_or_ids: List of page numbers or record IDs.

        Returns:
            List of results from all pages/IDs.
        """
        self.pbar = tqdm(total=len(pages_or_ids), desc='列表数据获取', ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sema = asyncio.Semaphore(50)
        tasks = self.build_tasks(api, params, headers, pages_or_ids)
        results = loop.run_until_complete(tasks)
        # 修复 Windows 下出现的 RuntimeErro: Event loop is closed
        # 为什么注销 close 会管用，我也没完全搞清楚
        # 猜测可能是 asyncio 会自动关闭 loop
        # 暂且先这样吧！
        # loop.close()
        self.pbar.close()
        return results

    async def build_tasks(self, api, params, headers, pages_or_ids):
        """Build async tasks for concurrent API requests.

        Args:
            api: API endpoint.
            params: Query parameters.
            headers: HTTP headers.
            pages_or_ids: List of pages or IDs to fetch.

        Returns:
            List of results from gather.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.get_track(
                    self.build_url(api, params, arg),
                    headers,
                    session
                )
                for arg in pages_or_ids
            ]
            return await asyncio.gather(*tasks)

    async def get_track(self, url, headers, session):
        """Fetch single page/record with semaphore control.

        Args:
            url: URL to fetch.
            headers: HTTP headers.
            session: aiohttp session.

        Returns:
            Result dictionary from API.
        """
        async with self.sema:
            response = await self.async_get(url, headers, session)
            self.pbar.update(1)
            result = response['rows']
            try:
                result['collectionID'] = result['uuid']
                del result['uuid']
            except TypeError:
                pass
            return result

    def build_url(self, api, params, page_or_id=False):
        """Build complete API URL with parameters.

        Args:
            api: API endpoint.
            params: Query parameters dict.
            page_or_id: Page number (int) or record ID.

        Returns:
            Complete URL string.
        """
        if isinstance(page_or_id, int):
            params['offset'] = page_or_id * 30
        else:
            params['id'] = page_or_id
        url =  '{base}&{opt}'.format(
               base=api,
               opt=urllib.parse.urlencode(params)
        )
        return url

    async def async_get(self, url, headers, session):
        """Perform async HTTP GET request.

        Args:
            url: URL to fetch.
            headers: HTTP headers.
            session: aiohttp session.

        Returns:
            JSON response or None on failure.
        """
        try:
            while True:
                print(url)
                async with session.get(url, headers=headers, timeout=60, ssl=False) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(10)
                    else:
                        response = await resp.json()
                        break
        except BaseException:
            response = await self.single_get(url, headers)
        if not response:
            print(url, "联网超时，请检查网络连接！")
        return response

    async def single_get(self, url, headers):
        """Fallback synchronous GET request.

        Args:
            url: URL to fetch.
            headers: HTTP headers.

        Returns:
            JSON response or None on failure.
        """
        try:
            while True:
                rps = requests.get(url, headers=headers, verify=False)
                if rps.status_code == 429:
                    await asyncio.sleep(10)
                else:
                    return rps.json()
        except BaseException:
            return None

    def query(self, api, params, headers):
        """Query API to get total pages.

        Args:
            api: API endpoint.
            params: Query parameters.
            headers: HTTP headers.

        Returns:
            Number of pages.

        Raises:
            ValueError: If no results found.
        """
        while True:
            rps = requests.get(api, params, headers=headers, verify=False)
            if rps.status_code == 429:
                sleep(3)
            else:
                total = rps.json()['total']
                if total == 0:
                    raise ValueError("没有查询到相应结果")
                elif total%30 == 0:
                    return total//30
                else:
                    return total//30 + 1

    def build_headers(self):
        """Build HTTP headers for CVH API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://www.cvh.ac.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44'
        }

    def build_params(self, arguments):
        """Build query parameters from arguments.

        Args:
            arguments: Dictionary of search parameters.

        Returns:
            Cleaned parameters dict.
        """
        params = {k: v for k, v in arguments.items() if v}
        del params['self']
        if params:
            return params
        else:
            raise ArgumentError("参数传递有误!")
