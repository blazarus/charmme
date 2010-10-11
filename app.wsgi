
import os; os.chdir('/csc/code/connectme')
import sys
sys.stdout = sys.stderr
sys.path.insert(0, '/csc/code/connectme')
from connectme import app as application
