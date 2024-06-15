import os
import audio_summary.server.run as main_script

__target = os.path.realpath(main_script.__file__)
cmd = ' '.join(["streamlit", "run",  f"{repr(__target)}"])
os.system(cmd)