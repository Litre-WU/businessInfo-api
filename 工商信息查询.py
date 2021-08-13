# -*- coding: utf-8 -*-
# Author: Litre WU
# E-mail: litre-wu@tutanota.com
# Software: PyCharm
# File: 工商信息查询.py
# Time: 4月 21, 2021
import asyncio
from typing import Optional, List
from fastapi import FastAPI, Header, Cookie, Depends, BackgroundTasks
from starlette.requests import Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
import aiohttp
from user_agent import generate_user_agent
from lxml import etree
import json
import time
from random import randint, sample
import os
from json import load, dump
import socket
import platform
from functools import lru_cache

host = socket.gethostbyname(socket.gethostname())

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

tags_metadata = [
    {
        "name": "企业工商信息查询接口",
        "description": "企业工商信息查询(天眼查、企查查、爱企查、国家企业公示系统)",
        "externalDocs": {
            "description": "More",
            "url": f"http://{host}/docs",
        },
    },
]

app = FastAPI(openapi_url="/api/v1/api.json", title="企业工商信息查询接口", openapi_tags=tags_metadata)


@app.get("/")
async def index(request: Request, user_agent: Optional[str] = Header(None), x_token: List[str] = Header(None), ):
    result = {
        "code": 200,
        "msg": "来了！老弟",
        "result": "你看这个面它又长又宽，就像这个碗它又大又圆",
        "info": {
            "openapi_url": "/api/v1/openapi.json",
            "ip": request.client.host,
            "x-token": x_token,
            "user-agent": user_agent,
            "headers": dict(request.headers)
        }
    }
    return JSONResponse(result)


class Qcc(BaseModel):
    key: str = Field(..., example='哔哩哔哩')
    creditCode: str = Field(..., example='统一社会信用代码(暂不使用)')


# 首页
@app.post("/", response_model=Qcc)
async def api(data: Qcc, request: Request, background_tasks: BackgroundTasks, x_token: List[str] = Header(None),
              user_agent: Optional[str] = Header(None)):
    kwargs = data.dict()
    # 设置第三方代理
    proxy = await get_proxy()
    if proxy:
        kwargs = kwargs | {"proxy": f'http://{proxy[0]["ip"]}:{proxy[0]["port"]}'}
    else:
        kwargs = kwargs | {"proxy": ""}
    result = await query(**kwargs)
    return JSONResponse(result)


# 超时时间
set_timeout = 5


