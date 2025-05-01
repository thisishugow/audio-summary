#!/bin/bash

audio_summary > /dev/stdout 2>&1 &
audio_summary_purger --start-scheduler --dump-dir $APP_FILE_DUMP --age-days $APP_FILE_DUMP_AGE_DAYS > /dev/stdout 2>&1 &

# 保持容器運行
tail -f /dev/null