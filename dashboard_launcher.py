"""Desktop launcher used by the Windows .exe build."""
import os,sys,subprocess
here=os.path.dirname(os.path.abspath(sys.argv[0]));dashboard=os.path.join(here,'dashboard.py')
subprocess.call([sys.executable,'-m','streamlit','run',dashboard,'--server.headless','true','--browser.gatherUsageStats','false'])
