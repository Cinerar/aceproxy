'''
Playlist Generator
This module can generate .m3u playlists with tv guide
and groups
'''
import re
import urllib2
from plugins.config.playlist import PlaylistConfig as config

class PlaylistGenerator(object):

    def __init__(self,
                 m3uemptyheader=config.m3uemptyheader,
                 m3uheader=config.m3uheader,
                 m3uchanneltemplate=config.m3uchanneltemplate,
                 changeItem=config.changeItem,
                 comparator=config.compareItems if config.sort else None):
        self.itemlist = list()
        self.m3uemptyheader = m3uemptyheader
        self.m3uheader = m3uheader
        self.m3uchanneltemplate = m3uchanneltemplate
        self.changeItem = changeItem
        self.comparator = comparator

    def addItem(self, itemdict):
        '''
        Adds item to the list
        itemdict is a dictionary with the following fields:
            name - item name
            url - item URL
            tvg - item tvg name (optional)
            tvgid - item tvg id (optional)
            group - item playlist group (optional)
            logo - item logo file name (optional)
        '''
        self.itemlist.append(itemdict)

    def _generatem3uline(self, item):
        '''
        Generates EXTINF line with url
        '''
        return self.m3uchanneltemplate % item

    def _changeItems(self):
        for item in self.itemlist:
            self.changeItem(item)
            if not item.has_key('tvg'):
                item['tvg'] = item.get('name').replace(' ', '_')
            if not item.has_key('tvgid'):
                item['tvgid'] = ''
            if not item.has_key('group'):
                item['group'] = ''
            if not item.has_key('logo'):
                item['logo'] = ''

    def exportm3u(self, hostport, path='', add_ts=False, empty_header=False, archive=False, process_url=True, header=None, fmt=None):
        '''
        Exports m3u playlist
        '''
        
        if add_ts:
            # Adding ts:// after http:// for some players
            hostport = 'ts://' + hostport
            
        if header is None:
            if not empty_header:
                itemlist = self.m3uheader
            else:
                itemlist = self.m3uemptyheader
        else:
            itemlist = header

        self._changeItems()
        if self.comparator:
            items = sorted(self.itemlist, cmp=self.comparator)
        else:
            items=self.itemlist
        
        for i in items:
            item = i.copy()
            item['name'] = item['name'].replace('"', "'").replace(',', '.')
            url = item['url'];

            if process_url:
                # For .acelive and .torrent
                item['url'] = re.sub('^(http.+)$', lambda match: 'http://' + hostport + path + '/torrent/' + \
                                 urllib2.quote(match.group(0), '') + '/stream.mp4', url,
                                       flags=re.MULTILINE)
                if url == item['url']:  # For PIDs
                    item['url'] = re.sub('^(acestream://)?(?P<pid>[0-9a-f]{40})$', 'http://' + hostport + path + '/pid/\\g<pid>/stream.mp4',
                                        url, flags=re.MULTILINE)
                if archive and url == item['url']:  # For archive channel id's
                    item['url'] = re.sub('^([0-9]+)$', lambda match: 'http://' + hostport + path + '/archive/play?id=' + match.group(0),
                                        url, flags=re.MULTILINE)
                if not archive and url == item['url']:  # For channel id's
                    item['url'] = re.sub('^([0-9]+)$', lambda match: 'http://' + hostport + path + '/channels/play?id=' + match.group(0),
                                            url, flags=re.MULTILINE)
                if url == item['url']:  # For channel names
                    item['url'] = re.sub('^([^/]+)$', lambda match: 'http://' + hostport + path + '/' + match.group(0) + '/stream.mp4',
                                            url, flags=re.MULTILINE)
            
            if fmt:
                if '?' in item['url']:
                    item['url'] = item['url'] + '&fmt=' + fmt
                else:
                    item['url'] = item['url'] + '/?fmt=' + fmt

            itemlist += self._generatem3uline(item)

        return itemlist
