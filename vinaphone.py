import httpx
from bs4 import BeautifulSoup as Bs4
import time
import os
import datetime
import random,json
from urllib.parse import unquote
import aiohttp
import urllib3,re

import httpx


httpx._config.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
async def sendOtp(phone,type=None):
  url='https://api-myvnpt.vnpt.vn/mapi_v2/services/otp_send'
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  }
  if not type:
    type='authen_msisdn'
  elif type=='updatePassword':
    type='authen_miss_password'
  data={
  "msisdn": '84'+phone[1:],
  "otp_service": type,
  "tinh_id": "",
  "for_test": ""
}
  req=httpx.post(url,headers=headers,json=data)
  if req.status_code<400:
    print('New OTP sent to '+phone)
    return True
  print('Can\'t send new OTP to '+phone)
  return False
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post(url,headers=headers,json=data) as res:
      if res.status<400:
        print('New OTP sent to '+phone)
        return True
  print('Can\'t send new OTP to '+phone)
  return False
async def loginByPassword(phone,password='5c5d10e87562f09ceb66dbad807cd7a5'):
  url='https://my.vnpt.com.vn/mapi/services/authen_msisdn'
  data={"device_info":"Firefox","fcm_registration_token":"","mode":"password","msisdn":phone,"password":password,"session":""}
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
  }
  req=httpx.post(url,headers=headers,json=data)
  if req.status_code<400:
    js=req.json()
    if js['error_code']=='0':
      print(f'{phone} login success')
      return {'headers':headers,'session':js['session'],'msisdn':js['msisdn'],'phone':phone}
  print(f'{phone} can\'t login')
  return False
      

async def loginByOtp(phone,otp):
  url='https://api-myvnpt.vnpt.vn/mapi_v2/services/authen_msisdn'
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
  }
  data={"device_info":"Firefox","fcm_registration_token":"","mode":"otp","msisdn":'84'+phone[1:],"password":otp,"session":""}
  req=httpx.post(url,headers=headers,json=data)
  if req.status_code<400:
    js=req.json()
    if js['error_code']!='wrong_otp':
      session=js['session']
      headers['cookie']=req.headers['set-cookie']
      headers['msisdn']='84'+phone[1:]
      print(f'{phone} login success')
      return {'headers':headers,'session':session,'phone':phone}
  print(f'{phone} can\'t login')
  return False
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post(url,headers=headers,json=data) as res:
      if res.status<400:
        js=await res.json()
        session=js['session']
        headers['cookie']=''
        cookies = session.cookie_jar.filter_cookies('https://my.vnpt.com.vn')
        for key, cookie in cookies.items():
          headers['cookie'] += cookie.key +'='+cookie.value+';'
        print(f'{phone} login success')
        return {'headers':headers,'session':session,'phone':phone}
  print(f'{phone} can\'t login')
  return False
async def updatePassword(headers,otp):
  url='https://api-myvnpt.vnpt.vn/mapi_v2/services/authen_miss_password'
  data={
    "password": "5C5D10E87562F09CEB66DBAD807CD7A5",
    "otp": otp,
    "msisdn": "84"+headers['phone'][1:]
  }
  req=httpx.post(url,headers=headers['headers'],json=data)
  if req.status_code<400:
    js=req.json()
    if js['error_code']=='0':
      print(f'{headers["phone"]} Update password success')
      return {'result':True}
  print(f'{headers["phone"]} can\'t update password')
  return {'result':False,'content':js}
async def getInfo(headers):
  url='https://my.vnpt.com.vn/mapi/services/mobile_IN_balances'
  data1={"msisdn":headers['msisdn'] if 'msisdn' in headers else ('84'+headers['phone'][1:]),"session":headers['session']}
  #ck=re.search('.*TS01d53577=(.*?);.*',headers['headers']['cookie']).group(1)
  header={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'}
  req=httpx.post(url,headers=header,json=data1)
  data=(req.json())['result']
  if len(data)>0:
    dt={}
    dt['balance']=data
    req=httpx.post('https://my.vnpt.com.vn/mapi/services/mobile_get_info',headers=header,json=data1)
    data=(req.json())['result']
    data=data|dt
    req=httpx.post('https://my.vnpt.com.vn/mapi/services/mobile_data_get_high_bandwidth',headers=header,json=data1)
    js=(req.json())['result']
    data=data|js
    req=httpx.post('https://my.vnpt.com.vn/mapi/services/get_rank_vnp_plus',headers=header,json=data1)
    js=(req.json())['result']
    data=data|js
    print(f'{headers["phone"]} get information success')
    return {'data':data,'phone':headers['phone']}
  print(f'{headers["phone"]} can\'t get information')
  return False
