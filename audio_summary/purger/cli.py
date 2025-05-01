#!/usr/bin/env python
"""
檔案清理命令行工具

提供簡單的命令行界面，用於手動執行檔案清理任務
"""

import os
import sys
import argparse
import time
from typing import List, Optional

from audio_summary.purger.purger import (
    setup_purger,
    start_scheduler,
    stop_scheduler,
    purge_now
)


def parse_args():
    """解析命令行參數

    Returns:
        argparse.Namespace: 解析後的參數
    """
    parser = argparse.ArgumentParser(
        description=(
            "檔案清理工具 - 清理應用程式產生的檔案\n"
            "Example: audio_summary_purger --purge-now --dump-dir $APP_FILE_DUMP\n"
            "Example: audio_summary_purger --start-scheduler --dump-dir $APP_FILE_DUMP\n"
            
        )
    )
    
    # 動作選項
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--purge-now", 
        action="store_true", 
        help="立即執行一次清理"
    )
    action_group.add_argument(
        "--start-scheduler", 
        action="store_true", 
        help="啟動清理排程器"
    )
    
    # 配置選項
    parser.add_argument(
        "--dump-dir", 
        type=str, 
        help="要清理的目錄路徑 (預設: APP_FILE_DUMP 環境變數或 'file_dump')"
    )
    parser.add_argument(
        "--frequency", 
        type=str, 
        choices=["daily", "weekly", "monthly"],
        help="清理頻率 (預設: 每日)"
    )
    parser.add_argument(
        "--age-days", 
        type=int, 
        help="檔案保存期限（天） (預設: 7)"
    )
    parser.add_argument(
        "--file-types", 
        type=str, 
        help="要清理的檔案類型，以逗號分隔 (預設: 所有類型)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="僅模擬清理，不實際刪除檔案"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日誌級別 (預設: INFO)"
    )
    
    return parser.parse_args()


def main():
    """主函數"""
    args = parse_args()
    
    # 處理檔案類型
    file_types = None
    if args.file_types:
        file_types = [t.strip() for t in args.file_types.split(",")]
    
    # 設置清理器
    purger = setup_purger(
        dump_dir=args.dump_dir,
        frequency=args.frequency,
        age_days=args.age_days,
        file_types=file_types,
        enabled=True,
        dry_run=args.dry_run,
        log_level=args.log_level
    )
    
    # 執行動作
    if args.purge_now:
        # 立即執行一次清理
        purged_count = purge_now(purger)
        print(f"已清理 {purged_count} 個檔案")
    
    elif args.start_scheduler:
        # 啟動排程器
        start_scheduler(purger)
        print("排程器已啟動。按 Ctrl+C 停止...")
        
        try:
            # 保持程式運行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # 停止排程器
            stop_scheduler()
            print("程式已退出")


if __name__ == "__main__":
    main() 