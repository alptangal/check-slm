import asyncio
import websockets
import os
import re,json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import get
import random
from datetime import datetime,timedelta
import server
from guild import *
from viettel import *
import vinaphone as vnpt
import vietnamobile
import aiohttp
import ast
import collections 
import websocketsServer,websocketsClient
from bs4 import BeautifulSoup as Soup


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
VIETTELS='032, 033, 034, 035, 036, 037, 038, 039, 096, 097, 098, 086'
VIETTELS=VIETTELS.split(',')
VINAPHONES=' 091, 094, 088, 081, 082, 083, 084, 085'
VINAPHONES=VINAPHONES.split(',')
VIETNAMOBILE='052, 056, 058, 092'
VIETNAMOBILE=VIETNAMOBILE.split(',')
HEADERS = []
THREADS = []
USERNAMES = [] 
GUILDID = 1122707918177960047 
RESULT=None
BOT_NAME='SIM carrier'
SESSION_ID=None
SESSION_ID_OLD=None
LAST_UPDATE=None
LAST_MSG=None

def correctSingleQuoteJSON(s):
    rstr = ""
    escaped = False

    for c in s:
    
        if c == "'" and not escaped:
            c = '"' # replace single with double quote
        
        elif c == "'" and escaped:
            rstr = rstr[:-1] # remove escape character before single quotes
        
        elif c == '"':
            c = '\\' + c # escape existing double quotes
   
        escaped = (c == "\\") # check for an escape character
        rstr += c # append the correct json
    
    return rstr
def remove_duplicates(l):
    seen = {}
    res = []
    for item in l:
        if item not in seen:
            seen[item] = 1
            res.append(item)
    return res
BASE_URL='https://shoebee-fswaboivdxpaan5ewbppbf.streamlit.app/'
#https://shoebee-fswaboivdxpaan5ewbppbf.streamlit.app/api/v2/app/disambiguate
@client.event
async def on_ready():
    guild = client.get_guild(GUILDID)
    await tree.sync(guild=guild)
    global HEADERS, THREADS, USERNAMES,RESULT,BOT_NAME,SESSION_ID,SESSION_ID_OLD,LAST_MSG
    try: 
      req=requests.get('http://localhost:8888')
      headers={
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
      }
      async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(BASE_URL,headers=headers,allow_redirects=False) as res:
          if res.status<400:
            location=res.headers['location']
            headers['cookie']=''
            async with session.get(location,headers=headers,allow_redirects=False) as res:
              cookies = session.cookie_jar.filter_cookies('streamlit.app')
              for key, cookie in cookies.items():
                headers['cookie'] += cookie.key +'='+cookie.value+';'
            async with session.get(BASE_URL+'api/v2/app/disambiguate',headers=headers) as res:
              if res.status<400:
                headers['x-csrf-token']=res.headers['x-csrf-token']
                url=BASE_URL+'api/v2/app/status'
                req=requests.get(url,headers=headers)
                js=req.json()
                print(js)
                if js['status']!=5:
                  url=BASE_URL+'api/v2/app/resume'
                  req=requests.post(url,headers=headers)
      
      await client.close()
      exit()
    except:
        server.b()
        
        guild = client.get_guild(GUILDID)
        RESULT=await getBasic(guild)
        if any(item not in str(RESULT['phonesCh'].available_tags) for item in ['🔃Loading','✔Loaded','Viettel','Vinaphone','Vietnamobile','Mobifone']):
          for item in ['🔃Loading','✔Loaded','Viettel','Vinaphone','Vietnamobile','Mobifone']:
            if item not in str(RESULT['phonesCh']):
              await RESULT['phonesCh'].create_tag(name=item)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        if not keepOnline.is_running():
          keepOnline.start()
        if not taskGetInfo.is_running():
          taskGetInfo.start(guild)
        if not taskUpdatePhone.is_running():
          taskUpdatePhone.start(guild)
        if not taskSendOtp.is_running():
          taskSendOtp.start(guild)
        if not taskLogin.is_running():
          taskLogin.start(guild)