# 代理
async def get_proxy(**kwargs):
    if not kwargs.get("turn", 0):
        time_now = int(time.time())
        if not os.path.exists('proxy.json'):
            with open('proxy.json', 'w') as f:
                dump([], f)
        with open('proxy.json', 'r') as f:
            data = json.load(f)
            if data:
                expire_time = int(time.mktime(time.strptime(data[0]["expire_time"], "%Y-%m-%d %H:%M:%S")))
                if time_now < expire_time:
                    return data
    # # 番茄代理
    # url = 'http://x.fanqieip.com/gip'
    # params = {"getType": "3","qty": "1","port": "1","time": "1","city": "0","format": "2","ss": "1","dt": "1","css": ""}
    # 芝麻代理
    url = 'http://webapi.http.zhimacangku.com/getip'
    params = {"num": "1", "type": "2", "pro": "0", "city": "0", "yys": "0", "port": "1", "time": "1", "ts": "1",
              "ys": "0", "cs": "0", "lb": "1", "sb": "0", "pb": "4", "mr": "1", "regions": ""}
    headers = {
        "User-Agent": generate_user_agent(),
        # "X-Forwarded-For": "123.123.123.123",
    }
    try:
        async with aiohttp.ClientSession() as client:
            async with client.request(method="GET", url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = await rs.text()
                    result = json.loads(result)
                    if result.get("data", ""):
                        with open('proxy.json', 'w') as f:
                            json.dump(result["data"], f)
                        return result["data"]
                    else:
                        time.sleep(randint(0, 1))
                        retry = kwargs.get("retry", 0)
                        retry += 1
                        if retry >= 2:
                            return None
                        kwargs["retry"] = retry
                        return await get_proxy(**kwargs)
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await get_proxy(**kwargs)
    except Exception as e:
        print(e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await get_proxy(**kwargs)


# IP查询
async def query_ip(**kwargs):
    proxy = kwargs.get("proxy", "") if kwargs.get("proxy", "") else ""
    url = 'http://httpbin.org/get?show_env=1'
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", url=url, proxy=proxy, proxy_auth=proxy_auth,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = await rs.json()
                    print(result)
                    ip = result["origin"].split()[0]
                    return ip
                # print(await rs.text())
                time.sleep(randint(1, 2))
                retry = kwargs.get("retry", 0)
                retry += 1
                if retry >= 2:
                    return None
                kwargs["retry"] = retry
                return await query_ip(**kwargs)
    except Exception as e:
        print(e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await query_ip(**kwargs)


# 查询
async def query(**kwargs):
    result = await qcc(**kwargs)
    result = await tyc(**kwargs) if not result else result
    result = await aqc(**kwargs) if not result else result
    result = await gsxt(**kwargs) if not result else result
    if result:
        result = {"code": 200, "msg": "OK", "result": result}
    else:
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return {"code": 200, "msg": "Fail", "result": None}
        kwargs["retry"] = retry
        proxy = await get_proxy(**{"turn": 1})
        if proxy:
            kwargs = kwargs | {"proxy": f'http://{proxy[0]["ip"]}:{proxy[0]["port"]}'}
        else:
            kwargs = kwargs | {"proxy": ""}
        return await query(**kwargs)
    return result


# 天眼查
async def tyc(**kwargs):
    proxy = kwargs.get("proxy", "")
    key = kwargs.get("key", "")
    url = 'https://m.tianyancha.com/search'
    params = {"key": key}
    headers = {
        "Referer": "https://m.tianyancha.com",
        "User-Agent": generate_user_agent(),
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, params=params,
                                      headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    ids = etree.HTML(html).xpath('//div[@class="search-company-item"]/@onclick')
                    if not ids: return None
                    ids = [x.strip("jumpToCompany('").strip("');") for x in ids]
                    tasks = [asyncio.create_task(tqc_detail(**{"id": ids[i], "proxy": proxy})) for i in range(len(ids))]
                    result = await asyncio.gather(*tasks)
                    return [x for x in result if x]
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await tyc(**kwargs)
    except Exception as e:
        print('tyc', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await tyc(**kwargs)


# 天眼查详情
async def tqc_detail(**kwargs):
    proxy = kwargs.get("proxy", "")
    id = kwargs.get("id", "")
    if not id: return None
    url = f'https://m.tianyancha.com/company/{id}'
    headers = {
        "Referer": "https://m.tianyancha.com/search",
        "User-Agent": generate_user_agent()
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    # print(html)
                    divs = etree.HTML(html).xpath('//div[@class="content"]/div[@class="divide-content"]/div')
                    info = [x.xpath('div//text()') for x in divs] if divs else ""
                    data = {}
                    if not info:
                        retry = kwargs.get("retry", 0)
                        retry += 1
                        if retry >= 2:
                            return None
                        kwargs["retry"] = retry
                        return await tqc_detail(**kwargs)
                    for x in info:
                        if "法定代表人" in x:
                            if len(x) == 2:
                                data[x[0]] = x[1]
                            else:
                                data[x[0]] = x[2]
                        elif "经营范围" in x:
                            data[x[0]] = x[1]
                        else:
                            if len(x) > 3:
                                for i in range(0, len(x), 2):
                                    data[x[i]] = x[i + 1]
                            else:
                                data[x[0]] = x[1]
                    result = {
                        "social_credit_code": data.get("统一社会信用代码", ""),
                        "name_cn": etree.HTML(html).xpath('//head/title/text()')[0].split("_")[0].split()[0],
                        "legal_person": data.get("法定代表人", ""),
                        "status": data.get("经营状态", ""),
                        "found_date": data.get("成立日期", ""),
                        "registered_capital": data.get("注册资本", ""),
                        "really_capital": data.get("实缴资本", ""),
                        "issue_date": data.get("核准日期", ""),
                        "organization_code": data.get("组织机构代码", ""),
                        "regist_code": data.get("工商注册号", ""),
                        "taxpayer_code": data.get("纳税人识别号", ""),
                        "type": data.get("企业类型", ""),
                        "license_start_date": data.get("营业期限", ""),
                        "taxpayer_crop": data.get("纳税人资质", ""),
                        "industry_involved": data.get("行业", ""),
                        "province": data.get("所属地区", ""),
                        "regist_office": data.get("登记机关", ""),
                        "staff_size": data.get("人员规模", ""),
                        "insured_size": data.get("参保人数", ""),
                        "transformer_name": data.get("曾用名", ""),
                        "name_en": data.get("英文名称", ""),
                        "imp_exp_enterprise_code": data.get("进出口企业代码", ""),
                        "address": data.get("注册地址", ""),
                        "regist_address": data.get("注册地址", ""),
                        "business_scope": data.get("经营范围", ""),
                        "email": "",
                        "unit_phone": "",
                        "fax": "",
                        "website": ""
                    }
                    if result.get("license_start_date", ""):
                        result["license_start_date"], result["license_end_date"] = result["license_start_date"].split(
                            "至")
                    else:
                        result["license_start_date"], result["license_end_date"] = "", ""
                    return result
                else:
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await tqc_detail(**kwargs)
    except Exception as e:
        print('tyc_detail', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await tqc_detail(**kwargs)


# 企查查
async def qcc(**kwargs):
    proxy = kwargs.get("proxy", "")
    key = kwargs.get("key", "")
    creditCode = kwargs.get("creditCode", "")
    url = 'https://www.qcc.com/web/search'
    params = {
        "key": key
    }
    headers = {
        "user-agent": generate_user_agent(),
        "cookie": "",
        "referer": f"https://www.qcc.com/web/search?key={key}"
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, params=params,
                                      headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    content = etree.HTML(html).xpath('//script[1]/text()')
                    content = '{"appState' + content[0].split("appState")[1].split(";(function")[
                        0] if content else ""
                    if not content: return None
                    result = json.loads(content)
                    result = result["search"]["searchRes"].get("Result", "") if result else ""
                    if not result:
                        return None
                    data_list = []
                    for r in result:
                        data = {
                            "keyNo": r.get("KeyNo", ""),
                            "legal_person": r.get("OperName", ""), "email": r.get("Email", ""),
                            "unit_phone": r.get("ContactNumber", ""), "fax": "",
                            "address": r.get("Address", "").replace("<em>", "").replace("</em>", ""),
                            "website": r.get("GW", "")
                        }
                        data_list.append(data)
                    tasks = [asyncio.create_task(qcc_detail(**{"data": data_list[i], "proxy": proxy})) for i in
                             range(len(data_list))]
                    result = await asyncio.gather(*tasks)
                    return [x for x in result if x]
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await qcc(**kwargs)
    except Exception as e:
        print('qcc', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await qcc(**kwargs)


# 企查查企业详情
async def qcc_detail(**kwargs):
    # time.sleep(randint(1, 2))
    proxy = kwargs.get("proxy", "")
    data = kwargs.get("data", "")
    url = f'https://www.qcc.com/firm/{data["keyNo"]}.html'
    headers = {
        "user-agent": generate_user_agent(),
        "cookie": "",
        # "cookie": "acw_sc__v2=6062bdefc57536ceeeb840ffcf85497a600eef9f",
        "referer": f'https://www.qcc.com/firm/{data["keyNo"]}.html'
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    table = etree.HTML(html).xpath('//table[@class="ntable"]')[0] if etree.HTML(html).xpath(
                        '//table[@class="ntable"]') else ""
                    if type(table) == str:
                        retry = kwargs.get("retry", 0)
                        retry += 1
                        if retry >= 2:
                            return False
                        kwargs["retry"] = retry
                        return await qcc_detail(**kwargs)
                    trs = table.xpath('tr')
                    if not trs: return False
                    tds = []
                    for x in trs:
                        tds += x.xpath('td[@class="tb"]')
                    info = {x.xpath('text()')[0].strip(): x.xpath('following-sibling::node()/text()')[0].strip() for x
                            in tds if x.xpath('following-sibling::node()/text()')}
                    # print(info)
                    result = {
                        "social_credit_code": info.get("统一社会信用代码", ""),
                        "name_cn": info.get("企业名称", ""),
                        "legal_person": info.get("法定代表人", ""),
                        "status": info.get("登记状态", ""),
                        "found_date": info.get("成立日期", ""),
                        "registered_capital": info.get("注册资本", ""),
                        "really_capital": info.get("实缴资本", ""),
                        "issue_date": info.get("核准日期", ""),
                        "organization_code": info.get("组织机构代码", ""),
                        "regist_code": info.get("工商注册号", ""),
                        "taxpayer_code": info.get("纳税人识别号", ""),
                        "type": info.get("企业类型", ""),
                        "license_start_date": info.get("营业期限", "").strip(),
                        "taxpayer_crop": info.get("纳税人资质", ""),
                        "industry_involved": info.get("所属行业", ""),
                        "province": info.get("所属地区", ""),
                        "regist_office": info.get("登记机关", ""),
                        "staff_size": info.get("人员规模", ""),
                        "insured_size": info.get("参保人数", "") if info.get("参保人数", "") else
                        [span.strip() for span in table.xpath('tr/td/span/text()') if span.strip()][0],
                        "transformer_name": table.xpath('tr/td/div/text()')[-1].strip(),
                        "name_en": info.get("英文名", ""),
                        "imp_exp_enterprise_code": info.get("进出口企业代码", ""),
                        "regist_address": info.get("注册地址", "") if info.get("注册地址", "") else
                        table.xpath('tr/td/a[@class="text-dk"]/text()')[0],
                        "business_scope": info.get("经营范围", ""),
                    }
                    if result.get("license_start_date", ""):
                        result["license_start_date"], result["license_end_date"] = (x.strip() for x in
                                                                                    result["license_start_date"].split(
                                                                                        "至"))
                    else:
                        result["license_start_date"], result["license_end_date"] = "", ""
                    result["legal_person"] = data["legal_person"]
                    return {**data, **result}
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await qcc_detail(**kwargs)
    except Exception as e:
        print('qcc_detail', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await qcc_detail(**kwargs)


# 爱企查
async def aqc(**kwargs):
    proxy = kwargs.get("proxy", "")
    key = kwargs.get("key", "")
    creditCode = kwargs.get("creditCode", "")
    url = 'https://aiqicha.baidu.com/s'
    params = {
        "q": key,
        "t": "0"
    }
    headers = {
        "User-Agent": generate_user_agent(),
        "Cookie": "",
        # "Cookie": "__yjs_st=2_MmMwMTY0YjJkNmI0ZmU1MjllZGU0NTA4ZThmMWI0ZmRjYjUxMmIyZWFmMTRmM2Q1ZTQwMjZjYmY2YmNiMGY0ZmU0NDFjOWM1M2FiNTA1MGRiOTFkMmM4OTczZjQzMzUxZTc2ZjViZmYwYjRmYjhhZGYxYzY2N2YzZTk1MTZmZTg1OTNiZmQ4OTQ3NTNmZTkxZDAwNmVmYzhjNmJmNmMyNTJmY2IxYmJkMTc2NDA3OTVjNGIyYjkyZDQxMWM3YzgwZmQ2ZTQ5MzdjMmI0NjViNmI2MDIxZDA2ODA2ODI0MmQ0YWJlMTkxMTc5NDQyZGQ5YTJkZDI2ZWYxZGE3N2NiZF83X2FkZGY1ZWUw;",
        "Referer": 'https://aiqicha.baidu.com/'
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, params=params,
                                      headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    content = etree.HTML(html).xpath('//script[1]/text()')
                    if content:
                        result = '{"sid"' + content[0].split('{"sid"')[1].split(";\n")[0]
                        # print(result)
                        result = json.loads(result)
                        data_list = []
                        for r in result["result"]["resultList"]:
                            # if not creditCode or r["regNo"] == creditCode:
                            #     return await aqc_detail(**{"data": {"pid": r["pid"]}})
                            data_list.append({"pid": r["pid"]})
                        tasks = [asyncio.create_task(aqc_detail(**{"data": data_list[i], "proxy": proxy})) for i in
                                 range(len(data_list))]
                        result = await asyncio.gather(*tasks)
                        return [x for x in result if x]
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await aqc(**kwargs)
    except Exception as e:
        print('aqc', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await aqc(**kwargs)


# 爱企查企业详情
async def aqc_detail(**kwargs):
    proxy = kwargs.get("proxy", "")
    data = kwargs.get("data", "")
    url = 'https://aiqicha.baidu.com/detail/basicAllDataAjax'
    params = {
        "pid": data["pid"]
    }
    headers = {
        "User-Agent": generate_user_agent(),
        "Cookie": "",
        # "Cookie": "__yjs_st=2_MmMwMTY0YjJkNmI0ZmU1MjllZGU0NTA4ZThmMWI0ZmRjYjUxMmIyZWFmMTRmM2Q1ZTQwMjZjYmY2YmNiMGY0ZmU0NDFjOWM1M2FiNTA1MGRiOTFkMmM4OTczZjQzMzUxZTc2ZjViZmYwYjRmYjhhZGYxYzY2N2YzZTk1MTZmZTg1OTNiZmQ4OTQ3NTNmZTkxZDAwNmVmYzhjNmJmNmMyNTJmY2IxYmJkMTc2NDA3OTVjNGIyYjkyZDQxMWM3YzgwZmQ2ZTQ5MzdjMmI0NjViNmI2MDIxZDA2ODA2ODI0MmQ0YWJlMTkxMTc5NDQyZGQ5YTJkZDI2ZWYxZGE3N2NiZF83X2FkZGY1ZWUw;",
        "Referer": f'https://aiqicha.baidu.com/company_detail_{data["pid"]}',
        "X-Requested-With": "XMLHttpRequest",
        "Zx-Open-Url": f'https://aiqicha.baidu.com/company_detail_{data["pid"]}'
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="GET", proxy=proxy, proxy_auth=proxy_auth, url=url, params=params,
                                      headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = json.loads(await rs.text())
                    result = result["data"]["basicData"] if result.get("data", "") else ""
                    if not result:
                        retry = kwargs.get("retry", 0)
                        retry += 1
                        if retry >= 2:
                            return None
                        kwargs["retry"] = retry
                        return await aqc_detail(**kwargs)
                    province = f'{result["district"].split("省")[0]}省' if "省" in result.get(
                        "district", "") else f'{result.get("district", "").split("市")[0]}市'
                    result = {
                        "name_cn": result.get("entName", ""),
                        "name_en": "",
                        "legal_person": result.get("legalPerson", ""),
                        "registered_capital": result.get("regCapital", ""),
                        "really_capital": result.get("realCapital", ""),
                        "found_date": result.get("startDate", ""),
                        "issue_date": result.get("annualDate", ""),
                        "social_credit_code": result.get("unifiedCode", ""),
                        "organization_code": result.get("orgNo", ""),
                        "regist_code": result.get("licenseNumber", ""),
                        "taxpayer_code": result.get("regNo", ""),
                        "imp_exp_enterprise_code": "",
                        "industry_involved": result.get("industry", ""),
                        "type": result.get("entType", ""),
                        "license_start_date": result.get("startDate", ""),
                        "license_end_date": result.get("openTime", "").split("至")[-1].strip(),
                        "regist_office": result.get("authority", ""),
                        "staff_size": "",
                        "insured_size": result["insuranceInfo"]["insuranceNum"],
                        "province": province,
                        "address": result.get("addr", ""),
                        "business_scope": result.get("scope", ""),
                        "email": result.get("email", ""),
                        "unit_phone": result.get("telephone", ""),
                        "fax": "",
                        "website": result.get("website", ""),
                        "regist_address": result.get("regAddr", ""),
                        "transformer_name": result["prevEntName"][0] if type(result.get("prevEntName", "")) == list else
                        result.get("prevEntName", ""),
                        "status": result.get("openStatus", ""),
                    }
                    return result
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await aqc_detail(**kwargs)
    except Exception as e:
        print("aqc_detail", e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await aqc_detail(**kwargs)


# 国家企业信用信息公示系统
async def gsxt(**kwargs):
    proxy = kwargs.get("proxy", "")
    key = kwargs.get("key", "")
    creditCode = kwargs.get("creditCode", "")
    url = 'https://app.gsxt.gov.cn/gsxt/corp-query-app-search-1.html'
    data = {
        "conditions": '{"excep_tab":"0","ill_tab":"0","area":"0","cStatus":"0","xzxk":"0","xzcf":"0","dydj":"0"}',
        "searchword": key,
        "sourceType": "W"
    }
    headers = {
        "User-Agent": generate_user_agent(),
        "X-Requested-With": "XMLHttpRequest",
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method="POST", proxy=proxy, proxy_auth=proxy_auth, url=url, data=data,
                                      headers=headers,
                                      timeout=10) as rs:
                if rs.status == 200:
                    result = await rs.text()
                    # print(result)
                    result = json.loads(result)
                    if result.get("data", ""):
                        data_list = []
                        for r in result["data"]["result"]["data"]:
                            # if not creditCode or r["uniscId"] == creditCode:
                            #     return await gsxt_detail(**{"data": {"pripid": r["pripid"]}})
                            data_list.append({"pripid": r["pripid"]})
                        tasks = [asyncio.create_task(gsxt_detail(**{"data": data_list[i], "proxy": proxy})) for i in
                                 range(len(data_list))]
                        result = await asyncio.gather(*tasks)
                        return [x for x in result if x]
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await gsxt(**kwargs)
    except Exception as e:
        print('gsxt', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await gsxt(**kwargs)


# 国家企业信用信息公示系统公司详情信息
async def gsxt_detail(**kwargs):
    proxy = kwargs.get("proxy", "")
    data = kwargs.get("data", "")
    url = f'https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-primaryinfoapp-entbaseInfo-{data["pripid"]}.html'
    params = {
        "nodeNum": "310000",
        "entType": "6150",
        "sourceType": "W"
    }
    headers = {
        "User-Agent": generate_user_agent(),
        "X-Requested-With": "XMLHttpRequest",
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            proxy_auth = aiohttp.BasicAuth(kwargs.get("proxy_user", ""), kwargs.get("proxy_pass", ""))
            async with client.request(method='POST', proxy=proxy, proxy_auth=proxy_auth, url=url, params=params,
                                      headers=headers,
                                      timeout=10) as rs:
                if rs.status == 200:
                    result = await rs.text()
                    result = json.loads(result)
                    if result.get("result"):
                        result = {
                            "name_cn": result["result"]["entName"],
                            "name_en": "",
                            "legal_person": result["result"]["name"],
                            "registered_capital": f'{result["regCaption"]}{result["regCapCurCN"]}'.strip(),
                            "really_capital": "",
                            "found_date": result["result"]["estDate"],
                            "issue_date": result["result"]["apprDate"],
                            "social_credit_code": result["result"]["uniscId"],
                            "organization_code": "",
                            "regist_code": result["result"]["regNo"],
                            "taxpayer_code": "",
                            "imp_exp_enterprise_code": "",
                            "industry_involved": result["result"]["industryPhy"],
                            "type": result["result"]["entType_CN"],
                            "license_start_date": result["result"]["opFrom"],
                            "license_end_date": result["result"]["opTo"],
                            "regist_office": result["result"]["regOrg_CN"],
                            "staff_size": "",
                            "insured_size": "",
                            "province": result["nodeNum"],
                            "address": result["result"]["dom"],
                            "business_scope": result["result"]["opScope"],
                            "email": "",
                            "unit_phone": "",
                            "fax": "",
                            "website": "",
                            "regist_address": result["result"]["dom"],
                            "transformer_name": "",
                            "status": result["result"]["regState_CN"],
                        }
                        return result
                else:
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await gsxt_detail(**kwargs)
    except Exception as e:
        print('gsxt_detail', e)
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 2:
            return None
        kwargs["retry"] = retry
        return await gsxt_detail(**kwargs)


async def test():
    # proxy = await get_proxy()
    proxy = 'http://127.0.0.1:1080'
    print(proxy)
    rs = await qcc(**{"key": "特变电工湖南工程有限公司", "proxy": proxy})
    print(rs)
    # tasks = [asyncio.create_task(qcc(**{"key": "特变电工湖南工程有限公司", "proxy": proxy})) for x in range(10)]
    # await asyncio.gather(*tasks)


if __name__ == '__main__':
    # import uvicorn
    # uvicorn.run(app)
    # proxy = 'http://127.0.0.1:1080'
    proxy = ''
    # rs = asyncio.get_event_loop().run_until_complete(test())
    # rs = asyncio.get_event_loop().run_until_complete(get_proxy())
    kwargs = {"key": "上海茗昊机械工程有限公司", "proxy": ""}
    # kwargs = {"key": "上海宽娱数码科技有限公司", "proxy": ""}
    # kwargs = {**kwargs, **sample(rs, 1)[0]}
    # rs = asyncio.get_event_loop().run_until_complete(query_ip(**kwargs))
    # rs = asyncio.get_event_loop().run_until_complete(tyc(**kwargs))
    # rs = asyncio.get_event_loop().run_until_complete(qcc(**kwargs))
    # rs = asyncio.get_event_loop().run_until_complete(get_proxy(**kwargs))
    # rs = asyncio.get_event_loop().run_until_complete(
    #     qcc_detail(**{"url": "https://www.qcc.com/firm/963f4179841540334d3a16db3fc3567d.html"}))
    rs = asyncio.get_event_loop().run_until_complete(aqc(**kwargs))
    # rs = asyncio.get_event_loop().run_until_complete(aqc_detail(**{"data": {"pid": "43880125442188"}}))
    # rs = asyncio.get_event_loop().run_until_complete(gsxt(**kwargs))
    # pripid = "D1FDF711DFE03EE312CC2ACD3CE218AB448EC78EC78E61ABE228E2ABE2ABE2ABEEABE2ABDF960DC782CB82C7647C-1618992356543"
    # pripid = "0CFD2A1102E0E3E3CFCCF7CDE1E2C5AB998E1A8E1A8EBCAB3FAB3FAB3FAB3FABED75E1F63324BC8E1A8E1A6473B6-1618991419697"
    # rs = asyncio.get_event_loop().run_until_complete(gsxt_detail(**{"data": {"pripid": pripid}}))
    # rs = asyncio.get_event_loop().run_until_complete(get_proxy())
    # rs = asyncio.get_event_loop().run_until_complete(query_ip(**{"proxy": "http://182.111.108.203:45113"}))
    print(rs)
