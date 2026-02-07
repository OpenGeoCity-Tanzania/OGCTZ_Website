import sys
import os

# Add ogctz_frontend to Python path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ogctz_frontend'))

# Import the Flask app from ogctz_frontend/app.py
# This keeps your app.py clean and uses it as the main app
from app import app
