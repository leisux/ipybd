from argparse import ArgumentError
import asyncio

import aiohttp
import arrow
import pandas as pd
import requests
from tqdm import tqdm


QUERY_API = 'https://www.cvh.ac.cn/controller/spms/list.php'
INFO_API = 'https://www.cvh.ac.cn/controller/spms/detail.php'


class CvhData:
    def __init__(self, taxonName=None, family=None, genus=None, country=None, 
                county=None, locality=None, minimumElevation=None, maximumElevation=None, 
                recordedBy=None, recordNumber=None, collectedYear=None, institutionCode=None,
                collectionCode=None, identifiedBy=None, dateIdentified=None, withPhoto=False, 
                typesOnly=False, hasFruit=False, hasFlower=False, hasMolecularMaterial=False):
        self.taxonName = taxonName
        self.family = family
        self.genus = genus
        self.country = country
        self.county = county
        self.locality = locality
        self.minimumElevation = minimumElevation
        self.maximumElevation = maximumElevation
        self.recordedBy = recordedBy
        self.recordNumber = recordNumber
        self.year = collectedYear
        self.institutionCode = institutionCode
        self.collectionCode = collectionCode
        self.identifiedBy = identifiedBy
        self.dateIdentified = dateIdentified
        self.withPhoto = withPhoto
        self.typesOnly = typesOnly
        self.hasFruit = hasFruit
        self.hasFlower = hasFlower
        self.hasMolecularMaterial = hasMolecularMaterial


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
        self.pbar = tqdm(total=len(search_terms), desc=action, ascii=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.sema = asyncio.Semaphore(500, loop=loop)
        tasks = self.build_tasks(get_action[action], search_terms)
        results = loop.run_until_complete(tasks)
        # 修复 Windows 下出现的 RuntimeErro: Event loop is closed
        # 为什么注销 close 会管用，我也没完全搞清楚
        # 猜测可能是 asyncio 会自动关闭 loop
        # 暂且先这样吧！
        #loop.close()
        self.pbar.close()

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

    async def get_powo_name(self, query, session):
        """ 从 KEW API 返回的最佳匹配中，获得学名及其科属分类阶元信息

            query: (simple_name, rank, author, raw_name)
            api: KEW 的数据接口地址
            return：raw_name, scientificName, family, genus
        """
        name = await self.check_powo_name(query, session)
        if name:
            return query[-1], name, 'powo'

    def build_request_info(self):
        policy = self.build_policy()
        token = self.get_token(policy)
        data = {"policy": policy.decode('utf-8')}
        return data, token

    async def kew_search(self, query, filters, api, session):
        params = self._build_params(query, filters)
        resp = await self.async_get(self.build_url(api), session)
        try:
            return resp['results']
        except (TypeError, KeyError):
            return None

    async def async_get(self, url, headers, session):
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
            response = await self.get(url)
        if not response:
            print(url, "联网超时，请检查网络连接！")
        return response  # 返回 None 表示网络有问题

    async def get(self, url, headers):
        try:
            while True:
                rps = requests.get(url, headers=headers)
                # print(rps.status_code)
                if rps.status_code == 429:
                    await asyncio.sleep(3)
                else:
                    return rps.json()
        except BaseException:
            return None

    def build_headers(self):
        headers = json.dumps(
            {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-encoding': 'gzip, deflate, br',
                'referer': 'https://www.cvh.ac.cn',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44'
            },
            ensure_ascii=False
        )
        return base64.b64encode(headers.encode('utf-8'))

    def build_url(self, api):
        params = self._build_params()
        return '{base}?{opt}'.format(
               base=api,
               opt=urllib.parse.urlencode(params)
        )

    def _build_params(self):
        params = {k:v for k,v in self.__dict__.items() if v}
        if params:
            return params
        else:
            raise ArgumentError
        


#!/usr/bin/python
# -*- coding=utf8 -*-
"""
# @Author : Xu Zhoufeng
# @Created Time : 2020-09-03 09:53:46
# @Description :https://github.com/leisux/ipybd
"""

import asyncio
import base64
import hmac
import json
import urllib.parse
import urllib.request
from hashlib import sha1
from json.decoder import JSONDecodeError

import aiohttp
from tqdm import tqdm

from ipybd.core import NpEncoder

URL = "https://noi.link/api/data_add"
UPDATE_ID_URL = "https://noi.link/api/data_update"
ACCESSKEY = ""
SECRETKEY = ""


class Api:
    """ noi.link Post Data API

        实现单条记录的注册
    """
    def __init__(
            self, json_data, rights, data_from, data_model_id):
        self.data = json_data
        self.rights = rights
        self.data_from = data_from
        self.model_id = data_model_id

    def post(self, url):
        data, token = self.build_post_info()
        postdata = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, postdata)
        req.add_header("token", token)
        res = urllib.request.urlopen(req)
        html = res.read()
        print(html)

    def build_post_info(self):
        policy = self.build_policy()
        token = self.get_token(policy)
        data = {"policy": policy.decode('utf-8')}
        return data, token

    def build_policy(self):
        json_policy = json.dumps(
            {
                'data_info': self.data,
                'data_from': self.data_from,
                'data_copyright': self.rights,
                'data_modelid': self.model_id
            },
            ensure_ascii=False
        )
        return base64.b64encode(json_policy.encode('utf-8'))

    def get_token(self, policy):
        digest = hmac.new(SECRETKEY.encode('utf-8'), policy, sha1).digest()
        digest_b64 = base64.b64encode(digest)
        sign = digest_b64.decode('utf-8')
        return ":".join([ACCESSKEY, sign])


