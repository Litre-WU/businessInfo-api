# -*- coding: utf-8 -*-
# Author: Litre WU
# E-mail: litre-wu@tutanota.com
# Software: PyCharm
# File: 看准-企业工商信息查询.py
# Time: 1月 06, 2022
import asyncio
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from user_agent import generate_user_agent
from random import randint
from time import sleep
from sys import platform
from json import loads
from bs4 import BeautifulSoup
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
import socket
from boltons.cacheutils import LRU
from hashlib import md5

if platform == "win32":
    asyncio.set_event_loop(asyncio.ProactorEventLoop())
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

host = socket.gethostbyname(socket.gethostname())

lru_cache = LRU(max_size=100)

tags_metadata = [
    {
        "name": "看准-企业工商信息查询接口",
        "description": "看准-企业工商信息查询",
        "externalDocs": {
            "description": "More",
            "url": f"http://{host}/docs",
        },
    },
]

contact = {
    "name": "Litre",
    "url": "http://121.37.209.113",
    "email": "litre-wu@tutanota.com",
}

app = FastAPI(openapi_url="/api/v1/api.json", title="看准-企业工商信息查询接口", contact=contact, openapi_tags=tags_metadata)


class SearchItem(BaseModel):
    query: str = Field(..., example='哔哩哔哩')
    cityCode: str = Field(..., example=0)
    industryCodes: str = Field(..., example='')
    pageNum: str = Field(..., example=1)
    limit: str = Field(..., example=15)


# 查询接口
@app.post("/search", tags=["看准-工商信息查询"])
async def search(data: SearchItem):
    kwargs = data.dict()
    key = md5(str(kwargs).encode()).hexdigest()
    if lru_cache.get(key): return lru_cache[key]
    result = await query(**kwargs)
    if result: lru_cache[key] = result
    return result


class InfoItem(BaseModel):
    encCompanyId: str = Field(..., example='0XN_2dW7Fw~~')


# 工商信息接口
@app.post("/compInfo", tags=["看准-工商信息查询"])
async def info(data: InfoItem):
    kwargs = data.dict()
    key = md5(str(kwargs).encode()).hexdigest()
    if lru_cache.get(key): return lru_cache[key]
    result = await compInfo(**kwargs)
    if result: lru_cache[key] = result
    return result


# 公共请求函数
async def pub_req(**kwargs):
    method = kwargs.get("method", "GET")
    url = kwargs.get("url", "")
    params = kwargs.get("params", {})
    data = kwargs.get("data", {})
    headers = {**{"User-Agent": generate_user_agent()}, **kwargs.get("headers", {})}
    proxy = kwargs.get("proxy", "")
    timeout = kwargs.get("timeout", 10)
    try:
        async with asyncio.Semaphore(20):
            async with ClientSession(timeout=ClientTimeout(total=3),
                                     connector=TCPConnector(ssl=False),
                                     trust_env=True) as client:
                async with client.request(method=method, url=url, params=params, data=data, headers=headers,
                                          proxy=proxy,
                                          timeout=timeout) as rs:
                    if rs.status == 200 or 201:
                        content = await rs.read()
                        return content
                    else:
                        sleep(randint(1, 2))
                        retry = kwargs.get("retry", 0)
                        retry += 1
                        if retry >= 2:
                            return None
                        kwargs["retry"] = retry
                        return await pub_req(**kwargs)
    except Exception as e:
        print(e)
        sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await pub_req(**kwargs)


# 查询
async def query(**kwargs):
    meta = {
        "url": "https://www.kanzhun.com/search/company_v2.json",
        "params": {
            "query": kwargs.get("query", "哔哩哔哩"),
            "cityCode": kwargs.get("cityCode", 0),
            "industryCodes": kwargs.get("industryCodes", ""),
            "pageNum": kwargs.get("pageNum", 1),
            "limit": kwargs.get("limit", 15),
        },
        "headers": {
            "Accept-Encoding": "gzip, deflate, br"
        }
    }
    res = await pub_req(**meta)
    if not res: return None
    # print(res.decode())
    return loads(res)


# 工商信息
async def compInfo(**kwargs):
    meta = {
        "url": f'https://www.kanzhun.com/firm/info/{kwargs.get("encCompanyId", "")}.html',
        "headers": {
            "Accept-Encoding": "gzip, deflate, br"
        }
    }
    res = await pub_req(**meta)
    if not res: return None
    soup = BeautifulSoup(res.decode(), 'html.parser')
    div = soup.find_all("div", class_="kz-company-desc")
    if div:
        table = div[0].table
        table = pd.read_html(str(table))
        info = {}
        for x in table[0].values.tolist():
            for i in range(0, len(x), 2):
                if x[i].strip("-"):
                    info[x[i]] = x[i + 1]
        return info


async def main():
    rs = await query()
    # rs = await compInfo(**{"encCompanyId": "0XN_2dW7Fw~~"})
    print(rs)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
