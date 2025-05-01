# 檔案清理模組 (Purger)

這個模組提供定期自動清理功能，可以清除 APP_FILE_DUMP 目錄下的舊檔案，避免檔案累積佔用過多磁碟空間。

## 安裝

首先安裝所需依賴項：

```bash
pip install -r audio_summary/purger/requirements.txt
```

## 功能特點

- **定期自動清理**：可設定清理頻率（每天/每週/每月）
- **檔案保存期限**：可設定檔案保存的最長時間（例如7天、30天等）
- **檔案類型過濾**：可設定要清理的檔案類型（例如只清理 .mp3, .txt 等）
- **手動觸發清理**：提供 API 可手動觸發清理操作
- **日誌記錄**：記錄所有清理活動，包括清理時間、清理檔案數量等
- **安全機制**：防止意外刪除重要文件的保護措施

## 使用方法

### 1. 程式碼中使用

```python
from audio_summary.purger import setup_purger, start_scheduler, purge_now

# 初始化清理器
purger = setup_purger(
    dump_dir="file_dump",
    frequency="daily",
    age_days=7,
    file_types=[".mp3", ".txt", ".docx"],
    enabled=True,
    dry_run=False
)

# 立即執行一次清理
purge_count = purge_now(purger)
print(f"已清理 {purge_count} 個檔案")

# 啟動排程器
start_scheduler(purger)
```

### 2. 命令行使用

立即執行清理：
```bash
python -m audio_summary.purger.cli --purge-now --age-days 7
```

啟動排程器：
```bash
python -m audio_summary.purger.cli --start-scheduler --frequency daily --age-days 30
```

帶有更多選項：
```bash
python -m audio_summary.purger.cli --purge-now --dump-dir "/data/files" --age-days 14 --file-types ".mp3,.txt,.docx" --dry-run --log-level DEBUG
```

### 3. 環境變數配置

您也可以通過環境變數配置清理器：
```bash
export APP_FILE_DUMP="/path/to/files"
export PURGE_FREQUENCY="weekly"
export PURGE_AGE_DAYS="14"
export PURGE_FILE_TYPES=".mp3,.txt,.docx"
export PURGE_DRY_RUN="false"
export PURGE_LOG_LEVEL="INFO"
```

然後簡單運行：
```bash
python -m audio_summary.purger.cli --purge-now
```

## 配置參數

- `APP_FILE_DUMP`：檔案存放目錄，預設為 "file_dump"
- `PURGE_FREQUENCY`：清理頻率，預設為 "daily"
- `PURGE_AGE_DAYS`：檔案保存期限（天），預設為 7
- `PURGE_FILE_TYPES`：要清理的檔案類型，預設為全部
- `PURGE_ENABLED`：是否啟用自動清理，預設為 True
- `PURGE_DRY_RUN`：是否僅模擬清理（不實際刪除），預設為 False
- `PURGE_LOG_LEVEL`：日誌級別，預設為 INFO 