class UpdateID(Api):
    """ update occurrenceID of noi.link occurrence object

        occurrencID 是用户更新 noi occurrence 对象的唯一 ID
        一般该 ID 不会发生改变, 如果该 ID 发生改变或者发生错误,
        可以借助已经注册获得的 NOI 更新 occurrenceID
    """
    def __init__(self, noi, new_id):
        self.noi = noi
        self.new_id = new_id

    def build_policy(self):
        json_policy = json.dumps(
            {
                'noi':self.noi,
                'occurrenceID': self.new_id
            }
        )
        return base64.b64encode(json_policy.encode('utf-8'))


class Link:
    """ 使用协程实现记录批量注册 noi.link

        对于未注册成功的记录，会以json文件保存在相应路径下
        对于已经注册成功的记录，会议json文件将返回结果保存在相应路径下
    """
    def __init__(self, dict_in_list_datas, file_path, accesskey, secretkey, model_id=1):
        self.datas = dict_in_list_datas
        self.model_id = model_id
        self.file_path = file_path
        self.url = URL
        global ACCESSKEY
        global SECRETKEY
        ACCESSKEY = accesskey
        SECRETKEY = secretkey

    def register(self):
        responses = self.add()
        valid_resps = {}
        unvalid_resps = []
        for resp, data in zip(responses, self.datas):
            if resp:
                valid_resps[data['Occurrence']['occurrenceID']] = resp
            else:
                unvalid_resps.append(data)
        if valid_resps:
            with open(self.file_path+'_valid_resps.json', "w", encoding='utf-8') as f:
                json.dump(valid_resps, f, cls=NpEncoder, sort_keys=False,
                          indent=2, separators=(',', ': '), ensure_ascii=False)
        if unvalid_resps:
            with open(self.file_path+'_unpost.json', "w", encoding='utf-8') as f:
                json.dump(unvalid_resps, f, cls=NpEncoder, sort_keys=False,
                           indent=2, separators=(',', ': '), ensure_ascii=False)

    def add(self):
        self.pbar = tqdm(total=len(self.datas), desc="注册数据", ascii=True)
        loop = asyncio.get_event_loop()
        self.sem = asyncio.Semaphore(100, loop=loop)
        tasks = self.build_tasks()
        resp = loop.run_until_complete(tasks)
        loop.close()
        self.pbar.close()
        return resp

    async def build_tasks(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.limit_sem(data, session) for data in self.datas]
            return await asyncio.gather(*tasks)

    async def limit_sem(self, data, session):
        async with self.sem:
            postdata, token = self.build_post_data(data)
            result = await self.fetch(postdata, token, session)
            self.pbar.update(1)
            return result

    def build_post_data(self, data: dict):
        rights = data["Record"]["rightsHolder"]
        data_from = data["Record"]["dataFrom"]
        json_data = json.dumps(data, cls=NpEncoder, ensure_ascii=False)
        # print(json_data)
        api = Api(
            json_data,
            rights,
            data_from,
            self.model_id)
        return api.build_post_info()

    async def fetch(self, data: 'json', token, session):
        while True:
            try:
                async with session.post(self.url,
                                        data=data,
                                        headers={"token": token}
                                        ) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(3)
                        continue
                    elif resp.status == 200:
                        try:
                            response = await resp.json(content_type='text')
                            return self.get_data(response)
                        except aiohttp.ClientPayloadError as e:
                            # 这个错误的具体原因尚未弄清楚
                            # 在遭遇这个错误之后，我们验证了 noi 数据库
                            # 发现相应的索引其实已经注册
                            # 但这到目前这只是个例，且原因不明，
                            # 所以权衡之下，先返回 None 以默认未注册成功
                            # 同时也不再循环注册，后续是否继续注册，交由用户自行决定
                            return None
                        except JSONDecodeError as e:
                            # 这个错误，目前原因不明
                            # 数据库端解析请求，提示 401 错误
                            # 索引数据没有注册成功，sleep后重新执行注册
                            await asyncio.sleep(5)
                            continue
            except aiohttp.ServerDisconnectedError:
                # print(">server connect error! May be you are too fast!\n")
                await asyncio.sleep(3)
                continue
            except (ConnectionResetError, aiohttp.ClientOSError):
                await asyncio.sleep(3)
                continue
            except asyncio.TimeoutError:
                await asyncio.sleep(3)
                continue

    def get_data(self, response):
        if response['code'] == 200:
            return response['data']
        else:
            self.error_print(response)
            return None

    def error_print(self, response):
        if response['code'] == 400:
            print("\n请求报文格式错误 包括上传时，上传表单格式错误")
        elif response['code'] == 401:
            print("\n认证授权失败 错误信息包括密钥信息不正确；数字签名错误；授权已超时")
        elif response['code'] == 403:
            print("\n权限不足，拒绝访问\n")
        elif response['code'] == 404:
            print("\n资源不存在 包括空间资源不存在；镜像源资源不存在\n")
        elif response['code'] == 502:
            print("\n错误网关\n")
        elif response['code'] == 503:
            print("\n服务端不可用\n")
        elif response['code'] == 504:
            print("\n服务端tt操作超时\n")
        elif response['code'] == 599:
            print("\n服务端操作失败\n")
        elif response['code'] == 601:
            print("\n用户账户冻结\n")
        else:
            print("\n错误代码：{}\n".format(response['code']))


class UpdateIDs(Link):
    def __init__(self, dict_in_list_datas, file_path, accesskey, secretkey, model_id=1):
        super(UpdateIDs, self).__init__(dict_in_list_datas, file_path, accesskey, secretkey, model_id)
        self.url = UPDATE_ID_URL

    def build_post_data(self, data):
        noi = data['noi']
        occurrenceID = data['occurrenceID']
        json_data = json.dumps(data, cls=NpEncoder, ensure_ascii=False)
        api = UpdateID(noi, occurrenceID)
        return api.build_post_info()

    def get_data(self, response):
        if response['code'] == 200:
            return True
        else:
            print(response)
            self.error_print(response)
            return None

    def update(self):
        responses = self.add()
        unvalid_resps = []
        for resp, data in zip(responses, self.datas):
            if resp:
                pass
            else:
                unvalid_resps.append(data)
        if unvalid_resps:
            with open(self.file_path+'_unpost.json', "w", encoding='utf-8') as f:
                json.dump(unvalid_resps, f, cls=NpEncoder, sort_keys=False,
                           indent=2, separators=(',', ': '), ensure_ascii=False)

