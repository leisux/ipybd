from argparse import ArgumentError
import asyncio
import aiohttp
import pandas as pd
import requests
from time import sleep
from tqdm import tqdm
import urllib


QUERY_API = 'https://www.cvh.ac.cn/controller/spms/list.php?stateProvince%5B%5D=广东省%21'
INFO_API = 'https://www.cvh.ac.cn/controller/spms/detail.php?'
WEB_URL = 'https://www.cvh.ac.cn/spms/detail.php?'


class LinkCVH:
    def __init__(self, cache=True, detail=False):
        self.enable_cache = cache
        self.cache = {}
        self.detail = detail

    def build_cache(self, results):
        for res in results:
            try:
                self.cache[res.pop('collectionID')] = res
            except TypeError:
                pass

    def _unpack_pages_result(self, pages_result):
        results = []
        for result in pages_result:
            results.extend(result)
        return results

    def _supplement_info(self, params, results):
        del params['offset']
        keywords = '，'.join(list(params.values()))
        for result in results:
            result['references'] = 'id='.join([WEB_URL, result['collectionID']])
            result['queryKeywords'] = keywords
        return results
        
    def get(self, taxonName=None, family=None, genus=None, country=None, 
            county=None, locality=None, minimumElevation=None, maximumElevation=None,
            recordedBy=None, recordNumber=None, collectedYear=None, institutionCode=None,
            collectionCode=None, identifiedBy=None, dateIdentified=None, withPhoto=False,
            typesOnly=False, hasFruit=False, hasFlower=False, hasMolecularMaterial=False):
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
        """ 检索 WEB API，获得检索结果

        return: 返回由字典组成的列表，每个字典为一个查询结果
        """
        self.pbar = tqdm(total=len(pages_or_ids), desc='列表数据获取', ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sema = asyncio.Semaphore(50, loop=loop)
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
        async with self.sema:
            response = await self.async_get(url, headers, session)
            self.pbar.update(1)
            result = response['rows']
            # 将 detail 的结果中 uuid 改名为 collectionID
            # 以便遵从 DarwinCore ，同时与非 detail 模式下
            # 返回的页面列表结果保持统一
            try:
                result['collectionID'] = result['uuid']
                del result['uuid']
            except TypeError:
                pass
            return result

    def build_url(self, api, params, page_or_id=False):
        if isinstance(page_or_id, int):
            params['offset'] = page_or_id
        else:
            params['id'] = page_or_id
        return '{base}&{opt}'.format(
               base=api,
               opt=urllib.parse.urlencode(params)
        )

    async def async_get(self, url, headers, session):
        try:
            while True:
                # print(url)
                async with session.get(url, headers=headers, timeout=60) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(10)
                    else:
                        response = await resp.json()
                        # print(response)
                        break
        except BaseException:  # 如果异步请求出错，改为正常的 Get 请求以尽可能确保有返回结果
            response = await self.single_get(url)
        if not response:
            print(url, "联网超时，请检查网络连接！")
        return response  # 返回 None 表示网络有问题

    async def single_get(self, url, headers):
        try:
            while True:
                rps = requests.get(url, headers=headers)
                # print(rps.status_code)
                if rps.status_code == 429:
                    await asyncio.sleep(10)
                else:
                    return rps.json()
        except BaseException:
            return None

    def query(self, api, params, headers):
        while True:
            rps = requests.get(api, params, headers=headers)
            # print(rps.status_code)
            if rps.status_code == 429:
                sleep(3)
            else:
                total = rps.json()['total']
                if total:
                    return total//30 + 1
                else:
                    raise ValueError("没有查询到相应结果")

    def build_headers(self):
        return {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://www.cvh.ac.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44'
        }

    def build_params(self, arguments):
        params = {k: v for k, v in arguments.items() if v}
        del params['self']
        if params:
            return params
        else:
            raise ArgumentError("参数传递有误!")
