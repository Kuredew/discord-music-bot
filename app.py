'''KUREICHI DEV SINCE 2024'''

import os
import base64
from playlist_collection import PlaylistCollection
import yt_dlp
from youtube_search import YoutubeSearch
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents=intents)

def loads():
    global voice_client, music_url_object, playing, cookie, BOT_TOKEN, loop_index, loop_music_url_object, is_loop

    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    COOKIE_BASE64 = os.environ.get('cookie')

    cookie_ascii = COOKIE_BASE64.encode('ascii')
    cookie_base64_decoded = base64.b64decode(cookie_ascii)
    cookie_string = cookie_base64_decoded.decode('ascii')

    with open('cookies.txt', 'w') as f:
        f.write(cookie_string)
        
    cookie = 'cookies.txt'

    voice_client = {}
    music_url_object = {}
    playing = False

    is_loop = False
    loop_index = 0
    loop_music_url_object = {}


async def ytdlp(query):
    print(f'Mencari Musik {query}...')

    ydl_opts = {
        'cookiefile': cookie,
        'format': 'ba/best',
        'default_search': 'ytsearch5',
        'noplaylist': True,
        'skip_download': True,
        'extract_flat': 'discard_in_playlist',
        'ignoreerrors': True,
        'max_downloads': 5
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
    def __init__(self, ctx, message, guild_id, results):
        super().__init__()
        self.ctx = ctx
        self.message = message
        self.result = results
        self.guild_id = guild_id
        self.options = []
        for index, result in enumerate(self.result):
            query = discord.SelectOption(label=result['title'], value=str(index), description=result['channel'])
            self.options.append(query)


        self.select = discord.ui.Select(placeholder='Pilih Lagu', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.interactions):
        index_selected = int(self.select.values[0])
        result_selected = self.result[index_selected]

        title = result_selected['title']
        url = 'https://www.youtube.com' + result_selected['url_suffix']
        # url = result_selected['url']

        await interaction.response.edit_message(content=f'🧿 **Memproses** {title}', view=None)

        ytdlp_result = await ytdlp(url)
        stream_url = ytdlp_result['data']

        await initialize_play_music(self.ctx, self.message, self.guild_id, title, stream_url)

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
        
class PlaylistSelect(discord.ui.View):
    def __init__(self, execute, username, title_song, url):
        super().__init__()
        self.title_song = title_song
        self.url = url

        self.execute = execute
        
        self.playlist_collection = PlaylistCollection(username)
        playlists = self.playlist_collection.ListPlaylist()

        options = []

        for index, playlist in enumerate(playlists):
            query = discord.SelectOption(label=playlist['playlist_name'], value=playlist['playlist_name'])
            options.append(query)

        self.select = discord.ui.Select(placeholder='Pilih Playlist', options=options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        playlist_name = self.select.values[0]

        if self.execute == 'add':
            self.playlist_collection.AddMusic(playlist_name=playlist_name, title=self.title_song, url=self.url)
        if self.execute == 'delete':
            self.playlist_collection.DeleteMusic(playlist_name=playlist_name, title=self.title_song, url=self.url)
            
        
        await interaction.response.edit_message(content=f'📝 **{self.title_song}** berhasil dimasukkan ke {playlist_name}', view=None)

class MusicSelectRaw(discord.ui.View):
    def __init__(self, username, query):
        super().__init__()

        self.username = username
        self.results = YoutubeSearch(query, 5).to_dict()

        options = []
        for index, result in enumerate(self.results):
            options.append(discord.SelectOption(label=f'{index + 1}. {result['title']}', description=result['channel'], value=str(index)))

        self.select = discord.ui.Select(placeholder='Pilih Musiknya bang', options=options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        index_selected = int(self.select.values[0])
        result_selected = self.results[index_selected]

        view = PlaylistSelect('add', self.username, result_selected['title'], f'https://www.youtube.com{result_selected['url_suffix']}')

        await interaction.response.edit_message(content='Pilih Playlistnya bang', view=view)


class PlaylistSelectForMusicSelectFromPlaylist(discord.ui.View):
    def __init__(self, username):
        super().__init__()

        self.username = username

        self.playlist_collections = PlaylistCollection(username)
        self.playlists = self.playlist_collections.ListPlaylist()

        self.options = []
        for index, playlist in enumerate(self.playlists):
            self.options.append(discord.SelectOption(label=playlist['playlist_name'], value=index))

        self.select = discord.ui.Select(placeholder='Pilih Playlist', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interact: discord.Interaction):
        playlist_name = self.playlists[int(self.select.values[0])]['playlist_name']

        view = MusicSelectFromPlaylist(self.username, playlist_name)

        await interact.response.edit_message(content='Pilih lagunya bang.', view=view)



class MusicSelectFromPlaylist(discord.ui.View):
    def __init__(self, username, playlist_name):
        super().__init__()

        self.playlist_name = playlist_name
        self.playlist_collections = PlaylistCollection(username)
        self.list_music = self.playlist_collections.ListMusic(playlist_name)

        self.options = []
        for index, music in enumerate(self.list_music):
            self.options.append(discord.SelectOption(label=str(index + 1) + '. ' + music['title'], value=index))

        self.select = discord.ui.Select(placeholder='Pilih lagu yang ingin dihapus dari playlist', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        music_selected = self.list_music[int(self.select.values[0])]
        title = music_selected['title']
        url = music_selected['url']

        self.playlist_collections.DeleteMusic(self.playlist_name, title, url)

        await interaction.response.edit_message(content=f'Music **{title}** Berhasil dihapus dari **{self.playlist_name}**', view=None)

class PlaylistRemoveSelect(discord.ui.View):
    def __init__(self, username):
        super().__init__()

        self.username = username
        self.playlist_collections = PlaylistCollection(username)
        self.playlist_list = self.playlist_collections.ListPlaylist()

        self.options = []

        for index, playlist in enumerate(self.playlist_list):
            query = discord.SelectOption(label=playlist['playlist_name'], value=str(index))

            self.options.append(query)

        self.select = discord.ui.Select(placeholder='Pilih Playlist', options=self.options)
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        self.playlist_name = self.playlist_list[int(self.select.values[0])]['playlist_name']

        self.playlist_collections.DeletePlaylist(self.playlist_name)
        await interaction.response.edit_message(content=f'{self.playlist_name} Berhasil di remove dari database', view=None)

class PlaylistSelectPlay(discord.ui.View):
    def __init__(self, ctx, guild_id, username):
        super().__init__()

        self.ctx = ctx
        self.guild_id = guild_id
        self.username = username
        self.options = []

        playlist_collection = PlaylistCollection(self.username)
        self.playlist_list = playlist_collection.ListPlaylist()

        for index, playlist in enumerate(self.playlist_list):
            music_query = ''
            if len(playlist['music']) > 1:
                for index, music in enumerate(playlist['music']):
                    music_query += f'{music['title']}'
                    if index+1 < len(playlist['music']):
                        music_query =+ ', '
            else:
                music_query = playlist['music'][0]['title']

            q = discord.SelectOption(label=playlist['playlist_name'], description=music_query, value=str(index))

        self.select = discord.ui.Select(placeholder='Pilh Playlist')
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interact: discord.Interaction):
        playlist_collections = PlaylistCollection(self.username)

        playlist_name = self.playlist_list[int(self.select.values[0])]['playlist_name']
        music_list = playlist_collections.ListMusic(playlist_name)

        message = await interact.response.send_message(content='🧿 Memproses..\n\n*Karena minimnya resource, ini bakalan memakan waktu sedikit lama. Namun tenang saja, lagu akan tetap dijalankan sambil menunggu proses selesai.*')

        for music in music_list:
            title = music['title']
            url = music['url']

            print(f'Memasukkan URL {title} Kedalam playlist utama')

            result = await ytdlp(url)
            title = result['title']
            url_stream = result['data']

            await initialize_play_music(self.ctx, message, self.guild_id, title, url_stream)

        




async def initialize_play_music(ctx, message, guild_id, title, url):
    global playing
    print('Menginisialisasi Play Music')

    obj = {
        'title': title,
        'url': url
    }

    if guild_id not in music_url_object:
        music_url_object[guild_id] = []
        loop_music_url_object[guild_id] = []

        print('playlist tidak ada, menulis playlist baru.')

    music_url_object[guild_id].append(obj)
    loop_music_url_object[guild_id].append(obj)

    if not playing:
        await message.delete()
        await play_music(ctx, guild_id)
        playing = True
    else:
        await message.edit(content=f'📝 **{title}** ditambah kedalam Playlist.', view=None)


async def play_music(ctx, guild_id):
    global loop_index

    print('Fungsi Play Music dijalankan')

    if not is_loop:
        if len(music_url_object[guild_id]) > 0:
            obj = music_url_object[guild_id].pop(0)
        else:
            global playing

            await ctx.send('Lagu Habis.')
            music_url_object.pop(guild_id)

            loop_index = 0
            playing = False
            return
    else:
        print('Loop Dijalankan')
        try:
            obj = loop_music_url_object[guild_id][loop_index]
        except:
            loop_index = 0
            obj = loop_music_url_object[guild_id][loop_index]

    title = obj['title']
    url = obj['url']

    await ctx.send(f'🎶 **Memutar** {title}')
    voice_client[guild_id].play(discord.FFmpegOpusAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_music(ctx, guild_id), client.loop))
    loop_index += 1

    print('Function Play Music Selesai!')

async def main():
    async with client:
        @client.event
        async def on_ready():
            print('Bot Connected!')
            assets = {
                'large_image': 'large_image2',
                'large_text': 'Sherlock tak parani',
                'small_image': '',
                'small_text': 'Ngapa?'
            }

            playing_vs_code = discord.Game(name='Only Fans', platform='PS5', assets=assets)
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
                result = await ytdlp(q)

                await initialize_play_music(ctx, message, ctx.guild.id, result['title'], result['data'])
            else:
                message = await ctx.send('🧿 Mencari...')

                search_query = q
                result_search = YoutubeSearch(search_query, max_results=5).to_dict()

                view = MusicSelect(ctx, message, ctx.guild.id, result_search)

                await message.edit(content='✨ Pilih lagunya bang.', view=view)

                '''query = q.replace(' ', '+')
                url = f'https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%253D%253D'
                result = await search_youtube(ctx, url, voice_client[ctx.guild.id], ctx.guild.id)'''


        @client.command()
        async def loop(ctx):
            global is_loop

            if not is_loop:
                is_loop = True

                await ctx.send('Loop Berhasil di Aktifkan!')
            else:
                is_loop = False

                await ctx.send('Loop Berhasil di Nonaktifkan')
                

        @client.command()
        async def start_debug(ctx):
            await ctx.send('Memulai Debug...')
            await ctx.send('Mengirim query ke variable p')
            await p(ctx, 'escapism')
            await ctx.send('Debug Selesai.')

            

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
            global playing

            if not ctx.author.voice:
                await ctx.send('Tidak bisa memberhentikan musik jika kamu berada diluar voice.')
                return
            
            message = await ctx.send('Memberhentikan Musik')
            music_url_object.pop(ctx.guild.id)
            loop_music_url_object.pop(ctx.guild.id)
            playing = False

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

        @client.command()
        async def playlistmake(ctx, *, q):
            playlist_name = q
            username = ctx.author.name

            playlist_collection = PlaylistCollection(username)
            check_user = playlist_collection.CheckUser()

            if not check_user:
                await ctx.send('Kamu belum menambahkan playlist sebelumnya, menginisalisasi database baru...')
                playlist_collection.AddUser()
            
            playlist_collection.AddPlaylist(playlist_name)
            await ctx.send(f'Playlist dengan nama **{playlist_name}** berhasil ditambahkan ke Database')

        @client.command()
        async def playlistadd(ctx, *, q):
            message = await ctx.send('🧿 Memproses.')
            music_name = q
            username = ctx.author.name

            if q[:5] == 'https':
                result = await ytdlp(q)
                title = result['title']

                view = PlaylistSelect('add', username, title, q)

                await message.edit(content='Pilih playlist', view=view)
            else:
                view = MusicSelectRaw(username, q)

                await message.edit(content='Pilih lagunya', view=view)

        @client.command()
        async def playlistdelete(ctx):
            playlist_collections = PlaylistCollection(ctx.author.name)
            check_user = playlist_collections.CheckUser()
            
            if not check_user:
                await ctx.send('Kamu belum mempunyai playlist sama sekali.')
                return
            
            view = PlaylistSelectForMusicSelectFromPlaylist(ctx.author.name)
            await ctx.send(content='Pilih Playlist', view=view)

        @client.command()
        async def playlistremove(ctx):
            username = ctx.author.name
            view = PlaylistRemoveSelect(username)

            await ctx.send(content='Pilih playlist yang ingin kamu remove\n\n*Playlist yang sudah dihapus tidak akan bisa dikembalikan lagi!*', view=view)
            
        @client.command()
        async def playlistplay(ctx):

            username = ctx.author.name
            guild_id = ctx.guild.id

            if ctx.author.voice:
                if ctx.voice_client == None:
                    voice_client[guild_id] = ctx.author.voice.channel.connect()
            else:
                await ctx.send(content='Masuk voice dulu bang, gw gk tau mau join ke mana.')
                return
            
            view = PlaylistSelectPlay(ctx, guild_id, username)
            message = await ctx.send(content='📖 Pilih Playlist yang ingin kamu putar', view=view)


        @client.command()
        async def playlist(ctx):
            guild_id = ctx.guild.id
            username = ctx.author.name

            playlist_collections = PlaylistCollection(username)
            if not playlist_collections.CheckUser():
                await ctx.send('Kamu belum membuat playlist, silahkan buat playlist dengan mengetik command **.playlistmake (nama playlist yang kamu inginkan)**')

            message_query = '📕 Playlist kamu yang tersimpan di database kami.\n\n'
            playlist_list = playlist_collections.ListPlaylist()
            for index, playlist in enumerate(playlist_list):
                playlist_name = playlist['playlist_name']
                music_query = ''
                for music in playlist['music']:
                    music_query += f'   {music['title']}\n'

                query = f'{index+1}. {playlist_name}\n{music_query}'
                message_query += query

            await ctx.send(message_query)


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