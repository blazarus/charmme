
import os; os.chdir('/csc/code/charmme')
import sys
sys.stdout = sys.stderr
sys.path.insert(0, '/csc/code/charmme')
os.environ['NLTK_DATA'] = '/csc/main/data/nltk'
from main import app as application
