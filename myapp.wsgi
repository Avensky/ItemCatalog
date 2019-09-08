#!/usr/bin/python
import sys
import logging
sys.path.append('/var/www/html/ItemCatalog')
from __init__ import app as application
application.secret_key = 'super_secret_key'

