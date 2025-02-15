from pymongo import MongoClient
import os

CONNECTION_STRING = os.environ.get('MONGODB_CONNECTION_STRING')

mongoClient = MongoClient(CONNECTION_STRING)
db = mongoClient['kureichi_music']
collection = db['playlist']


class PlaylistCollection:
    def __init__(self, username):
        self.id = 232148
        self.username = username
        playlistCollection = collection.find_one({'id': self.id})
        if playlistCollection:
            self.playlistCollection = playlistCollection
        else:
            query = {
                'id': self.id,
                'playlist': {}
            }

            insert = collection.insert_one(query)
            print(insert)

            self.playlistCollection = query

    def UpdatePlaylistCollection(self):
        update = collection.update_one({'id': self.id}, {'$set': self.playlistCollection})
        print(update)

    '''CRUD AccountUser'''

    def CheckUser(self):
        return False if self.username not in self.playlistCollection['playlist'] else True
    def AddUser(self):
        self.playlistCollection['playlist'][self.username] = []
        self.UpdatePlaylistCollection()
    
    '''CRUD Playlist'''

    def CheckPlaylist(self, playlist_name):
        list_playlist = []

        for playlist in self.playlistCollection['playlist'][self.username]:
            print(playlist)
            list_playlist.append(playlist['playlist_name'])

        return False if playlist_name not in list_playlist else True
    
    def ListPlaylist(self):
        return self.playlistCollection['playlist'][self.username]
    
    def AddPlaylist(self, playlist_name):
        lists = self.ListPlaylist()
        lists.append({'playlist_name': playlist_name, 'music': []})

        self.playlistCollection['playlist'][self.username] = lists

        self.UpdatePlaylistCollection()

    def DeletePlaylist(self, playlist_name):
        for index, playlist in enumerate(self.playlistCollection['playlist'][self.username]):
            print(playlist)
            if playlist['playlist_name'] == playlist_name:
                self.playlistCollection['playlist'][self.username].pop(index)

        self.UpdatePlaylistCollection()



    '''CRUD Music'''

    def ListMusic(self, playlist_name):
        for index, playlist in enumerate(self.ListPlaylist()):
            if playlist['playlist_name'] == playlist_name:
                return self.playlistCollection['playlist'][self.username][index]['music']
        return False

    def AddMusic(self, playlist_name, title, url):
        query = {'title': title, 'url': url}
        for index, playlist in enumerate(self.ListPlaylist()):
            if playlist['playlist_name'] == playlist_name:
                self.playlistCollection['playlist'][self.username][index]['music'].append(query)
        #self.playlistCollection['playlist'][playlist_name].append(query)

        self.UpdatePlaylistCollection()

    def DeleteMusic(self, playlist_name, title, url):
        query = {'title': title, 'url': url}
        for index, playlist in enumerate(self.ListPlaylist()):
            if playlist['playlist_name'] == playlist_name:
                for index2, music in enumerate(playlist['music']):
                    if music['title'] == title:
                        self.playlistCollection['playlist'][self.username][index]['music'].pop(index2)
                        break

        self.UpdatePlaylistCollection()
