import asyncio
import os
import re,json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import get
import random
from datetime import datetime,timedelta
#import server
from guild import *
from viettel import *
import vinaphone as vnpt
import vietnamobile
import aiohttp
import ast
import collections 
#server.b() 


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
  
@client.event
async def on_ready():
    global HEADERS, THREADS, USERNAMES,RESULT
    guild = client.get_guild(GUILDID)
    #await tree.sync(guild=discord.Object(id=GUILDID))
    RESULT=await getBasic(guild) 
    if not taskGetInfo.is_running():
      taskGetInfo.start(guild)
    if not taskUpdatePhone.is_running():
      taskUpdatePhone.start(guild)
    if not taskLogin.is_running():
      taskLogin.start(guild)
    if not taskSendOtp.is_running():
      taskSendOtp.start(guild)

    
@tasks.loop(seconds=1)
async def taskKeepCookie(guild):
  RESULT=await getBasic(guild)
  for thread in RESULT['phonesCh'].threads:
    try:
      msgs=[msg async for msg in thread.history(oldest_first=True)]
      if any(item.strip() in thread.name for item in VIETTELS) and 'header' in msgs[0].content:
        headers=json.loads(msgs[0].content.replace("'",'"'))
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
          async with session.get('https://vietteltelecom.vn/thong-tin-tai-khoan',headers=headers['headers']) as res:
            print(res.status)
    except Exception as err:
      print(err)
      pass
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
        phone=msg.content.strip()
        thread=await RESULT['phonesCh'].create_thread(name=phone,content='loading...')
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
      elif any(thread.name.startswith(item.strip()) for item in VIETNAMOBILE):
        try:
          msgs=[msg async for msg in thread.history()]
          if len(msgs)==1 and 'loading' in msgs[0].content:
            rs=await vietnamobile.sendOtp(thread.name)
            if rs:
              await msgs[0].edit(content=rs)
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
          if (len(msgs)==1 and 'loading' in msgs[0].content) or ('session' in msgs[0].content and datetime.datetime.now().timestamp()-msgs[0].edited_at.timestamp()>=3600): 
            otp=msgs[len(msgs)-1].content
            rs=await vnpt.loginByPassword(thread.name)
            if rs:
              for i,msg in enumerate(msgs):
                if i!=0 and 'headers' not in msgs[0].content:
                  await msg.delete()
                else: 
                  await msg.edit(content=rs)
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
                headers=await vietnamobile.login(rs)
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
          print(error,333)
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
                  if i==2 and item['REMAIN']<5000:
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
              '''except Exception as err:
                print(err)
                rs=False'''
        elif any(item.strip() in thread.name for item in VIETNAMOBILE): 
          msgs=[msg async for msg in thread.history(oldest_first=True)]
          if len(msgs)==1 and 'loading' not in msgs[0].content or 'token' in msgs[0].content:
            #try:
            rs=await vietnamobile.getInfo(ast.literal_eval(msgs[0].content))
            if not rs:
              headers=await vietnamobile.login(ast.literal_eval(msgs[0].content))
              if headers:
                try:
                  await msgs[0].edit(content=headers)
                  rs=await vietnamobile.getInfo(headers)
                except:
                  msg=await thread.send('re-active thread')
                  await msg.delete()
            if rs:
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
      except Exception as err:
        print(err,1111)
        pass
@tasks.loop(seconds=3)
async def ping(): 
    print(datetime.now())


@tree.command( 
    name="check_amount_in_phone",
    description="check amount avainable in phone",
    guild=discord.Object(id=GUILDID)
)
async def first_command(interaction):
    await interaction.response.defer()
    msgs = [msg async for msg in interaction.channel.history()]
    hasText = False
    hasImage = False
    notEdit = False
    for i, msg in enumerate(msgs):
        if i == 1 and not msg.author.bot and len(msgs) > 2:
            content = msg.content
            files = []
            temp = []
            for att in msg.attachments:
                if 'text' in att.content_type:
                    content = await att.read()
                    content = content.decode('utf-8')
                    hasText = True
                    with open('content.txt', 'w') as file:
                        file.write(content)
                    files.append(discord.File('content.txt'))
                    temp.append('content.txt')
                    content = ''
                elif 'image' in att.content_type:
                    await att.save(att.filename)
                    files.append(discord.File(att.filename))
                    temp.append(att.filename)
                    hasImage = True
            await msg.delete()
        elif i == len(msgs)-1:
            if 'content' not in locals():
                content = ''
            if 'files' not in locals():
                files = []
            if 'temp' not in locals():
                temp = []
            if len(msgs) == 2 and not msgs[1].author.bot:
                notEdit = True
            if not hasText and len(content.strip()) == 0:
                content = msg.content
                for att in msg.attachments:
                    if 'text' in att.content_type:
                        content = await att.read()
                        content = content.decode('utf-8')
                        with open('content.txt', 'w') as file:
                            file.write(content)
                        files.append(discord.File('content.txt'))
                        temp.append('content.txt')
                        hasText = True
            if not hasImage:
                for att in msg.attachments:
                    if 'image' in att.content_type:
                        await att.save(att.filename)
                        files.append(discord.File(att.filename))
                        temp.append(att.filename)
            if notEdit:
                name = re.search(
                    r'.*Tên sản phẩm: (.*?)\..*', content).group(1)
                name = name.strip()[0:99]
                if hasText:
                    content = ''
                thread = await interaction.channel.parent.create_thread(name=name, content=content, files=files)
                await thread.thread.send('Need update!')
                await interaction.channel.delete()
            else:
                if hasText:
                    content = ''
                await msg.edit(content=content, attachments=files)
            for file in temp:
                if os.path.isfile(file):
                    os.remove(file)
        elif i != 0 and i != len(msgs)-1 and msg.author.bot and not notEdit:
            await msg.delete()
    if not notEdit:
        await interaction.edit_original_response(content='Need update!')
client.run(os.eviron.get('botToken'))
