# -*- coding: utf-8 -*-
import os, sys
import re

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import urllib, time
from datetime import datetime, timedelta
from ga import ga

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon').decode("utf-8")
__language__ = __addon__.getLocalizedString
__cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__icon_msg__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'bulsat.png' ) ).decode("utf-8")
__data__ = xbmc.translatePath( os.path.join( __profile__, '', 'data.dat') ).decode("utf-8")
__pls__ = xbmc.translatePath( os.path.join( __profile__, '', 'playlist.m3u') ).decode("utf-8")
sys.path.insert(0, __resource__)

def Notify (msg1, msg2):
  xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (msg1, msg2, '5000', __icon_msg__)).encode('utf-8'))

if __addon__.getSetting("firstrun") == "true":
  Notify('Settings', 'empty')
  __addon__.openSettings()
  __addon__.setSetting("firstrun", "false")

refresh = __addon__.getSetting("refresh")
timeout = __addon__.getSetting("timeout")
base = __addon__.getSetting("base")
offset = int(__addon__.getSetting("offset"))

if __addon__.getSetting("dbg") == 'true':
  dbg = True
else:
  dbg = False

if not __addon__.getSetting("username"):
  Notify('User', 'empty')
if not __addon__.getSetting("password"):
  Notify('Password', 'empty')

def update(name, dat, crash=None):
  payload = {}
  payload['an'] = __scriptname__
  payload['av'] = __version__
  payload['ec'] = name
  payload['ea'] = 'tv_start'
  payload['ev'] = '1'
  payload['dl'] = urllib.quote_plus(dat.encode('utf-8'))
  ga().update(payload, crash)

def timesmk(v):
  ts = v.get('start', None)
  te = v.get('stop', None)
  if ts is None or te is None:
    return u''
  ts = datetime.fromtimestamp(time.mktime(time.strptime(ts.split()[0], '%Y%m%d%H%M%S'))) + timedelta(minutes=offset)
  te = datetime.fromtimestamp(time.mktime(time.strptime(te.split()[0], '%Y%m%d%H%M%S'))) + timedelta(minutes=offset)
  return u'%s %s' % (ts.strftime("%H:%M:%S"), te.strftime("%H:%M:%S"))

def indexch():
  import traceback
  b = None
  try:
    import bsco
    b = bsco.dodat(base = base,
                  login = {'usr': __addon__.getSetting("username"),
                          'pass': __addon__.getSetting("password")
                          },
                  cachepath = __data__,
		  playlist = __pls__,
                  cachetime = refresh,
                  dbg = dbg,
                  timeout=float(timeout))
  except Exception, e:
    Notify('Module Import', 'Fail')
    update('exception', e.args[0], sys.exc_info())
    traceback.print_exc()
    pass

  try:
    i = -1
    c = {}
    if b is not None:
       for i, c in b.data_fetch():
          addch(i, c)
          Notify('Data', 'Fetch Ok')
  except Exception, e:
    if e.args[0] == 'LoginFail':
      Notify('LoginFail', 'Check login data')
    else:
      Notify('Data', 'Fetch Fail')
    update('exception', '%s:%d->%s' % (e.args[0], i, c.get('title', None)), sys.exc_info())
    traceback.print_exc()
    pass

def playch(url, name):
  li = xbmcgui.ListItem(path=url)
  # li.addStreamInfo('video', { 'duration': 3600})
  # li.addStreamInfo('subtitle', { 'language': 'en' })
  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
  update(name, url)

def addch(idx, dat):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(dat['sources']) + "&mode=" + str(1) + "&name=" + urllib.quote_plus(dat['title'].encode('utf-8'))
  liz = xbmcgui.ListItem(dat['title'], iconImage=dat['logo_mobile_selected'], thumbnailImage=dat['logo_mobile'])
  info = u'%s - Ch: %d' % (timesmk(dat), idx)
  for c in ('program', 'desc', 'channel', 'pg'):
    d = dat.get(c, ' ')
    if d is not None:
      info += ' ' + d

  liz.setInfo(type="video", infoLabels={"Title": dat['title'], "plot": ' '.join(info.split())})
  liz.setInfo('video', { 'title': name})
  liz.setProperty('fanart_image', dat['logo_epg'])
  liz.setProperty("IsPlayable" , "true")
  return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)

def setviewmode():
  if (xbmc.getSkinDir() != "skin.confluence") or __addon__.getSetting("viewset") != 'true':
    return
  mode = {
            '0': '52',
            '1': '502',
            '2': '51',
            '3': '500',
            '4': '501',
            '5': '508',
            '6': '504',
            '7': '503',
            '8': '515'
          }
  xbmc.executebuiltin('Container.SetViewMode(%s)' % mode[__addon__.getSetting("viewmode")])

def get_params():
  param = []
  paramstring = sys.argv[2]
  if len(paramstring) >= 2:
    params = sys.argv[2]
    cleanedparams = params.replace('?', '')
    if (params[len(params) - 1] == '/'):
      params = params[0:len(params) - 2]
    pairsofparams = cleanedparams.split('&')
    param = {}
    for i in range(len(pairsofparams)):
      splitparams = {}
      splitparams = pairsofparams[i].split('=')
      if (len(splitparams)) == 2:
        param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
url = None
name = None
mode = None

try:
  url = urllib.unquote_plus(params["url"])
except:
  pass
try:
  name = urllib.unquote_plus(params["name"])
except:
  pass
try:
  mode = int(params["mode"])
except:
  pass

if mode == None or url == None or len(url) < 1:
  indexch()
elif mode == 1:
  playch(url, name)

xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
setviewmode()
