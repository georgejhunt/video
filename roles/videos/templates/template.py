#!/usr/bin/env python
# -*- coding: utf-8 -*-
# server.py

import os
from flask import Flask,request
from jinja2 import Environment, FileSystemLoader
import json

# Create the jinja2 environment.
CAPTIVE_PORTAL_BASE = "/opt/iiab/captive-portal"
j2_env = Environment(loader=FileSystemLoader(CAPTIVE_PORTAL_BASE),trim_blocks=True)

application = Flask(__name__)


@application.route('/')
def one():
    rv = "hello world"
    return str(rv)

    
if __name__ == "__main__":
    application.run(host='0.0.0.0',port=9458)

#vim: tabstop=3 expandtab shiftwidth=3 softtabstop=3 background=dark
