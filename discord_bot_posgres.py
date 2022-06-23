# bot.py
import os
import sys

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from time import sleep
from datetime import datetime, time
import random
import handler
import requests

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
DATABASE_URL = os.getenv('DATABASE_URL')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

import psycopg2
conn = psycopg2.connect(DATABASE_URL)

@bot.command(name='hello', help='Says hello')
async def hello(ctx):
    user = ctx.author
    await ctx.send(f'Hello {user.mention}')

@bot.command(name='daily', help='Check in after completing daily challenge')
async def check_in(ctx):
    user = ctx.author
    consecutive, total, err = handler.check_in(conn, user.name)
    if err == 'checked_in':
        if consecutive > 1:
            response = f'安安 {user.mention}, 今天是你連續第{consecutive}天完成簽到, 總共簽到了{total}天, 請繼續保持✅ ✅ ✅ '
        elif total > 1:
            response = f'安安 {user.mention}, 好久不見, 你總共簽到過了{total}天, 請繼續保持✅ ✅ ✅ '
        else:
            response = f'安安 {user.mention}, 歡迎你加入刷題大家庭的行列, 請繼續保持✅ ✅ ✅ '
    elif err == 'duplicate_error':
        response = f'安安 {user.mention}, 今天簽到過了ㄛ～～'
    elif err == 'db_error':
        response = '哭啊資料庫壞了QQ'
    else:
        response = f'哭啊不知道啥東西壞了'
    await ctx.send(response)

@bot.command(name='subscribe', help='Subscribe to reminder and condemnation for daily challenge')
async def subscribe(ctx, remind_time, condemn_time):
    user = ctx.author

    err = handler.subscribe(conn, user.name, remind_time, condemn_time)
    if err == 'subscribed':
        response = f'安安 {user.mention}, 成功設定每天{remind_time}點提醒, {condemn_time}點譴責～～'
    elif err == 'db_error':
        response = '哭啊資料庫壞了QQ'
    else:
        response = f'哭啊不知道啥東西壞了'
    
    await ctx.send(response)

@bot.command(name='unsubscribe', help='Unsubscribe from reminder and condemnation for daily challenge')
async def unsubscribe(ctx):
    user = ctx.author

    err = handler.unsubscribe(conn, user.name)
    if err == 'unsubscribed':
        response = f'嗚嗚 {user.mention}, 別走嘛'
    elif err == 'db_error':
        response = '哭啊資料庫壞了QQ'
    else:
        response = f'哭啊不知道啥東西壞了'
    
    await ctx.send(response)

@bot.command(name='doggo', help='Get a random cute doggo picture')
async def doggo(ctx, breed=None, sub_breed=None,):
    if not breed:
        url = 'https://dog.ceo/api/breeds/image/random'
    else:
        breed_arr = [breed]
        if sub_breed is not None:
            breed_arr.append(sub_breed)
        url = f'https://dog.ceo/api/breed/{"/".join(breed_arr)}/images/random'
    resp = requests.get(url).json()
    if resp.get('status') == 'success':
        embed = discord.Embed()
        embed.set_image(url=resp.get('message'))
        embed.description = '刷題累了，來張可愛ㄉ狗勾吧'
        await ctx.send(embed = embed)

@tasks.loop(minutes=1)
async def remind():
    if datetime.now().minute >= 1:
        return
    channel = bot.get_channel(CHANNEL_ID)
    remind_list, err = handler.get_remind_list(conn, 'remind')
    remind_users = []
    for name in remind_list:
        user = discord.utils.get(channel.members, name=name)
        if user is not None:
            remind_users.append(user.mention)
    
    good_words = [
        '通往光明的道路是平坦的，為了成功，為了奮鬥的渴望，我們不得不努力。',
        '沒有人會關心你付出過多少努力，撐得累不累，摔的痛不痛，他們只會看你最後站在什麼位置，然後羨慕嫉妒恨',
        '每個人都有屬於自己的舞臺，這個舞臺，是那麼光燦，美麗，生命從此輝煌無悔!只要堅韌不拔的走下去！',
        '今天做別人不願做的事，明天就能做別人做不到的事。',
        '沒有一種夢想，是可以不需要努力，而能以實現的；沒有一樁事業，是可以不經歷風雨，而輕鬆成功的；相信我，付出必有收穫。',
        '勝利貴在堅持，要取得勝利就要堅持不懈地努力',
        '贏家不是那些從不失敗的人，而是那些從不放棄的人。'
    ]

    if remind_users:
        remind_users = ' '.join(remind_users)
        msg = f'安安 {remind_users} 記得寫題目歐歐～～\n{random.choice(good_words)}'
        await channel.send(msg)

    words = [
        '還敢混！！',
        '我對你很失望',
        '..................',
        '混爽沒？',
        '譴責！！！',
        '努力不一定成功，但放棄一定很輕鬆',
        '你不丟臉我都為你感到丟臉了',
        '= =',
        '一定要人罵就是了'
    ]
    condemn_list, err = handler.get_remind_list(conn, 'condemn')
    condemn_users = []
    for name in condemn_list:
        user = discord.utils.get(channel.members, name=name)
        if user is not None:
            condemn_users.append(user.mention)
    if condemn_users:
        condemn_users = ' '.join(condemn_users)
        msg2 = f'{condemn_users} {random.choice(words)}'

        await channel.send(msg2)

@remind.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

@bot.event
async def on_command_error(ctx, error):
    print('err', error, flush=True)
    if isinstance(error, commands.errors.CommandNotFound ):
        await ctx.send(f'安安, 還沒有這個commandㄛ,非常歡迎各位參與開發自己想要的功能～')
    
    else:
        await ctx.send('哭啊！不知道出了啥問題, 正在重啟... 請稍候再試試看')
        os.execv(sys.executable, ['python3'] + sys.argv)

print('init!')
remind.start()
bot.run(TOKEN)