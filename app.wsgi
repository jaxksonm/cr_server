import sys
import logging

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, "/var/www/html")

from app import app as application

