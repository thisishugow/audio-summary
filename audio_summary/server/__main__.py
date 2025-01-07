import os
import audio_summary.server.run as main_script
from dotenv import load_dotenv
load_dotenv()

def main():
    __target = os.path.realpath(main_script.__file__)
    MAX_UPLOAD_SIZE = os.getenv("MAX_FILE_SIZE", "1024")
    cmd = ' '.join(["streamlit", "run",  f"{repr(__target)}", "--server.maxUploadSize", MAX_UPLOAD_SIZE])
    os.system(cmd)

if __name__ == "__main__":
    main()