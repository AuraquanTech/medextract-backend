import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from mangum import Mangum
from src.main import app

handler = Mangum(app)
