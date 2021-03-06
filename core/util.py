#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
#
#
import time
import json
import base64
import urllib
import urllib2
import logging
import hashlib
import threading

import smtplib
from email.mime.text import MIMEText

from datetime import datetime

from config import DEBUG, LOG_PATH, EMAIL_ACCOUNT, EMAIL_PASSWORD, __version__

encrypt_md5 = lambda s: hashlib.md5(s + '3d2535f2ecf1dd3b7b').hexdigest()
md5 = lambda s: hashlib.md5(s).hexdigest()

NOW = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
now = lambda: datetime.now()

def utf8sub(content, start = 0, end = 50):
    if isinstance(content, unicode):
        return content[start:end]
    if isinstance(content, str):
        return content.decode('utf-8')[start:end].encode('utf-8')
    return content

def make_active_code(loginname, email):
    return base64.b64encode(encrypt_md5(loginname + email + time.time()))

def send_active_email(email, activecode):
    pass

def page_bar(count, index, size):
    """ 生成页码 """
    totalpage = count / size if count % size == 0 else count / size + 1
    currentpage = index
    nextpage = index + 1 if (index + 1) <= totalpage else totalpage
    prevpage = index -1 if (index -1) >= 1 else 1

    return dict(totalpage = totalpage,
                currpage = currentpage,
                nextpage = nextpage,
                prevpage = prevpage)

def http_helpler(url, params, method = 'POST'):
    """ http请求辅助函数 """
    params = urllib.urlencode(params)
    if method.lower() == 'post':
        request = urllib2.Request(url, params)
    elif method.lower() == 'get':
        url += '?'+params
        request = urllib2.Request(url)
    else:
        raise ValueError('method error')

    response = urllib2.urlopen(request)
    tmp = response.read()
    result = json.loads(tmp)
    return result

def get_logger():
    logger = logging.getLogger()
    if DEBUG:
        hdl = logging.StreamHandler()
        level = logging.DEBUG
    else:
        level = logging.INFO
        hdl = logging.FileHandler(LOG_PATH)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    hdl.setFormatter(fmt)
    handler = hdl
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(level) # change to DEBUG for higher verbosity
    return logger


class HttpHelper(object):
    def __init__(self, url, params = {}, method = 'GET'):
        self._url = url
        self._params = params
        self._method = method
        self.cookies = []
        self.make_request()

    def make_request(self):
        params = urllib.urlencode(self._params)
        method = self._method
        url = self._url
        if not self._url.startswith('http://'):
            url = 'http://' + self._url
        if method == 'GET':
            self.request = urllib2.Request(url + "?" + params)
        else:
            self.request = urllib2.Request(url, params)
        if self.cookies:
            self.add_header('Cookie', ';'.join(self.cookies))

    def add_header(self, key, val):
        self.request.add_header(key, val)

    def change(self, url, params = {}, method = 'GET'):
        self._url = url
        self._params = params
        self._method = method
        self.make_request()

    def open(self):
        response = urllib2.urlopen(self.request)
        cookies = response.headers.dict.get('set-cookie')
        if cookies:
            self.cookies.append(cookies)
        content = response.read()
        try:
            return json.loads(content)
        except:
            return content

def _send_mail(to_list, sub, content):
    logger = get_logger()
    user, server = EMAIL_ACCOUNT.split("@")
    content += u"<br /> (这是一封由系统生成的邮件,请勿回复)"
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = sub
    msg['From'] = "<"+EMAIL_ACCOUNT+">"
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP_SSL("smtp." + server)
        s.login(user, EMAIL_PASSWORD)
    except Exception as e:
        logger.info(str(e))
        return False
    s.sendmail(EMAIL_ACCOUNT, to_list, msg.as_string())
    s.close()
    logger.debug(msg.as_string())
    logger.info("Send email to %r", to_list)
    return True

def send_mail(to_list, sub, content):
    target = _send_mail
    t = threading.Thread(target = target, args = (to_list, sub, content))
    t.start()


def get_version():
    return float(str(__version__[0]) + '.' + str(__version__[1]) + \
                        str(__version__[2]))
