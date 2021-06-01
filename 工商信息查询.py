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
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import aiohttp
from user_agent import generate_user_agent
from lxml import etree
import json
import time
from random import randint

# windows系统需要
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

tags_metadata = [
    {
        "name": "企业工商信息查询接口",
        "description": "企业工商信息查询(企查查、爱企查)",
        "externalDocs": {
            "description": "More",
            "url": "http://localhost/docs",
        },
    },
]

app = FastAPI(openapi_url="/api/v1/api.json", openapi_tags=tags_metadata)


@app.get("/")
async def index(request: Request, user_agent: Optional[str] = Header(None), x_token: List[str] = Header(None), ):
    result = {
        "code": 200,
        "msg": "来了！老弟",
        "result": "你看这个面它又长又宽，就像这个碗它又大又圆",
        "info": {
            "openapi_url": "/api/v1/openapi.json",
            "ip": request.client.host,
            "X-Token": x_token,
            "UA": user_agent,
            "headers": request.headers.items()
        }
    }
    return JSONResponse(result)


class Qcc(BaseModel):
    key: str = None
    creditCode: str = None


# 首页
@app.post("/", response_model=Qcc)
async def api(data: Qcc, request: Request, background_tasks: BackgroundTasks, x_token: List[str] = Header(None),
              user_agent: Optional[str] = Header(None)):
    kwargs = data.dict()
    # print(data)
    # proxy = ''
    # proxy = await get_proxy()
    proxy = 'http://127.0.0.1:1080'
    kwargs["proxy"] = proxy if proxy else ""
    result = await qcc(**kwargs)
    result = await aqc(**kwargs) if not result else result
    result = await tyc(**kwargs) if not result else result
    result = await gsxt(**kwargs) if not result else result
    if result:
        result = {"code": 200, "msg": "OK", "result": result}
    else:
        result = {"code": 200, "msg": "Fail", "result": result}
    return JSONResponse(result)


# 超时时间
set_timeout = 5