@tasks.loop(minutes=15)
async def keepOnline():
  headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
  }
  async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
    async with session.get(BASE_URL,headers=headers,allow_redirects=False) as res:
      if res.status<400:
        location=res.headers['location']
        headers['cookie']=''
        async with session.get(location,headers=headers,allow_redirects=False) as res:
          cookies = session.cookie_jar.filter_cookies('streamlit.app')
          for key, cookie in cookies.items():
            headers['cookie'] += cookie.key +'='+cookie.value+';'
        async with session.get(BASE_URL+'api/v2/app/disambiguate',headers=headers) as res:
          if res.status<400:
            headers['x-csrf-token']=res.headers['x-csrf-token']
            url=BASE_URL+'api/v2/app/status'
            req=requests.get(url,headers=headers)
            js=req.json()
            print(js)
            if js['status']!=5:
              url=BASE_URL+'api/v2/app/resume'
              req=requests.post(url,headers=headers)
@client.event
async def on_disconnect():
    global RESULT,SESSION_ID
    if RESULT and SESSION_ID:
        for thread in RESULT['statusBotCh'].threads:
            if BOT_NAME in thread.name:
                msgs=[msg async for msg in thread.history(oldest_first=True)]
                old=re.search('Sessions are `(.*?)` actived',msgs[0].content).group(1)
                i=int(old)-1 if int(old)>1 else 0
                await msgs[0].edit(content='Sessions are `'+str(i)+'` actived')
                if i==0 and len(msgs)>1:
                    await msgs[-1].delete()
@tasks.loop(seconds=1)
async def taskUpdatePhone(guild):
  RESULT=await getBasic(guild)
  phones=[]
  try:
    async for msg in RESULT['rawsCh'].history():
      phones.append(msg.content.strip())
      isset=False
      phoneCh=RESULT['phonesCh'].threads+[thread async for thread in RESULT['phonesCh'].archived_threads()]
      for thread in phoneCh:
        if msg.content.strip() in thread.name.strip():
          isset=True
      if not isset:
        tags=[]
        for tag in RESULT['phonesCh'].available_tags:
          if 'loading' in tag.name.lower():
            tags.append(tag)
        phone=msg.content.strip()
        thread=await RESULT['phonesCh'].create_thread(name=phone,content='loading...',applied_tags=tags)
    phones=remove_duplicates(phones)
    seen={}
    async for msg in RESULT['rawsCh'].history():
      if msg.content not in seen:
        seen[msg.content]=1
      else:
        await msg.delete()
  except:
    pass
@tasks.loop(seconds=3)
async def taskSendOtp(guild):
  RESULT=await getBasic(guild)
  phoneCh=RESULT['phonesCh'].threads+[thread async for thread in RESULT['phonesCh'].archived_threads()]
  for thread in phoneCh:
      if any(item.strip() in thread.name for item in VIETTELS):
        try:
          msgs=[msg async for msg in thread.history()]
          if len(msgs)==1 and 'loading' in msgs[0].content:
            rs=await sentOtpReg(thread.name)
            if rs:
              await thread.send('New otp sent to '+thread.name)
        except:
          pass
      elif any(thread.name.startswith(item.strip()) for item in VINAPHONES):
        try:
          msgs=[msg async for msg in thread.history()]
          if len(msgs)==1 and 'loading' in msgs[0].content:
            rs=await vnpt.sendOtp(thread.name)
            if rs:
              await thread.send('New otp sent to '+thread.name)
        except:
          pass
      elif any(thread.name.startswith(item.strip()) for item in VIETNAMOBILE):
        try:
          msgs=[msg async for msg in thread.history()]
          if len(msgs)==1 and 'loading' in msgs[0].content:
            rs=await vietnamobile.sendOtp(thread.name)
            if rs:
              await thread.send('New otp sent to '+thread.name)
        except:
          pass

