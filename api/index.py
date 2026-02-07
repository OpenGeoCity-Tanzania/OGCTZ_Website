import sys
from pathlib import Path

# Add the ogctz_frontend directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "ogctz_frontend"))

from app import app

# Export the Flask app for Vercel
export = app
