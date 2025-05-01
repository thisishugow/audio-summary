# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [UNRELEASED]

### Added
- [x] Add streamlit UI.

### Changed

### Fixed
  
### Deprecated 


## [0.1.6] 2024-11-21
### Added
- Docker support
- Automatic file cleanup functionality (purger)
- Added startup scripts
- Added schedule dependency

### Changed
- Removed unnecessary dependencies (transformers, datasets, accelerate, etc.)
- Updated Poetry configuration, added script entry points

### Fixed
- Optimized log output in Docker environment

## [0.1.5] 2024-11-20
### Added
- Offline APP (work w/ local Whisper)


## [0.1.4] 2024-06-14

### Added
- Add option `duration` to control the size of split audio. 
- User check if the split file size exceeds 25 MB (limit from Whisper). 

### Changed
- Use `google-generativeai` instead of requesting manually. 

### Fixed
- Remove the tmp files while API request interrupted. 
  
### Deprecated 
- Request manually via url. 


## [0.1.4-rc1] - 2024-06-03

### Added
- Add option `duration` to control the size of split audio. 
- User check if the split file size exceeds 25 MB (limit from Whisper). 

### Changed
- Use `google-generativeai` instead of requesting manually. 

### Fixed
- Remove the tmp files while API request interrupted. 
  
### Deprecated 
- Request manually via url. 


## [0.1.3] - 2024-05-11

### Fixed
- fixed some bugs

### Changed
- use AsyncOpenAI to improve performance. 
  
### Added
- improve logs.(2024-05-11) 
- add lang opt