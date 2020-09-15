#!/usr/bin/python
# -*- coding=utf8 -*-
"""
# @Author : Xu Zhoufeng
# @Created Time : 2020-09-03 09:53:46
# @Description :https://github.com/leisux/ipybd 
"""

from ipybd.core import FormatTable
import os
import urllib.request
import urllib.parse
import base64
import hmac
import json
from hashlib import sha1
import aiohttp
import asyncio

URL = "https://www.noi.link/api/data_add"
ACCESSKEY = "ao4npk40meft2j612b4h8osh69e3hdbi"
SECRETKEY = "qk3ps9sot5dbnz8wihf3ruetprovzks1"


class Api:
    def __init__(
            self, json_data, registrant, data_rights, 
            data_rights_holder, data_model_id
            ):
        self.data = json.dumps(json_data)
        self.registrant = registrant
        self.rights = data_rights
        self.rights_holder = data_rights_holder
        self.model_id = data_model_id

    def register(self):
        postdata, token = self.build_post_info()
        req = urllib.request.Request(URL, postdata)
        req.add_header("token", token)
        res = urllib.request.urlopen(req)
        html=res.read()
        print(html)

    def build_post_info(self):
        policy = self.build_policy()
        token = self.get_token(policy)
        data = {"policy":policy.decode('utf-8')}
        postdata = urllib.parse.urlencode(data).encode('utf-8')
        return postdata, token

    def build_policy(self):
        json_policy = json.dumps(
                {
                    'data_info':self.data,
                    'data_registrant':self.registrant,
                    'data_from':self.rights_holder,
                    'data_copyright':self.rights,
                    'data_modelid':self.model_id
                    },
                    ensure_ascii = False
                )
        return base64.b64encode(json_policy.encode('utf-8'))

    def get_token(self, policy):
        digest = hmac.new(SECRETKEY.encode('utf-8'), policy, sha1).digest()
        digest_b64 = base64.b64encode(digest)
        sign = digest_b64.decode('utf-8')
        return ":".join([ACCESSKEY, sign])


class Noi:
    def __init__(self, post_datas):
       self.sem = asyncio.Semaphore(50) 
       self.datas = post_datas

    def mult_register(self, tasks):
        tasks = self.build_tasks()
        loop = asyncio.get_event_loop()
        resp = loop.run_until_complete(tasks)
        loop.close()
        print(resp)
    
    async def build_tasks(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.limit_sem(data, session) for data in self.datas]
            return await asyncio.gather(*tasks)
        
    async def limit_sem(self, data, session):
        async with self.sem:
            return await self.fetch(data, session)
        
    async def fetch(self, data, session):
        async with session.post(URL, data, timeout=60) as resp:
            if resp.status == 429:
                await asyncio.sleep(3)
            else:
                result = await resp.json()
            return result

if __name__ == '__main__':
    pass
