'''KUREICHI DEV SINCE 2024'''

import os
import base64
import yt_dlp
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents=intents)

def loads():
    global voice_client, music_url_object, playing, cookie, BOT_TOKEN

    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    COOKIE_BASE64 = os.environ.get('cookie')

    cookie_ascii = COOKIE_BASE64.encode('ascii')
    cookie_base64_decoded = base64.b64decode(cookie_ascii)
    cookie_string = cookie_base64_decoded.decode('ascii')

    with open('cookie.txt', 'w') as f:
        f.write(cookie_string)

    cookie = 'cookie.txt'

    voice_client = {}
    music_url_object = {}
    playing = False


async def search_youtube(ctx, query, voice_client, guild_id):
    print(f'Mencari Musik {query}...')

    ydl_opts = {
        'cookiefile': cookie,
        'format': 'ba/best',
        'default_search': 'ytsearch5',
        'noplaylist': True,
        'skip_download': True,
        'extract_flat': 'discard_in_playlist',
        'ignoreerrors': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        print('selesai')

    if 'entries' in info:
        return {'type': 'entries', 'data': info['entries']}
    else:
        print(info['url'])
        #await initialize_play_music(ctx, voice_client, guild_id, info['title'], info['url'])
        print('Mendapatkan Link bukan Search')
        return {'type': 'url', 'title': info['title'], 'data': info['url']}
    

class MusicSelect(discord.ui.View):
    def __init__(self, ctx, message, voice_client, guild_id, results):
        super().__init__()
        self.ctx = ctx
        self.message = message
        self.voice_client = voice_client
        self.result = results
        self.guild_id = guild_id
        self.options = []
        for index, result in enumerate(self.result):
            query = discord.SelectOption(label=result['title'], value=str(index), description=result['uploader'])
            self.options.append(query)


        self.select = discord.ui.Select(placeholder='Pilih Lagu', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.interactions):
        index_selected = int(self.select.values[0])
        result_selected = self.result[index_selected]

        title = result_selected['title']
        url = result_selected['url']

        await initialize_play_music(self.ctx, self.message, self.voice_client, self.guild_id, title, url)

class DeleteSelect(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__()

        self.guild_id = guild_id
        self.options = []

        for index, obj in enumerate(music_url_object[guild_id]):
            self.options.append(discord.SelectOption(label=f'{index + 1}. {obj['title']}', value=str(index)))
        
        self.select = discord.ui.Select(placeholder='Pilih Lagu yang ingin dihapus.', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        print('On Select Terpanggil')

        selected_index = int(self.select.values[0])
        music_selected = music_url_object[self.guild_id].pop(selected_index)

        title = music_selected['title']
        url = music_selected['url']
        
        await interaction.response.edit_message(content=f'🚮 {title} Dihapus dari playlist', view=None)
        



async def initialize_play_music(ctx, message, voice_client, guild_id, title, url):
    global playing
    print('Menginisialisasi Play Music')

    obj = {
        'title': title,
        'url': url
    }

    if guild_id not in music_url_object:
        music_url_object[guild_id] = []

        print('playlist tidak ada, menulis playlist baru.')

    music_url_object[guild_id].append(obj)

    if not playing:
        await message.delete()
        await play_music(ctx, voice_client, guild_id)
        playing = True
    else:
        await message.edit(content=f'📝 **{title}** ditambah kedalam Playlist.', view=None)


async def play_music(ctx, voice_client, guild_id):
    print('Fungsi Play Music dijalankan')

    if len(music_url_object[guild_id]) > 0:
        obj = music_url_object[guild_id].pop(0)

        title = obj['title']
        url = obj['url']

        await ctx.send(f'🎶 **Memutar** {title}')
        voice_client[guild_id].play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_music(ctx, voice_client, guild_id), client.loop))
    else:
        global playing

        await ctx.send('Lagu Habis.')
        music_url_object.pop(guild_id)
        playing = False


async def main():
    async with client:
        @client.event
        async def on_ready():
            print('Bot Connected!')
            playing_vs_code = discord.Game(name='VS Code')
            await client.change_presence(activity=playing_vs_code)

        @client.command()
        async def p(ctx, *, q):
            if ctx.author.voice:
                if ctx.voice_client == None:
                    voice_client[ctx.guild.id] = await ctx.author.voice.channel.connect()
            else:
                await ctx.send('Masuk Voice dulu bang.')
                return

            if q[:5] == 'https':
                message = await ctx.send('🧿 Memproses Link...')
            else:
                message = await ctx.send('🧿 Mencari...')

            result = await search_youtube(ctx, q, voice_client[ctx.guild.id], ctx.guild.id)

            if result['type'] == 'entries':
                view = MusicSelect(ctx, message, voice_client[ctx.guild.id], ctx.guild.id, result['data'])
                await message.edit(content='Pilih lagunya.', view=view)

            if result['type'] == 'url':
                print('Ini terpanggil')
                await initialize_play_music(ctx, message, voice_client, ctx.guild.id, result['title'], result['data'])
            

        @client.command()
        async def list(ctx):
            try:
                if len(music_url_object[ctx.guild.id]) > 0:
                    message = 'List Playlist setelah ini.\n\n'
                    for index, obj in enumerate(music_url_object[ctx.guild.id]):
                        query = f'{index+1}. {obj['title']}\n'
                        message += query

                    await ctx.send(message)
                else:
                    await ctx.send('Tidak ada lagu lagi setelah ini.')
            except:
                await ctx.send('Aku lagi gk muter musik saat ini.')

        @client.command()
        async def hapus(ctx):
            if not ctx.author.voice:
                await ctx.send('Harap masuk ke voice dulu.')
                return
            
            if len(music_url_object[ctx.guild.id]) > 0:
                view = DeleteSelect(ctx.guild.id)
                await ctx.send('Pilih musik dibawah ini', view=view)
            else:
                await ctx.send('Tidak ada lagu lagi setelah ini')

        @client.command()
        async def stop(ctx):
            if not ctx.author.voice:
                await ctx.send('Tidak bisa memberhentikan musik jika kamu berada diluar voice.')
                return
            
            message = await ctx.send('Memberhentikan Musik')
            await voice_client[ctx.guild.id].disconnect()

        @client.command()
        async def skip(ctx):
            if not ctx.author.voice:
                await message.reply('Tidak bisa menskip musik jika kamu berada diluar voice.')

            message = await ctx.send('Menskip Musik')
            await voice_client[ctx.guild.id].stop()

        @client.command()
        async def j(ctx, *, q):
            voice_client = await ctx.author.voice.channel.connect()

            await initialize_play_music(ctx, voice_client, ctx.guild.id, 'Again', 'https://cf-hls-opus-media.sndcdn.com/playlist/b06e1466-a101-45cd-abf5-f6176677e6ed.64.opus/playlist.m3u8?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiKjovL2NmLWhscy1vcHVzLW1lZGlhLnNuZGNkbi5jb20vcGxheWxpc3QvYjA2ZTE0NjYtYTEwMS00NWNkLWFiZjUtZjYxNzY2NzdlNmVkLjY0Lm9wdXMvcGxheWxpc3QubTN1OCoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3MzkyODAwODh9fX1dfQ__&Signature=S8y2DiHHrzROu8akUiwTVfSsky-19VCVXxsBGsaBqfqHeWp0cl6RynQenHtgILXE7ERrPt8vR7bPQ3dIRGpyJORo9JlAAD1BhTvxNXZob3R-7gTNBuPhMtEHRj3hvpmoOCxAhH5TP528ahWusMgTqswoOKukfhqr0wWV~KLVbnM~BVcyKKQnWfAz2HwfIvxHhbPVM3Vqk25an5GCa67tGLnTXFF3GIZ~qjnOL67taxYZQNT8c8IrrppTUrTzWSekSPy-B0iCaxUNbOM0Trbjk76jLQYMBkOZ0fkvxmT9mcTKLtzjSeRjHsRoAaEl8uu5FG5Dp9Bxgb2Bz7DzviGoHA__&Key-Pair-Id=APKAI6TU7MMXM5DG6EPQ')

            await ctx.send('test')



        '''START MAIN PROGRAM'''
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(console_handler)

        '''handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        discord.utils.setup_logging(level=logging.INFO, handler=handler, root=False)'''

        await client.start(BOT_TOKEN)

        
if __name__ == '__main__':
    # Loads Global Variables
    loads()

    # Run Main Program
    asyncio.run(main())