@tasks.loop(seconds=3)
async def taskLogin(guild):
  print('taskLogin is running')
  RESULT=await getBasic(guild)
  phoneCh=RESULT['phonesCh'].threads#+[thread async for thread in RESULT['phonesCh'].archived_threads()]
  for thread in phoneCh:
      if any(item.strip() in thread.name for item in VIETTELS):
        try:
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if len(msgs)==3 and 'loading' in msgs[0].content: 
            otp=msgs[len(msgs)-1].content
            rs=await register(thread.name,otp)
            if rs['result']:
              log=await loginByChecksum(rs)
              if log:
                for i,msg in enumerate(msgs):
                  if i!=0 and 'headers' not in msgs[0].content:
                    await msg.delete()
                  else: 
                    await msg.edit(content=rs)
              else:
                await thread.send('Try re-create account again!')
            else:
              await thread.send(rs['message'])
        except Exception as err:
          print(err,333)
          pass
      elif any(item.strip() in thread.name for item in VINAPHONES):
        try:
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if 'session' in msgs[0].content and datetime.datetime.now().timestamp()-msgs[0].edited_at.timestamp()>=3600:
            rs=await vnpt.loginByPassword(thread.name)
            if rs:
              await msgs[0].edit(content=rs)
          elif 'New otp sent to update password' not in msgs[len(msgs)-1].content and ((len(msgs)==3 and 'loading' in msgs[0].content) ): 
            otp=msgs[len(msgs)-1].content
            rs=await vnpt.loginByOtp(thread.name,otp)
            if rs:
              print(f'{thread.name} login success')
              for i,msg in enumerate(msgs):
                if i!=0 and 'headers' not in msgs[0].content:
                  await msg.delete()
                else: 
                  await msg.edit(content=rs)
              rs=await vnpt.sendOtp(thread.name,'updatePassword')
              if rs:
                await thread.send('New otp sent to update password')
              else:
                await thread.send('Something went wrong, try delete channel to restart process')
          elif len(msgs)>2 and 'New otp sent to update password' in msgs[-2].content:
            headers=json.loads(msgs[0].content.replace("'",'"'))
            rs=await vnpt.updatePassword(headers,msgs[-1].content)
            if rs:
              for i,msg in enumerate(msgs):
                if i!=0 and 'headers' in msgs[0].content:
                  await msg.delete()
        except Exception as err:
          print(err,222)
          pass
      elif any(item.strip() in thread.name for item in VIETNAMOBILE):
        try:
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if (len(msgs)==3 and 'transId' in msgs[0].content) or ('session' in msgs[0].content and datetime.datetime.now().timestamp()-msgs[0].edited_at.timestamp()>=3600): 
            otp=msgs[len(msgs)-1].content
            headers=json.loads(msgs[0].content.replace('\'','\"').replace('True','true').replace('False','false').replace('None','null'))
            if headers['transId']!=None:
              rs=await vietnamobile.register(headers,otp)
              if rs['result']==True:
                headers=await vietnamobile.login(rs['headers'])
                if headers:
                  for i,msg in enumerate(msgs):
                    if i!=0 and 'headers' not in msgs[0].content:
                      await msg.delete() 
                    else: 
                      await msg.edit(content=rs['headers'])
                else:
                  await thread.send('Try re-create account again')
              else:
                await thread.send(rs['message'])
        except Exception as error:
          print(error,3333)
          pass
