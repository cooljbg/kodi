# -*- coding: utf8 -*-

import os, json, time
import base64
from requests import Session, codes
import io
from time import localtime, strftime
import aes as EN

class dodat():
  def __init__(self,
                base,
                login,
                cachepath,
		playlist,
                cachetime=1,
                dbg=False,
                dump_name='',
                timeout=0.5):
    self.__UA = {
                'Host': 'api.iptv.bulsat.com',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://test.iptv.bulsat.com/iptv.php',
                'Origin': 'https://test.iptv.bulsat.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                }

    self.__log_in = {}
    self.__p_data = {
                'user' : ['',''],
                'device_id' : ['','pcweb'],
                'device_name' : ['','pcweb'],
                'os_version' : ['','pcweb'],
                'os_type' : ['','pcweb'],
                'app_version' : ['','0.01'],
                'pass' : ['',''],
                }
    self.__channelsid = {'101':'93.dnevnik.bg','102':'116.dnevnik.bg','103':'99.dnevnik.bg','104':'222.dnevnik.bg','105':'223.dnevnik.bg','106':'97.dnevnik.bg',
'107':'91.dnevnik.bg','109':'188.dnevnik.bg','110':'81.dnevnik.bg','111':'280.dnevnik.bg','112':'Kanal 3','113':'268.dnevnik.bg','114':'224.dnevnik.bg',
'115':'133.dnevnik.bg','116':'Evrokom','117':'Bulgaria_24','201':'Diema','202':'272.dnevnik.bg','203':'272.dnevnik.bg','206':'192.dnevnik.bg','207':'201.dnevnik.bg',
'208':'103.dnevnik.bg','209':'SPORTALHD','212':'AMSHD','214':'201.dnevnik.bg','305':'208.dnevnik.bg'}
    self.__cachepath = cachepath
    self.__playlist = playlist
    self.__refresh = int(cachetime) * 60
    self.__p_data['user'][1] = login['usr']
    self.__log_in['pw'] = login['pass']
    self.__DEBUG_EN = dbg
    self.__t = timeout
    self.__BLOCK_SIZE = 16
    self.__URL_LOGIN = base + '/?auth'
    self.__URL_LIST = base + '/?json&tv&mini'
    #self.__URL_LIST = base + '/?json&tv&epg'
    self.__URL_XML = base + '/?xml&tv&mini'
    self.__URL_EPG = base + '/?json&epg'
    self.__js = None
    self.__epg = None

  def __log_dat(self, d):
    if self.__DEBUG_EN is not True:
      return
    print '---------'
    if type(d) is str:
      print d
    else:
      for k, v in d.iteritems():
        print k + ' : ' + str(v)

  def __store_data(self):
      with io.open(self.__cachepath, 'w+', encoding=self.__char_set) as f:
        f.write(unicode(json.dumps(self.__js,
                        sort_keys = True,
                        indent = 1,
                        ensure_ascii=False)))
      #self.__log_dat("Starting PLAYLIST SAVE")
      js1 = json.dumps(self.__js,
                        sort_keys = True,
                        indent = 1,
                        ensure_ascii=False)

      js1_res = '#EXTM3U tvg-shift=0\n' 
      for ch1 in self.__js['tv']:
      #for ch1 in js1['tv']:
		chid = None
		if self.__channelsid.has_key(unicode(ch1['channel'])):
			chid = self.__channelsid[unicode(ch1['channel'])]
		else:
			chid = unicode(ch1['channel'])
		if str(ch1['sources']).find('radio') is not -1:
			r1 = '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s.png" radio="true" group-title="%s",%s\n' % (chid,unicode(ch1['title']),unicode(ch1['channel']),unicode('Radio Channels'),unicode(ch1['title']))
		else:
			r1 = '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s.png" group-title="%s",%s\n' % (chid,unicode(ch1['title']),unicode(ch1['channel']),unicode('TV Channels'),unicode(ch1['title']))
		#r1 = '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="101-BNT 1 HD" group-title="NEWS",%s\n' % ('aa',unicode(ch1['title']) ,"cc")
#		js1_res += '#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="101-BNT 1 HD" group-title="Новини",%s\n' % (str(ch1['channel']),str(ch1['title']),str(ch1['title']))
		js1_res += r1
		js1_res += "%s\n" % str(ch1['sources'])
		#pass
               #js1_res+='#EXTINF:-1 tvg-id="%s" tvg-name="%s" tvg-logo="%s" group-title="",%s\n' % (ch1['title'],ch1['title'],ch1['title'],ch1['title'])	
      with io.open(self.__playlist, 'w+', encoding=self.__char_set) as f1:
		
		#f1.write(js1_res)
		f1.write(unicode(js1_res))	
      #self.__log_dat("Ending PLAYLIST SAVE")

  def __restore_data(self):
    with open(self.__cachepath, 'r') as f:
      self.__js = json.load(f)

  def __goforit(self):
    s = Session()
    r = s.post(self.__URL_LOGIN, timeout=self.__t,
                headers=self.__UA)

    if r.status_code == codes.ok:
      self.__log_in['key'] = r.headers['challenge']
      self.__log_in['session'] = r.headers['ssbulsatapi']

      s.headers.update({'SSBULSATAPI': self.__log_in['session']})

      _text = self.__log_in['pw'] + (self.__BLOCK_SIZE - len(self.__log_in['pw']) % self.__BLOCK_SIZE) * '\0'

      enc = EN.AESModeOfOperationECB(self.__log_in['key'])
      self.__p_data['pass'][1] = base64.b64encode(enc.encrypt(_text))

      self.__log_dat(self.__log_in)
      self.__log_dat(self.__p_data)

      r = s.post(self.__URL_LOGIN, timeout=self.__t,
                  headers=self.__UA, files=self.__p_data)

      self.__log_dat(r.request.headers)
      self.__log_dat(r.request.body)

      if r.status_code == codes.ok:
        data = r.json()
        if data['Logged'] == 'true':
          self.__log_dat('Login ok')
          s.headers.update({'Access-Control-Request-Method': 'POST'})
          s.headers.update({'Access-Control-Request-Headers': 'ssbulsatapi'})

          r = s.options(self.__URL_LIST, timeout=self.__t,
                          headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)
          self.__log_dat(str(r.status_code))

          r = s.post(self.__URL_LIST, timeout=self.__t,
                      headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)
          if r.status_code == codes.ok:
            self.__char_set = r.headers['content-type'].split('charset=')[1]
            self.__log_dat('get data ok')
            self.__js = r.json()
            #self.__log_dat(self.__js)
            self.__store_data()

	  r = s.post(self.__URL_EPG, timeout=self.__t,
                      headers=self.__UA)
	  if r.status_code == codes.ok:
	    self.__epg = r.json()
	    self.__log_dat(self.__epg)
        else:
          raise Exception("LoginFail")

  def data_fetch(self):
    if os.path.exists(self.__cachepath):
      self.__restore_data()
      if time.time() - self.__js['ts'] < self.__refresh:
        self.__log_dat('Use cache file')
      else:
        self.__log_dat('Use site')
        self.__js = None

    if self.__js is None:
      self.__goforit()
      self.__js['ts'] = divmod(time.time(), self.__refresh)[0] * self.__refresh
      self.__log_dat('Base time: %s' % time.ctime(self.__js['ts']))
      self.__store_data()

   if self.__js is not None and self.__js['tv'] is not None:
      for ch in self.__js['tv']:
         yield self.__js['tv'].index(ch) , ch
