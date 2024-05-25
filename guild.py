import asyncio


async def getBasic(guild):
    for category in guild.categories:
        if 'viettel' in category.name:
            for channel in category.channels:
                if 'phones' in channel.name:
                  phoneCh = channel
                elif 'raws' in channel.name:
                  rawsCh=channel
    return {'phonesCh': phoneCh,'rawsCh':rawsCh}
