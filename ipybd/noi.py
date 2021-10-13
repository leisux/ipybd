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

