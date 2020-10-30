#!/usr/bin/python
# -*- coding=utf8 -*-
"""
# @Author : Xu Zhoufeng
# @Created Time : 2020-09-03 09:53:46
# @Description :https://github.com/leisux/ipybd
"""

import urllib.request
import urllib.parse
import base64
import hmac
import json
from hashlib import sha1
import aiohttp
import asyncio
from ipybd.core import NpEncoder
from tqdm import tqdm

URL = "https://www.noi.link/api/data_add"
ACCESSKEY = "ao4npk40meft2j612b4h8osh69e3hdbi"
SECRETKEY = "qk3ps9sot5dbnz8wihf3ruetprovzks1"


class Api:
    def __init__(
            self, json_data, data_rights, data_rights_holder, data_model_id):
        self.data = json_data
        self.rights = data_rights
        self.rights_holder = data_rights_holder
        self.model_id = data_model_id

    def post(self):
        data, token = self.build_post_info()
        postdata = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(URL, postdata)
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
                    'data_from': self.rights_holder,
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


class Link:
    def __init__(self, datas:dict, model_id):
        self.datas = datas
        self.model_id = model_id

    def link(self):
        responses = self.add()
        self.unvalid_resps = []
        for resp, data in zip(responses, self.datas):
            if resp:
                pass
            else:
                self.unvalid_resps.append(data)

    def add(self):
        self.pbar = tqdm(total=len(self.datas), desc="注册数据", ascii=True)
        loop = asyncio.get_event_loop()
        self.sem = asyncio.Semaphore(50, loop)
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

    def build_post_data(self, data:dict):
        rights = data["Record"]["rights"]
        rights_holder = data["Record"]["rightsHolder"]
        json_data = json.dumps(data, cls=NpEncoder, ensure_ascii=False)
        # print(json_data)
        api = Api(
            json_data,
            rights,
            rights_holder,
            self.model_id)
        return api.build_post_info()

    async def fetch(self, data:'json', token, session):
        while True:
            async with session.post(URL,
                                    data=data,
                                    headers={"token": token}
                                    ) as resp:
                if resp.status == 429:
                    await asyncio.sleep(3)
                    continue
                elif resp.status == 200:
                    response = await resp.json(content_type='text')
                    return self.get_data(response)

    def get_data(self, response):
        if response['code'] == 200:
            return response['data']
        elif response['code'] == 400:
            print("\n认证授权失败:错误信息包括密钥信息不正确；数字签名错误；授权已超时\n")
        elif response['code'] == 403:
            print("\n权限不足，拒绝访问\n")
        elif response['code'] == 404:
            print("\n资源不存在 包括空间资源不存在；镜像源资源不存在\n")
        elif response['code'] == 502:
            print("\n错误网关\n")
        elif response['code'] == 503:
            print("\n服务端不可用\n")
        elif response['code'] == 504:
            print("\n服务端操作超时\n")
        elif response['code'] == 599:
            print("\n服务端操作失败\n")
        elif response['code'] == 601:
            print("\n用户账户冻结\n")
        else:
            print("\n错误代码：{}\n".format(response['code']))
        return None
