import requests
from bs4 import BeautifulSoup as Bs4
import time
import os
import datetime
import random,json
from urllib.parse import unquote
import aiohttp

async def sendOtp(phone):
    url='https://api.mobifone.vn/api/auth/getloginotp'
    data={
        'phone':phone
    }
    headers={
    'apisecret':'UEJ34gtH345DFG45G3ht1'
    }
    stop=False
    while not stop:
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            async with session.post(url,headers=headers,data=data) as res:
                if res.status<400:
                    js=await res.json()
                    if not js['errors']:
                        print(f'{phone} sent otp success')
                        return {'result':True,'headers':headers}
                    else:
                        print(f'{phone} error:{js.errors[0].message}')
    print(f'{phone} can\'t send otp')
    return {'result':False}
async def loginByOtp(phone,otp):
    headers={
        'user-agent':'MyMobiFone/4.13.1 (vms.com.MyMobifone; build:2; iOS 15.1.1) Alamofire/5.9.0',
        'apisecret':'UEJ34gtH345DFG45G3ht1',
    }
    url='https://api.mobifone.vn/api/auth/otplogin'
    data={
        'phone':phone,
        'otp':otp
    }
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.post(url,headers=headers,data=data) as res:
            if res.status<400:
                js=await res.json()
                if not js['errors']:
                    headers['deviceinfo']='iPhone 15 ProMax'
                    headers['uuid']='6B9105C4-4293-4247-BC54-3768959A8FF1'
                    headers['osinfo']='iOS, 18.1.1'
                    headers['appversion']='99.13.1'
                    headers['apisecret']=js['data']['apiSecret']
                    headers['userId']=js['data']['userId']
                    headers['phone']=phone[1:]
                    headers['refreshKey']=js['data']['refreshKey']
                    print(f'{phone} login success')
                    return {'result':True,'data':js['data'],'headers':headers,'phone':phone}
    print(f'{phone} can\'t login')
    return {'result':False,'message':js['errors'][0]}

async def getInfo(headers):
    url='https://api.mobifone.vn/api/user/getprofile'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.post(url,headers=headers) as res:
            if res.status<400:
                js=await res.json()
                print(js)
                if not js['errors']:
                    url='https://api.mobifone.vn/api/user/getphoneinfo'
                    async with session.post(url,headers=headers) as res:
                        if res.status<400:
                            js1=await res.json()
                            if not js1['errors']:
                                url='https://api.mobifone.vn/api/auth/refreshlogin'
                                data={
                                'refresh_key':headers['refreshKey'],
                                'user_id':headers['userId']
                                }
                                headers1=headers
                                headers1['apisecret']='UEJ34gtH345DFG45G3ht1'
                                req=requests.post(url,headers=headers1,data=data)
                                print(req.json())
                                js['data']=js['data'][0]|js1['data']
                                print(f'{headers["phone"]} get info success')
                                return {'result':True,'data':js['data']}
    print(f'{headers["phone"]} can\'t get info- {js['errors']}')
    return {'result':False}