@tasks.loop(seconds=1)  
async def taskGetInfo(guild):
  print('taskGetInfo is running')
  RESULT=await getBasic(guild)
  phoneCh=RESULT['phonesCh'].threads+[thread async for thread in RESULT['phonesCh'].archived_threads()]
  for thread in phoneCh:
    try:
        if any(item.strip() in thread.name for item in VIETTELS):
          try:
            msgs=[msg async for msg in thread.history(oldest_first=True)]
          except:
            pass
          if len(msgs)==1 and 'loading' not in msgs[0].content or 'headers' in msgs[0].content:
            #try:
            headers=await loginByChecksum(json.loads(msgs[0].content.replace('\'','\"').replace('True','true').replace('False','false').replace('None','null')))
            if headers:
              try:
                rs=await getInfo(headers)
              except:
                rs=False
              if rs:
                if any(it not in str(thread.applied_tags).lower() for it in ['loaded','viettel']):
                  tags=[]
                  for tag in RESULT['phonesCh'].available_tags:
                    if any(item in tag.name.lower() for item in ['loaded','viettel']):
                      await thread.add_tags(tag)
                    elif 'loading' in tag.name.lower():
                      await thread.remove_tags(tag)
                js=rs['data']
                caution=[]
                embed = discord.Embed(title=js['phone_number']+'- '+js['actStatusName'], description=js['productCode']+'/ '+js['serviceType'],colour=discord.Colour.red()) #,color=Hex code
                embed.add_field(name="Owner", value=js['fullName'],inline=True)
                embed.add_field(name="CCCD", value=js['cmnd_number'],inline=True)
                embed.add_field(name="CCCD_Date", value=js['cmnd_date'],inline=True)
                embed.add_field(name="Location", value=js['cmnd_place'],inline=True) 
                embed.add_field(name="Birthday", value=js['birthday'],inline=True)
                embed.add_field(name=" ", value='',inline=False)
                for i,item in enumerate(js['extraInfo']):
                  if i==0 and 'value' in item and int(item['value'])<5000:
                    caution.append('**Balance too low**')
                  if 'expire' in item and item['expire']:
                    expired=datetime.datetime.strptime(item['expire'],f'%m/%d/%Y %H:%M:%S %p')
                    expired=expired.strftime('%d/%m/%Y %H:%M:%S %p')
                    if item['name']=='Tài khoản gốc':
                      exp=datetime.datetime.strptime(item['expire'],f'%m/%d/%Y %H:%M:%S %p')
                      if datetime.datetime.now().timestamp()-exp.timestamp()>4320000:
                        caution.append('**Balance expried soon**')
                  embed.add_field(name=item['name'] if 'name' in item else None, value=(str(item['value']) if 'value' in item else 'None')+' '+(item['unit'] if 'unit' in item else 'None')+' - expire: '+str(expired),inline=True)
                embed.add_field(name=" ", value='',inline=False)
                embed.add_field(name="Points", value=js['viettelPlusInfo']['point_can_used'],inline=True)
                embed.add_field(name="Point Expire", value=js['viettelPlusInfo']['point_expired'],inline=True)
                issetPromotion=False
                for cate in js['list-promotion']:
                  for item1 in cate['list']:
                    if 'used_state' in item1 and int(item1['used_state'])>0:
                      if issetPromotion==False:
                        embed.add_field(name="Danh sách gói cước đang sử dụng", value='',inline=False)
                        issetPromotion=True
                      embed.add_field(name="🟢 Gói cước đang áp dụng" if int(item1['used_state'])==1 else "🟡 Gói cước chờ gia hạn", value='**'+(item1['code'] if 'code' in item1 else item1['pack_code'])+'** giá **'+str(item1['price'])+'** - `'+item1['cycle']+'`',inline=True)
                embed.set_footer(text='Updated at '+str(datetime.datetime.now()+timedelta(hours=7)).split('.')[0]+' ** Powered By VIETTEL')
                if len(msgs)==1:
                  await thread.send(embed=embed) 
                else:
                  try:
                    await msgs[1].edit(embed=embed)
                  except:
                    msg=await thread.send('re-active thread')
                    await msg.delete()
                if caution:
                  phone=thread.name
                  async for msg in RESULT['rawsCh'].history():
                    if phone.strip()==msg.content.strip():
                      owner=msg.author
                if len(caution)>0 and len(msgs)==2 and 'owner' in locals():
                  await thread.send(owner.mention+'\n')
                elif len(caution)>0 and len(msgs)>2 and 'owner' in locals():
                  for i,msg in enumerate(msgs):
                    if i>1:
                      await msg.delete()
                  await thread.send(owner.mention+'\n')
                elif len(caution)==0 and len(msgs)>2:
                  for i,msg in enumerate(msgs):
                    if i>1:
                      await msg.delete()
                for noti in caution:
                  await thread.send(f'⚠️ {noti} 🆘\n')
        elif any(item.strip() in thread.name for item in VINAPHONES):
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if len(msgs)==1 and 'loading' not in msgs[0].content or 'session' in msgs[0].content:
              #try:
              rs=await vnpt.getInfo(json.loads(msgs[0].content.replace("'",'"')))
              if rs:
                if any(it not in str(thread.applied_tags).lower() for it in ['loaded','vinaphone']):
                  tags=[]
                  for tag in RESULT['phonesCh'].available_tags:
                    if any(item in tag.name.lower() for item in ['loaded','vinaphone']):
                      await thread.add_tags(tag)
                    elif 'loading' in tag.name.lower():
                      await thread.remove_tags(tag)
                js=rs['data']
                caution=[]
                a=False
                b=False
                embed = discord.Embed(title='0'+js['MA_TB'][2:], description=js['LOAI']+'/ '+('Trả sau' if js['TRA_SAU']=="1" else 'Trả trước'),colour=discord.Colour.blue()) #,color=Hex code
                embed.add_field(name="Owner", value=js['TEN_TB'],inline=True)
                embed.add_field(name="CCCD", value=js['SO_GT'],inline=True)
                embed.add_field(name="CCCD_Date", value=js['NGAYCAP_GT'] if 'NGAYCAP_GT' in js else None,inline=True)
                embed.add_field(name="Location", value=js['DIACHI'],inline=True) 
                embed.add_field(name="Birthday", value=js['NGAYSINH'],inline=True)
                embed.add_field(name=" ", value='',inline=False)
                for i,item in enumerate(js['balance']): 
                  if i==2 and 'REMAIN' in item and item['REMAIN']<5000:
                    caution.append('**Balance too low**')
                    
                  if 'ACC_EXPIRATION' in item and item['BALANCE_NAME']=='Tài khoản chính':
                    exp=datetime.datetime.strptime(item['ACC_EXPIRATION'],f'%d/%m/%Y %H:%M:%S')
                    if datetime.datetime.now().timestamp()-exp.timestamp()>4320000:
                      caution.append('**Balance expried soon**')
                  
                  embed.add_field(name=item['BALANCE_NAME'] if 'BALANCE_NAME' in item else 'None', value=(str(item['REMAIN']) if 'REMAIN' in item else 'None')+' đồng- expire: '+(str(item['ACC_EXPIRATION']) if 'ACC_EXPIRATION' in item else 'None'),inline=True)
                embed.add_field(name='Băng thông tốc độ cao', value=js['text_high_bandwidth_volume_remain']+'/ '+js['text_high_bandwidth_volume_total'],inline=True)
                embed.add_field(name=" ", value='',inline=False)
                embed.add_field(name="Rank", value=js['rank'],inline=True)
                embed.add_field(name="Point", value=js['point'],inline=True)
                embed.set_footer(text='Updated at '+str(datetime.datetime.now()+timedelta(hours=7)).split('.')[0]+' ** Powered By VINAPHONE')
                if caution:
                  phone=thread.name
                  async for msg in RESULT['rawsCh'].history():
                    if phone.strip()==msg.content.strip():
                      owner=msg.author
                if len(msgs)==1:
                  await thread.send(embed=embed) 
                else:
                  try:
                    await msgs[1].edit(embed=embed)
                  except:
                    msg=await thread.send('re-active thread')
                    await msg.delete()
                if len(caution)>0:
                  phone=thread.name
                  async for msg in RESULT['rawsCh'].history():
                    if phone.strip()==msg.content.strip():
                      owner=msg.author
                if len(caution)>0 and len(msgs)==2 and 'owner' in locals():
                  await thread.send(owner.mention+'\n')
                elif len(caution)>0 and len(msgs)>2 and 'owner' in locals():
                  #await msgs[len(msgs)-1].delete()
                  for i,msg in enumerate(msgs):
                    if i>1:
                      await msg.delete()
                  await thread.send(owner.mention+'\n')
                elif len(caution)==0 and len(msgs)>2:
                  for i,msg in enumerate(msgs):
                    if i>1:
                      await msg.delete()
                for noti in caution:
                  await thread.send(f'⚠️ {noti} 🆘\n')
        elif any(item.strip() in thread.name for item in VIETNAMOBILE): 
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if len(msgs)==1 and 'loading' not in msgs[0].content or 'token' in msgs[0].content:
            #try:
            rs=await vietnamobile.getInfo(ast.literal_eval(msgs[0].content))
            if not rs:
              print(ast.literal_eval(msgs[0].content))
              headers=await vietnamobile.login(ast.literal_eval(msgs[0].content))
              if headers:
                try:
                  await msgs[0].edit(content=headers)
                  rs=await vietnamobile.getInfo(headers)
                except:
                  msg=await thread.send('re-active thread')
                  await msg.delete()
            if rs:
              if any(it not in str(thread.applied_tags).lower() for it in ['loaded','vietnamobile']):
                  tags=[]
                  for tag in RESULT['phonesCh'].available_tags:
                    if any(item in tag.name.lower() for item in ['loaded','vietnamobile']):
                      await thread.add_tags(tag)
                    elif 'loading' in tag.name.lower():
                      await thread.remove_tags(tag)
              js=rs
              caution=[]
              embed = discord.Embed(title='0'+js['MSISDN'][2:], description=js['CALL_PLAN']+'/ '+('Trả sau' if js['POSTPAID_FLAG']=="Y" else 'Trả trước'),colour=discord.Colour.orange()) #,color=Hex code
              embed.add_field(name="Owner", value=js['FULL_NAME'],inline=True)
              embed.add_field(name="Gender", value=js['GENDER'],inline=True)
              embed.add_field(name="Email", value=js['userInfo']['email'],inline=True)
              embed.add_field(name="CCCD", value=js['ID'],inline=True)
              embed.add_field(name="CCCD_Date", value=None,inline=True)
              embed.add_field(name="Location", value=js['ADDRESS'],inline=True) 
              embed.add_field(name="Birthday", value=js['DOB'],inline=True)
              embed.add_field(name=" ", value='',inline=False)
              embed.add_field(name="Tài Khoản Chính", value=js['MAIN_ACCOUNT_BALANCE']+' đồng- expire: '+js['RESTRICTED_DATE'],inline=True)
              if int(js['MAIN_ACCOUNT_BALANCE'])<5000:
                caution.append('**Too low balance, need charge more money**')
              exp=datetime.datetime.strptime(js['RESTRICTED_DATE'],f'%d/%m/%Y %H:%M:%S')
              if datetime.datetime.now().timestamp()-exp.timestamp()>4320000:
                caution.append('**Balance expired soon, charge more money to keep SIM live**')
              if js['pcrfServices']:
                embed.add_field(name='Băng thông tốc độ cao', value=js['pcrfServices'][0]['QTALIST'][0]['QTABALANCE']+'/ '+js['pcrfServices'][0]['QTALIST'][0]['QTAVALUE'],inline=True)
              embed.add_field(name=" ", value='',inline=False)
              embed.add_field(name="Rank", value=js['LMS_RANK'],inline=True)
              embed.add_field(name="Point", value=js['LMS_POINT'],inline=True)
              embed.set_footer(text='Updated at '+str(datetime.datetime.now()+timedelta(hours=7)).split('.')[0]+' ** Powered By VINAPHONE')

              if len(msgs)==1:
                await thread.send(embed=embed) 
              else:
                await msgs[1].edit(embed=embed)
              if len(caution)>0:
                phone=thread.name
                async for msg in RESULT['rawsCh'].history():
                  if phone.strip()==msg.content.strip():
                    owner=msg.author
              if len(caution)>0 and len(msgs)==2 and 'owner' in locals():
                await thread.send(owner.mention+'\n')
              elif len(caution)>0 and len(msgs)>2 and 'owner' in locals():
                msgs=[msg async for msg in thread.history(oldest_first=True)]
                for i,msg in enumerate(msgs):
                  if i!=0 and i!=1:
                    await msg.delete()
                await thread.send(owner.mention+'\n')
              for noti in caution:
                await thread.send(f'⚠️ {noti} 🆘\n')
    except Exception as error:
      print(11111,error)
      pass
