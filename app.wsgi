
import os; os.chdir('/csc/code/connectme')
import sys
sys.stdout = sys.stderr
sys.path.insert(0, '/csc/code/connectme')
os.environ['NLTK_DATA'] = '/csc/main/data/nltk'
from connectme import app as application
