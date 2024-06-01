import requests
from bs4 import BeautifulSoup as Bs4
import time
import os
import datetime
import random,json
from urllib.parse import unquote
import aiohttp

async def sendOtp(phone):
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
  }
  data={"account":phone,"password":"123123_Qwe","account_target":"","device_id":"webportal-3ecac22a-01c8-400d-a1ee-4b95cbe9f1a2-1710859612951","checksum":None,"otp_trust":"","errors":{},"type":"otp_login","featureCode":"myviettel://login_mobile"}
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post('https://vietteltelecom.vn/api/login-user-by-phone',headers=headers,json=data) as res:
      if res.status<400:
        print('New OTP sent to '+phone)
        return True
  print('Can\'t send new OTP to '+phone)
  return False
async def sentOtpReg(phone):
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
  }
  data={"msisdn":phone,"type":"register"}
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post('https://vietteltelecom.vn/api/get-otp',headers=headers,json=data) as res:
      if res.status<400:
        print('New OTP sent to '+phone)
        return True
  print('Can\'t send new OTP to '+phone)
  return False
async def register(phone,otp):
  headers={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"}
  url='https://vietteltelecom.vn/api/register-user-by-phone'
  data={"isdn":phone,"password":"123123_Qwe","password_confirmation":"123123_Qwe","otp":otp,"device_id":"webportal","regType":None,"listAcc":"","captcha":None,"isWeb":1,"captcha_code":"","sid":None,"checksum":None}
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post(url,headers=headers,json=data) as res:
      js=await res.json()
      if res.status<400:
        if js['errorCode']==0:
          print(f'{phone} register success')
          return {'result':True,'headers':headers,'phone':phone,'checksum':js['data']['data']['checksum']}
      print(f'{phone} can\'t register')
      return {'result':False,'message':js['message']}
async def loginByChecksum(input):
  headers={ 
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "cookie":""
  }
  data={"account":input['phone'],"password":"123123_Qwe","account_target":"","device_id":"webportal-3ecac22a-01c8-400d-a1ee-4b95cbe9f1a2-1710859612951","checksum":input['checksum'],"otp_trust":None,"errors":{},"type":"otp_login","featureCode":"myviettel://login_mobile"}
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post('https://vietteltelecom.vn/api/login-user-by-phone',headers=headers,json=data) as res: 
      if res.status<400:
        js=(await res.json())
        if js['errorCode']==0:
          print(f'{input["phone"]} login success')
          cookies = session.cookie_jar.filter_cookies('https://vietteltelecom.vn')
          for key, cookie in cookies.items():
            headers['cookie'] += cookie.key +'='+cookie.value+';'
            if 'X-XSRF-TOKEN' in cookie.key:
              headers['X-XSRF-TOKEN']=cookie.value
          return {'headers':headers,'phone':input["phone"],'data':js['data']['data']}
  print(f'{input["phone"]} can\'t login')
  return False
async def login(phone,otp):
  headers={
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "cookie":""
  }
  data={"account":phone,"password":"123123_Qwe","account_target":"","device_id":"webportal-3ecac22a-01c8-400d-a1ee-4b95cbe9f1a2-1710859612951","checksum":None,"otp_trust":otp,"errors":{},"type":"otp_login","featureCode":"myviettel://login_mobile"}
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.post('https://vietteltelecom.vn/api/login-user-by-phone',headers=headers,json=data) as res:
      if res.status<400:
        print(f'{phone} login success')
        cookies = session.cookie_jar.filter_cookies('https://vietteltelecom.vn')
        for key, cookie in cookies.items():
          headers['cookie'] += cookie.key +'='+cookie.value+';'
          if 'X-XSRF-TOKEN' in cookie.key:
            headers['X-XSRF-TOKEN']=cookie.value
        return {'headers':headers,'phone':phone}
  print(f'{phone} can\'t login')
  return False 
async def getInfo(headers):
  url='https://vietteltelecom.vn/thong-tin-tai-khoan'
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.get(url,headers=headers['headers']) as res:
      cookies = session.cookie_jar.filter_cookies('https://vietteltelecom.vn')
      ck=''
      cs=None
      for key, cookie in cookies.items():
        if 'X-XSRF-TOKEN' in cookie.key:
          cs=cookie.value
        ck += cookie.key +'='+cookie.value+';'
      url='https://vietteltelecom.vn/api/get-user-pre-info'
      #url='https://vietteltelecom.vn/api/get-info-user'

      async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.post(url,headers={'cookie':ck}) as res:
          if res.status<400:
            js=await res.json()
            data=js
            url='https://vietteltelecom.vn/api/auth/user'
            async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
              async with session.get(url,headers={'cookie':ck}) as res:
                if res.status<400:
                  js=await res.json()
                  if len(js)>0:
                    data=data|js 
                    url='https://vietteltelecom.vn/api/get-status-user'
                    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
                      async with session.post(url,headers={'cookie':ck}) as res:
                        if res.status<400:
                          js=await res.json()
                          data=data|js['data']
                      url='https://apigami.viettel.vn/mvt-api/myviettel.php/getPromotionDataMyvtV3'
                      data1={
                        'is_app':'1',
                        'list_all':'1',
                        'token':headers['data']['token'],
                        'type':'data_all'
                      }
                    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
                      async with session.post(url,data=data1,headers=headers['headers']) as res:
                        if res.status<400:
                          js=await res.json()
                          if 'data' in js:
                            data['list-promotion']=js['data']
              '''print(headers) 
              async with session.post(url,headers={'cookie':ck}) as res:
                if res.status<400:
                  print(f'{headers["phone"]} get info of success')
                  js=await res.json()
                  data=js['data'][0]
                  url='https://vietteltelecom.vn/api/get-status-user'
                  async with session.post(url,headers={'cookie':ck}) as res:
                    if res.status<400:
                      js=await res.json()
                      data=data|js['data']
                      url='https://vietteltelecom.vn/api/auth/user'
                      async with session.get(url,headers={'cookie':ck}) as res:
                        if res.status<400:
                          js=await res.json()
                          data=data|js
                          url='https://vietteltelecom.vn/api/get-info-user'
                          async with session.post(url,headers={'cookie':ck}) as res:
                            if res.status<400:
                              print(await res.json())'''
              print(f'{headers["phone"]} get information success')
              return {'data':data,'headers':headers} 
  print(f'{headers["phone"]} can\'t get information')
  return False