@tasks.loop(seconds=3)
async def ping(): 
    print(datetime.now())


@tree.command( 
    name="check_available_promotion",
    description="check available promotion applied on the phone",
    guild=discord.Object(id=GUILDID)
)
async def first_command(interaction):
  await interaction.response.defer()
  if any(item.strip() in interaction.channel.name for item in VIETTELS):
    msgs=[msg async for msg in interaction.channel.history(oldest_first=True)]
    header=await loginByChecksum(json.loads(msgs[0].content.replace('\'','\"').replace('True','true').replace('False','false').replace('None','null')))
    promotions=await getPromotions(header)
    if promotions:
      st=''
      if not os.path.exists('promotions'):
        os.mkdir('promotions')
      fileName="promotions/promotion_"+interaction.channel.name+".txt"
      f = open(fileName, "w",encoding="utf-8")
      for cate in promotions['data']:
        st+='🟢'+cate['name']+'\n'
        for item in cate['list']:
          st+='🟡🟡'+(item['code'] if 'code' in item else item['pack_code'])+'- '+str(item['price'])+'/ '+item['cycle']+'\n'
          detail=(Soup((item['detail'] if ('detail' in item and item['detail']) else item['des']),'html.parser')).getText()
          detail=detail.replace('.','.\n')
          st+='🔴🔴🔴'+detail+'\n**Đăng ký gói:**\n'+(item['regCommand'] if 'regCommand' in item else 'None')+'\n**Huỷ gói:**\n'+(item['canCommand'] if 'canCommand' in item else 'None')+'\n'
      f.write(st)
      f.close()
      await interaction.edit_original_response(content='Danh sách gói cước ưu đãi áp dụng cho thuê bao **'+interaction.channel.name+'**',attachments =[discord.File(fileName)])
  else:
    await interaction.edit_original_response(content='No data')
client.run(os.environ.get('botToken'))
