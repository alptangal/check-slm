import asyncio


async def getBasic(guild):
  try:
    for category in guild.categories:
        if 'viettel' in category.name:
            for channel in category.channels:
                if 'phones' in channel.name:
                  phoneCh = channel
                elif 'raws' in channel.name:
                  rawsCh=channel
                elif 'live_count' in channel.name:
                  countCh=channel
        elif 'bots' in category.name.lower():
            botsCh=category
            for channel in category.channels:
                if 'status' in channel.name.lower():
                    statusBotCh=channel
    return {'phonesCh': phoneCh,'rawsCh':rawsCh,'countCh':countCh,'statusBotCh':(statusBotCh if 'statusBotCh' in locals() else None),'botsCategory':(botsCh if 'botsCh' in locals() else None)}
  except Exception as error:
    print(error,'guild.py')
    pass