# 代理
async def get_proxy(**kwargs):
    # 番茄代理
    url = 'http://x.fanqieip.com/gip'
    params = {
        "getType": "3",
        "qty": "1",
        "port": "1",
        "time": "1",
        "city": "0",
        "format": "2",
        "ss": "1",
        "dt": "1",
        "css": ""
    }
    # 芝麻代理
    url = 'http://webapi.http.zhimacangku.com/getip'
    params = {"num": "1", "type": "2", "pro": "0", "city": "0", "yys": "0", "port": "1", "time": "1", "ts": "1",
              "ys": "1", "cs": "1", "lb": "1", "sb": "0", "pb": "45", "mr": "2", "regions": ""
              }
    # url = 'http://http.tiqu.letecs.com/getip3'
    # params = {"num": "1", "type": "2", "pro": "0", "city": "0", "yys": "0", "port": "1", "time": "1", "ts": "1",
    #           "ys": "1", "cs": "1", "lb": "1", "sb": "0", "pb": "45", "mr": "2", "regions": "", "gm": "4"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4484.7 Safari/537.36",
        # "X-Forwarded-For": "120.236.115.197",
        # "X-Forwarded-For": "219.137.186.56",
    }
    try:
        async with aiohttp.ClientSession() as client:
            async with client.request(method="GET", url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = await rs.text()
                    # print(result)
                    result = json.loads(result)
                    proxy = f'http://{result["data"][0]["ip"]}:{result["data"][0]["port"]}'
                    return proxy
                else:
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 2:
                        return None
                    kwargs["retry"] = retry
                    return await get_proxy(**kwargs)
    except Exception as e:
        print(e)
        time.sleep(randint(1, 2))
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
            async with client.request(method="GET", url=url, proxy=proxy, timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = await rs.json()
                    ip = result["origin"].split()[0]
                    return ip
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
            async with client.request(method="GET", proxy=proxy, url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    ids = etree.HTML(html).xpath('//div[@class="search-company-item"]/@onclick')
                    if not ids: return None
                    ids = [eval(x.strip("jumpToCompany")) for x in ids]
                    tasks = [asyncio.create_task(tqc_detail(**{"id": ids[i]})) for i in range(len(ids))]
                    result = await asyncio.gather(*tasks)
                    return [x for x in result if x]
                else:
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await tyc(**kwargs)
    except Exception as e:
        print('tyc', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4484.7 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            async with client.request(method="GET", proxy=proxy, url=url, headers=headers, timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    divs = etree.HTML(html).xpath('//div[@class="content"]/div[@class="divide-content"]/div')
                    info = [x.xpath('div//text()') for x in divs]
                    data = {}
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
                        "name_cn": etree.HTML(html).xpath('//head/title/text()')[0].split("_")[0],
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
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
            async with client.request(method="GET", proxy=proxy, url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    content = etree.HTML(html).xpath('//script[1]/text()')
                    content = '{"appState' + content[0].split("appState")[1].split(";(function")[0] if content else ""
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
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await qcc(**kwargs)
    except Exception as e:
        print('qcc', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
            async with client.request(method="GET", proxy=proxy, url=url, headers=headers, timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    # print(html)
                    table = etree.HTML(html).xpath('//table[@class="ntable"]')[0]
                    trs = table.xpath('tr')
                    tds = []
                    for x in trs:
                        tds += x.xpath('td[@class="tb"]')
                    info = {x.xpath('text()')[0].strip(): x.xpath('following-sibling::node()/text()')[0].strip() for x
                            in tds}
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
                        "license_start_date": info.get("营业期限", ""),
                        "taxpayer_crop": info.get("纳税人资质", ""),
                        "industry_involved": info.get("所属行业", ""),
                        "province": info.get("所属地区", ""),
                        "regist_office": info.get("登记机关", ""),
                        "staff_size": info.get("人员规模", ""),
                        "insured_size": info.get("参保人数", ""),
                        "transformer_name": info.get("曾用名", ""),
                        "name_en": info.get("英文名", ""),
                        "imp_exp_enterprise_code": info.get("进出口企业代码", ""),
                        "regist_address": info.get("注册地址", ""),
                        "business_scope": info.get("经营范围", ""),
                    }
                    if result.get("license_start_date", ""):
                        result["license_start_date"], result["license_end_date"] = result["license_start_date"].split(
                            "至")
                    else:
                        result["license_start_date"], result["license_end_date"] = "", ""
                    result["legal_person"] = data["legal_person"]
                    return {**data, **result}
                else:
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await qcc_detail(**kwargs)
    except Exception as e:
        print('qcc_detail', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
        "Cookie": "BD6D0; BDRCVFR[n9IS1zhFc9f]=mk3SLVN4HKm; delPer=0; H_PS_PSSID=31253_26350; BAIDUID_BFESS=052F271618C35B323E5A3EE30A92855F:FG=1; PSINO=7; Hm_lvt_ad52b306e1ae4557f5d3534cce8f8bbf=1621836200,1621934306; Hm_lpvt_ad52b306e1ae4557f5d3534cce8f8bbf=1621934320; ZX_UNIQ_UID=7da8713c563ea82758303b407e23815a; ab_sr=1.0.0_Y2FiNzBiOGZhOGNlNDE0MDIwY2UzN2I5NTgxMmY0ZThmZDVhYzE0ZTE0Y2Y1ZjJmNTFiYjU1Y2Y1YzNiYjUzYzgxZmMxNmY4MjBjZTA5ZTZiNGRkODc5MDFiMDBmZjIw; _s53_d91_=93c39820170a0a5e748e1ac9ecc79371df45a908d7031a5e0e6df033fcc8068df8a85a45f59cb9faa0f164dd33ed0c725ce0193064b26f78ee1fe0d9a4f2268afdacf18e692225844a44e79bd71a77f06f7e4596b88b0349e89e6b06a1578641c4c99befd9b0e7b25253cd16a5407825286ff581d6df283c4ae10dd20777111ae54f8098a7517df76b0a8f0565ca1ed04e4b8c9badc76492629f430223dcf523836a80fdb0bde7597942a188f03616047cec47f6f220f18e0bae8cf317754807970d2232d01d87c84aa94155409da9e3de623190cc2e96dff0bd7aa5898d09af; _y18_s21_=ca1d0606; __yjs_st=2_ODY4ZDU5MmIwNGJjYzgwMTcwYTE5ZGIyMzhlMDYxMGE3YjgzZGE3NWFjNTQzNDkyM2NjYTFiOGM1ZjNmNWE3ZDYzNjVkOTQ4NjE3MWQwNTIxOTk4NWYwMzhkNGMyMDMwZWRmYTc2N2FhZmNlMmUwYTgwMDI1ZTBhZDE2MTRkOWY1NjBhNmI5Mzg0YmE1OWUzODFhMTFmZTA5ZDFiNTk5M2U0NTMzMjU0MDNkMjM4NGEzNGQ2YWJhMzIzN2M1NDg2NGYwZmI2MGUyNTBjMDA2MTFjMGIwMTgyZTFmOWRhNjQ2NDA5YmExZTczZTgyZGU5MDgyNGZiNTE3MDdjNGE0MzJmZjBiOTNlZWRiZTcxMGQyMDM0NGExYWIzMjI1YjRlXzdfZTVhOGQ3Yzk=",
        "Referer": f'https://aiqicha.baidu.com/s?q={key}&t=0'
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            async with client.request(method="GET", proxy=proxy, url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    html = await rs.text()
                    content = etree.HTML(html).xpath('//script[1]/text()')
                    if content:
                        result = '{"sid"' + content[0].split('{"sid"')[1].split(";")[0]
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
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await aqc(**kwargs)
    except Exception as e:
        print('aqc', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
        "Cookie": "BD6D0; BDRCVFR[n9IS1zhFc9f]=mk3SLVN4HKm; delPer=0; H_PS_PSSID=31253_26350; BAIDUID_BFESS=052F271618C35B323E5A3EE30A92855F:FG=1; PSINO=7; Hm_lvt_ad52b306e1ae4557f5d3534cce8f8bbf=1621836200,1621934306; Hm_lpvt_ad52b306e1ae4557f5d3534cce8f8bbf=1621934320; ZX_UNIQ_UID=7da8713c563ea82758303b407e23815a; ab_sr=1.0.0_Y2FiNzBiOGZhOGNlNDE0MDIwY2UzN2I5NTgxMmY0ZThmZDVhYzE0ZTE0Y2Y1ZjJmNTFiYjU1Y2Y1YzNiYjUzYzgxZmMxNmY4MjBjZTA5ZTZiNGRkODc5MDFiMDBmZjIw; _s53_d91_=93c39820170a0a5e748e1ac9ecc79371df45a908d7031a5e0e6df033fcc8068df8a85a45f59cb9faa0f164dd33ed0c725ce0193064b26f78ee1fe0d9a4f2268afdacf18e692225844a44e79bd71a77f06f7e4596b88b0349e89e6b06a1578641c4c99befd9b0e7b25253cd16a5407825286ff581d6df283c4ae10dd20777111ae54f8098a7517df76b0a8f0565ca1ed04e4b8c9badc76492629f430223dcf523836a80fdb0bde7597942a188f03616047cec47f6f220f18e0bae8cf317754807970d2232d01d87c84aa94155409da9e3de623190cc2e96dff0bd7aa5898d09af; _y18_s21_=ca1d0606; __yjs_st=2_ODY4ZDU5MmIwNGJjYzgwMTcwYTE5ZGIyMzhlMDYxMGE3YjgzZGE3NWFjNTQzNDkyM2NjYTFiOGM1ZjNmNWE3ZDYzNjVkOTQ4NjE3MWQwNTIxOTk4NWYwMzhkNGMyMDMwZWRmYTc2N2FhZmNlMmUwYTgwMDI1ZTBhZDE2MTRkOWY1NjBhNmI5Mzg0YmE1OWUzODFhMTFmZTA5ZDFiNTk5M2U0NTMzMjU0MDNkMjM4NGEzNGQ2YWJhMzIzN2M1NDg2NGYwZmI2MGUyNTBjMDA2MTFjMGIwMTgyZTFmOWRhNjQ2NDA5YmExZTczZTgyZGU5MDgyNGZiNTE3MDdjNGE0MzJmZjBiOTNlZWRiZTcxMGQyMDM0NGExYWIzMjI1YjRlXzdfZTVhOGQ3Yzk=",
        "Referer": f'https://aiqicha.baidu.com/company_detail_{data["pid"]}',
        "X-Requested-With": "XMLHttpRequest",
        "Zx-Open-Url": f'https://aiqicha.baidu.com/company_detail_{data["pid"]}'
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                         connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as client:
            async with client.request(method="GET", proxy=proxy, url=url, params=params, headers=headers,
                                      timeout=set_timeout) as rs:
                if rs.status == 200:
                    result = json.loads(await rs.text())
                    result = result["data"]["basicData"]
                    province = f'{result["district"].split("省")[0]}省' if "省" in result[
                        "district"] else f'{result["district"].split("市")[0]}市'
                    result = {
                        "name_cn": result["entName"],
                        "name_en": "",
                        "legal_person": result["legalPerson"],
                        "registered_capital": result["regCapital"],
                        "really_capital": result["realCapital"],
                        "found_date": result["startDate"],
                        "issue_date": result["annualDate"],
                        "social_credit_code": result["unifiedCode"],
                        "organization_code": result["orgNo"],
                        "regist_code": result.get("licenseNumber", ""),
                        "taxpayer_code": result["regNo"],
                        "imp_exp_enterprise_code": "",
                        "industry_involved": result["industry"],
                        "type": result["entType"],
                        "license_start_date": result["startDate"],
                        "license_end_date": result["openTime"].split("至")[-1].strip(),
                        "regist_office": result["authority"],
                        "staff_size": "",
                        "insured_size": "",
                        "province": province,
                        "address": result["addr"],
                        "business_scope": result["scope"],
                        "email": result["email"],
                        "unit_phone": result["telephone"],
                        "fax": "",
                        "website": result["website"],
                        "regist_address": result["regAddr"],
                        "transformer_name": result["prevEntName"],
                        "status": result["openStatus"],
                    }
                    # print(result)
                    return result
                else:
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await aqc_detail(**kwargs)
    except Exception as e:
        print("qcc_detail", e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
            async with client.request(method="POST", proxy=proxy, url=url, data=data, headers=headers,
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
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await gsxt(**kwargs)
    except Exception as e:
        print('gsxt', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
            async with client.request(method='POST', proxy=proxy, url=url, params=params, headers=headers,
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
                    time.sleep(randint(1, 2))
                    retry = kwargs.get("retry", 0)
                    retry += 1
                    if retry >= 3:
                        return None
                    kwargs["retry"] = retry
                    return await gsxt_detail(**kwargs)
    except Exception as e:
        print('gsxt_detail', e)
        time.sleep(randint(1, 2))
        retry = kwargs.get("retry", 0)
        retry += 1
        if retry >= 3:
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
    proxy = 'http://127.0.0.1:1080'
    # rs = asyncio.get_event_loop().run_until_complete(test())
    # proxy = asyncio.get_event_loop().run_until_complete(get_proxy())
    # print(proxy)
    rs = asyncio.get_event_loop().run_until_complete(tyc(**{"key": "特变电工湖南工程有限公司", "proxy": proxy}))
    # rs = asyncio.get_event_loop().run_until_complete(qcc(**{"key": "特变电工湖南工程有限公司", "proxy": proxy}))
    # rs = asyncio.get_event_loop().run_until_complete(
    #     qcc_detail(**{"url": "https://www.qcc.com/firm/963f4179841540334d3a16db3fc3567d.html"}))
    # rs = asyncio.get_event_loop().run_until_complete(aqc(**{"key": "哔哩哔哩"}))
    # rs = asyncio.get_event_loop().run_until_complete(aqc_detail(**{"data": {"pid": "43880125442188"}}))
    # rs = asyncio.get_event_loop().run_until_complete(gsxt(**{"key": "上海宽娱数码科技有限公司"}))
    # pripid = "D1FDF711DFE03EE312CC2ACD3CE218AB448EC78EC78E61ABE228E2ABE2ABE2ABEEABE2ABDF960DC782CB82C7647C-1618992356543"
    # pripid = "0CFD2A1102E0E3E3CFCCF7CDE1E2C5AB998E1A8E1A8EBCAB3FAB3FAB3FAB3FABED75E1F63324BC8E1A8E1A6473B6-1618991419697"
    # rs = asyncio.get_event_loop().run_until_complete(gsxt_detail(**{"data": {"pripid": pripid}}))
    # rs = asyncio.get_event_loop().run_until_complete(get_proxy())
    # rs = asyncio.get_event_loop().run_until_complete(query_ip(**{"proxy": "http://182.111.108.203:45113"}))
    print(rs)
