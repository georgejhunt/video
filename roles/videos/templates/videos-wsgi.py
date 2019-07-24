#! /usr/bin/env python
# -*- coding: utf-8 -*-
# using Python's bundled WSGI server

from wsgiref.simple_server import make_server
import subprocess
from dateutil.tz import *
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from jinja2 import Environment, FileSystemLoader
import sqlite3
import re

# Create the jinja2 environment.
CAPTIVE_PORTAL_BASE = "/opt/iiab/captive-portal"
j2_env = Environment(loader=FileSystemLoader(CAPTIVE_PORTAL_BASE),trim_blocks=True)

# Get the IIAB variables
sys.path.append('/etc/iiab/')
from iiab_env import get_iiab_env
doc_root = get_iiab_env("WWWROOT")
fully_qualified_domain_name = get_iiab_env("FQDN")


# set up some logging -- selectable for diagnostics
# Create dummy iostream to capture stderr and stdout
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

#if len(sys.argv) > 1 and sys.argv[1] == '-l':
if True:
    loggingLevel = logging.DEBUG
    try:
      os.remove('/var/log/apache2/portal.log')
    except:
      pass
else:
    loggingLevel = logging.ERROR

# divert stdout and stderr to logger
logging.basicConfig(filename='/var/log/apache2/portal.log',format='%(asctime)s.%(msecs)03d:%(name)s:%(message)s', datefmt='%M:%S',level=loggingLevel)
logger = logging.getLogger('/var/log/apache2/portal.log')
handler = RotatingFileHandler("/var/log/apache2/portal.log", maxBytes=100000, backupCount=2)
logger.addHandler(handler)

stdout_logger = logging.getLogger('STDOUT')
sl = StreamToLogger(stdout_logger, logging.ERROR)
sys.stdout = sl

stderr_logger = logging.getLogger('STDERR')
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl


# Define globals

PORT=9458
logger.debug("")
logger.debug('##########################################')

# =============  Return html pages  ============================
def banner(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png')]
    start_response(status, headers)
    image = open("%s/js-menu/menu-files/images/iiab_banner6.png"%doc_root, "rb").read()
    return [image]

def bootstrap(environ, start_response):
    logger.debug("in bootstrap")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("%s/common/js/bootstrap.min.js"%doc_root, "rb").read() 
    return [boot]

def jquery(environ, start_response):
    logger.debug("in jquery")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("%s/common/js/jquery.min.js"%doc_root, "rb").read() 
    return [boot]

def bootstrap_css(environ, start_response):
    logger.debug("in bootstrap_css")
    status = '200 OK'
    headers = [('Content-type', 'text/css')]
    start_response(status, headers)
    boot = open("%s/common/css/bootstrap.min.css"%doc_root, "rb").read() 
    return [boot]

#
# ================== Start serving the wsgi application  =================
def application (environ, start_response):

   #######   Return pages based upon PATH   ###############
   # do more specific stuff first
   if  environ['PATH_INFO'] == "/iiab_banner6.png":
      return banner(environ, start_response) 

   if  environ['PATH_INFO'] == "/bootstrap.min.js":
      return bootstrap(environ, start_response) 

   if  environ['PATH_INFO'] == "/bootstrap.min.css":
      return bootstrap_css(environ, start_response) 

   if  environ['PATH_INFO'] == "/jquery.min.js":
      return jquery(environ, start_response) 

   if  environ['PATH_INFO'] == "/favicon.ico":
      return null(environ, start_response) 

   #### parse OS platform based upon URL  ##################
   # mac
   if  environ['PATH_INFO'] == "/mac_splash":
      return mac_splash(environ, start_response) 

   if  environ['PATH_INFO'] == "/step2":
      return step2(environ, start_response) 

   if environ['HTTP_HOST'] == "captive.apple.com" or\
     environ['HTTP_HOST'] == "appleiphonecell.com" or\
     environ['HTTP_HOST'] == "*.apple.com.edgekey.net" or\
     environ['HTTP_HOST'] == "gsp1.apple.com" or\
     environ['HTTP_HOST'] == "apple.com" or\
     environ['HTTP_HOST'] == "www.apple.com": 
     current_ts, last_ts, send204after = timeout_info(ip) 
     if not send204after:
          # take care of uninitialized state
          set_204after(ip,0)
     return macintosh(environ, start_response) 

   # android
   if  environ['PATH_INFO'] == "/android_splash":
     return android_splash(environ, start_response) 
   if  environ['PATH_INFO'] == "/android_https":
     return android_https(environ, start_response) 
   if environ['HTTP_HOST'] == "clients3.google.com" or\
      environ['HTTP_HOST'] == "mtalk.google.com" or\
      environ['HTTP_HOST'] == "alt7-mtalk.google.com" or\
      environ['HTTP_HOST'] == "alt6-mtalk.google.com" or\
      environ['HTTP_HOST'] == "connectivitycheck.android.com" or\
      environ['PATH_INFO'] == "/gen_204" or\
      environ['HTTP_HOST'] == "connectivitycheck.gstatic.com":
      current_ts, last_ts, send204after = timeout_info(ip) 
      logger.debug("current_ts: %s last_ts: %s send204after: %s"%(current_ts, last_ts, send204after,))
      if not last_ts or (ts - int(last_ts) > INACTIVITY_TO):
          return android(environ, start_response) 
      elif is_after204_timeout(ip):
          return put_204(environ,start_response)
      return android(environ, start_response) 

   # microsoft
   if environ['HTTP_HOST'] == "ipv6.msftncsi.com" or\
     environ['HTTP_HOST'] == "detectportal.firefox.com" or\
     environ['HTTP_HOST'] == "ipv6.msftncsi.com.edgesuite.net" or\
     environ['HTTP_HOST'] == "www.msftncsi.com" or\
     environ['HTTP_HOST'] == "www.msftncsi.com.edgesuite.net" or\
     environ['HTTP_HOST'] == "www.msftconnecttest.com" or\
     environ['HTTP_HOST'] == "www.msn.com" or\
     environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com" or\
     environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com.nsatc.net": 
     return microsoft(environ, start_response) 


# Instantiate the server
if __name__ == "__main__":
    httpd = make_server (
    "", # The host name
    PORT, # A port number where to wait for the request
    application # The application object name, in this case a function
    )

    httpd.serve_forever()
#vim: tabstop=3 expandtab shiftwidth=3 softtabstop=3 background=dark

