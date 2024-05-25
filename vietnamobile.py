import httpx
from bs4 import BeautifulSoup as Bs4
import time
import os
import datetime
import random,json
from urllib.parse import unquote
import aiohttp
import urllib3,re
import json
<<<<<<< HEAD
#requests.packages.urllib3.disable_warnings()
#requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
=======
>>>>>>> 6c8d50a9011435ee3727413c74abb86ad5d43502
httpx._config.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
async def sendOtp(phone):
  headers={
    'user-agent':'Vietnamobile/4 CFNetwork/1325.0.1 Darwin/21.1.0',
    'x-device-id':'BA7ABF14-BCC4-47EF-964F-DEF1B9E68541'
  }
  url='https://selfcare.vietnamobile.com.vn/api/account/register'
  data={
    'msisdn':'+84'+phone[1:]
  }
  print(data)
  req=httpx.post(url,headers=headers,json=data)
  if req.status_code<400:
    js=req.json()
    if js['code']==None:
      print(f'{phone} sent otp success')
      return {'phone':phone,'transId':js['data']['transId']}
  print(f'{phone} can\'t send otp')
  return False
async def register(headers,otp):
  headers['user-agent']='Vietnamobile/4 CFNetwork/1325.0.1 Darwin/21.1.0'
  headers['x-device-id']='BA7ABF14-BCC4-47EF-964F-DEF1B9E68541'
  header=headers
  url='https://selfcare.vietnamobile.com.vn/api/account/register/confirm'
  data={
    "transId": headers['transId'],
    "otp": otp,
    "password": "123123_Qwe"
  }
  #req=httpx.post(url,headers=headers,json=data)
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post(url,headers=headers,json=data) as res:
      js=await res.json()
      if res.status<400:
        if js['code']==None:
          print(f'{headers["phone"]} register success')
          headers=headers|js['data']
          
          return {'result':True,'headers':headers}
      print(f'{headers["phone"]} can\'t register')
      return {'result':False,'message':js['message']}

async def login(headers):
  url='https://selfcare.vietnamobile.com.vn/api/auth/loginPassword'
  header={
    'user-agent':headers['user-agent'],
    'x-device-id':headers['x-device-id']
  }
  data={
    "msisdn": "+84"+headers['phone'][1:],
    "password": "123123_Qwe"
  }
  req=httpx.post(url,headers=header,json=data)
  if req.status_code<400:
    js=req.json()
    if js['code']==None:
      print(f'{headers["phone"]} login success')
      headers['token']=js['data']['token']
      return headers
  print(f'{headers["phone"]} can\'t login')
  return False
  
async def getInfo(headers):
  url='https://selfcare.vietnamobile.com.vn/api/profile'
  header={
    'user-agent':headers['user-agent'],
    'x-device-id':headers['x-device-id'],
    'authorization':'Bearer '+headers['token']
  }
  req=httpx.get(url,headers=header)
  if req.status_code<400:
    js=req.json()
    if js['code']==None:
      js=js['data']
      url='https://selfcare.vietnamobile.com.vn/api/profile/personalInfo'
      req=httpx.get(url,headers=header)
      if req.status_code<400:
        js1=req.json()
        if js1['code']==None:
          js=js|js1['data']
          print(f'{headers["phone"]} get information success')
          return js
  print(f'{headers["phone"]} can\'t get information')
  return False
