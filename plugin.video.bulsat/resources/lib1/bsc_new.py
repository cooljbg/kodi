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
    self.__cachepath = cachepath
    self.__refresh = int(cachetime) * 60
    self.__p_data['user'][1] = login['usr']
    self.__log_in['pw'] = login['pass']
    self.__DEBUG_EN = dbg
    self.__t = timeout
    self.__BLOCK_SIZE = 16
    self.__URL_LOGIN = base + '/?auth'
    self.__URL_LIST = base + '/?json&tv'
    self.__js = None

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
            self.__log_dat(self.__js)
            self.__store_data()
        else:
          raise Exception("LoginFail")

  def __data_fetch(self):
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

  def get_genres(self):
    self.__data_fetch()
    seen = set()
    for g in [x['genre'] for x in self.__js['tvlists']['tv'] if not (x['genre'] in seen or seen.add(x['genre']))]:
      yield g

  def get_all_by_genre(self, g):
    self.__data_fetch()
    for ch in [i for i in self.__js['tvlists']['tv'] if i['genre'] == g]:
      yield ch
