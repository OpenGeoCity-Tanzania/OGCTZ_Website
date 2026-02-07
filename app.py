import sys
import os

# Add ogctz_frontend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ogctz_frontend'))

# Import the Flask app from ogctz_frontend/app.py
from app import app

# This file is imported by Vercel as the entry point
