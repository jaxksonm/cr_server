import sys
import logging

logging.basicConfig(stream=sys.stderr)

# Add your project directory to the Python path
sys.path.insert(0, "/var/www/html")

# Import your Flask app object as 'application' for mod_wsgi
from app import app as application

