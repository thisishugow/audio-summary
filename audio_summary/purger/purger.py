"""
檔案清理模組 (Purger)

這個模組提供定期自動清理功能，清除指定目錄下的舊檔案。
"""

import os
import time
import logging
import threading
import schedule
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Set, Union, Callable

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('file_purger')

# 預設設定
DEFAULT_PURGE_FREQUENCY = "daily"  # daily, weekly, monthly
DEFAULT_PURGE_AGE_DAYS = 7
DEFAULT_PURGE_FILE_TYPES = None  # None 表示所有類型
DEFAULT_PURGE_ENABLED = True
DEFAULT_PURGE_DRY_RUN = False
DEFAULT_PURGE_LOG_LEVEL = "INFO"

# 排程器
scheduler = None
scheduler_thread = None
is_running = False


class Purger:
    """檔案清理類別"""

    def __init__(
        self,
        dump_dir: Union[str, Path],
        frequency: str = DEFAULT_PURGE_FREQUENCY,
        age_days: int = DEFAULT_PURGE_AGE_DAYS,
        file_types: Optional[List[str]] = DEFAULT_PURGE_FILE_TYPES,
        enabled: bool = DEFAULT_PURGE_ENABLED,
        dry_run: bool = DEFAULT_PURGE_DRY_RUN,
        log_level: str = DEFAULT_PURGE_LOG_LEVEL
    ):
        """初始化清理器

        Args:
            dump_dir (Union[str, Path]): 要清理的目錄路徑
            frequency (str, optional): 清理頻率，可為 "daily", "weekly", "monthly"。預設為 "daily"
            age_days (int, optional): 檔案保存期限（天）。預設為 7
            file_types (Optional[List[str]], optional): 要清理的檔案類型列表。預設為 None，表示所有類型
            enabled (bool, optional): 是否啟用自動清理。預設為 True
            dry_run (bool, optional): 是否僅模擬清理（不實際刪除）。預設為 False
            log_level (str, optional): 日誌級別。預設為 "INFO"
        """
        self.dump_dir = Path(dump_dir)
        self.frequency = frequency
        self.age_days = age_days
        self.file_types = file_types
        self.enabled = enabled
        self.dry_run = dry_run
        
        # 設定日誌級別
        log_level_dict = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        logger.setLevel(log_level_dict.get(log_level.upper(), logging.INFO))
        
        # 確保目錄存在
        if not self.dump_dir.exists():
            logger.info(f"創建目錄: {self.dump_dir}")
            self.dump_dir.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"清理器已初始化: 目錄={self.dump_dir}, 頻率={self.frequency}, 保存期限={self.age_days}天")

    def purge_files(self) -> int:
        """執行檔案清理

        Returns:
            int: 已清理的檔案數量
        """
        if not self.enabled:
            logger.info("清理已禁用，跳過")
            return 0
            
        if not self.dump_dir.exists():
            logger.warning(f"目錄不存在: {self.dump_dir}")
            return 0
            
        # 計算截止日期
        cutoff_date = datetime.now() - timedelta(days=self.age_days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        logger.info(f"開始清理: 目錄={self.dump_dir}, 保存期限={self.age_days}天, 日期早於 {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} 的檔案將被清理")
        
        # 計數器
        purged_count = 0
        skipped_count = 0
        
        # 獲取所有檔案
        for file_path in self.dump_dir.glob('**/*'):
            if not file_path.is_file():
                continue
                
            # 檢查檔案類型
            if self.file_types is not None:
                file_ext = file_path.suffix.lower()
                if file_ext not in self.file_types:
                    logger.debug(f"跳過不符合類型的檔案: {file_path}")
                    skipped_count += 1
                    continue
            
            # 檢查檔案年齡
            file_mtime = file_path.stat().st_mtime
            if file_mtime >= cutoff_timestamp:
                logger.debug(f"跳過較新的檔案: {file_path}")
                skipped_count += 1
                continue
                
            # 清理檔案
            file_age_days = (datetime.now().timestamp() - file_mtime) / 86400
            if self.dry_run:
                logger.info(f"[DRY RUN] 將刪除: {file_path} (已存在 {file_age_days:.1f} 天)")
            else:
                try:
                    logger.info(f"刪除檔案: {file_path} (已存在 {file_age_days:.1f} 天)")
                    file_path.unlink()
                    purged_count += 1
                except Exception as e:
                    logger.error(f"刪除檔案時出錯: {file_path} - {e}")
        
        logger.info(f"清理完成: 已刪除 {purged_count} 個檔案, 已跳過 {skipped_count} 個檔案")
        return purged_count


def _run_scheduler():
    """在排程器執行緒中運行排程器"""
    global is_running
    is_running = True
    while is_running:
        schedule.run_pending()
        time.sleep(1)


def setup_purger(
    dump_dir: Union[str, Path] = None,
    frequency: str = None,
    age_days: int = None,
    file_types: Optional[List[str]] = None,
    enabled: bool = None,
    dry_run: bool = None,
    log_level: str = None
) -> Purger:
    """設置清理器

    Args:
        dump_dir (Union[str, Path], optional): 要清理的目錄路徑，如果為 None，則使用環境變數 APP_FILE_DUMP。
        frequency (str, optional): 清理頻率，可為 "daily", "weekly", "monthly"。
        age_days (int, optional): 檔案保存期限（天）。
        file_types (Optional[List[str]], optional): 要清理的檔案類型列表。
        enabled (bool, optional): 是否啟用自動清理。
        dry_run (bool, optional): 是否僅模擬清理（不實際刪除）。
        log_level (str, optional): 日誌級別。

    Returns:
        Purger: 清理器實例
    """
    # 從環境變數獲取配置（如果未指定）
    if dump_dir is None:
        dump_dir = os.getenv("APP_FILE_DUMP", "file_dump")
    
    if frequency is None:
        frequency = os.getenv("PURGE_FREQUENCY", DEFAULT_PURGE_FREQUENCY)
    
    if age_days is None:
        age_days = int(os.getenv("PURGE_AGE_DAYS", DEFAULT_PURGE_AGE_DAYS))
    
    if file_types is None and os.getenv("PURGE_FILE_TYPES"):
        file_types = os.getenv("PURGE_FILE_TYPES").split(",")
    
    if enabled is None:
        enabled = os.getenv("PURGE_ENABLED", "True").lower() == "true"
    
    if dry_run is None:
        dry_run = os.getenv("PURGE_DRY_RUN", "False").lower() == "true"
    
    if log_level is None:
        log_level = os.getenv("PURGE_LOG_LEVEL", DEFAULT_PURGE_LOG_LEVEL)
    
    # 創建清理器實例
    return Purger(
        dump_dir=dump_dir,
        frequency=frequency,
        age_days=age_days,
        file_types=file_types,
        enabled=enabled,
        dry_run=dry_run,
        log_level=log_level
    )


def start_scheduler(purger: Purger) -> bool:
    """啟動排程器

    Args:
        purger (Purger): 清理器實例

    Returns:
        bool: 是否成功啟動
    """
    global scheduler, scheduler_thread, is_running
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.warning("排程器已在運行中")
        return False
    
    # 清除現有排程
    schedule.clear()
    
    # 根據頻率設定排程
    if purger.frequency.lower() == "daily":
        schedule.every().day.at("03:00").do(purger.purge_files)
        logger.info("已設定每日清理排程 (03:00)")
    elif purger.frequency.lower() == "weekly":
        schedule.every().monday.at("03:00").do(purger.purge_files)
        logger.info("已設定每週清理排程 (週一 03:00)")
    elif purger.frequency.lower() == "monthly":
        schedule.every().month.day(1).at("03:00").do(purger.purge_files)
        logger.info("已設定每月清理排程 (每月1日 03:00)")
    else:
        logger.error(f"無效的頻率: {purger.frequency}")
        return False
    
    # 啟動排程器執行緒
    scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("清理排程器已啟動")
    return True


def stop_scheduler() -> bool:
    """停止排程器

    Returns:
        bool: 是否成功停止
    """
    global scheduler_thread, is_running
    
    if not scheduler_thread or not scheduler_thread.is_alive():
        logger.warning("排程器未在運行中")
        return False
    
    is_running = False
    schedule.clear()
    
    # 等待排程器執行緒結束
    scheduler_thread.join(timeout=2.0)
    
    logger.info("清理排程器已停止")
    return True


def purge_now(purger: Purger) -> int:
    """立即執行清理

    Args:
        purger (Purger): 清理器實例

    Returns:
        int: 已清理的檔案數量
    """
    logger.info("立即執行清理")
    return purger.purge_files()


# 使用範例
if __name__ == "__main__":
    # 初始化清理器
    purger = setup_purger()
    
    # 立即執行一次清理
    purge_count = purge_now(purger)
    print(f"已清理 {purge_count} 個檔案")
    
    # 啟動排程器
    start_scheduler(purger)
    
    try:
        # 保持程式運行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 停止排程器
        stop_scheduler()
        print("程式已退出")
