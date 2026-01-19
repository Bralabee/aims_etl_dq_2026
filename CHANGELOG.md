# Changelog

All notable changes to the AIMS Data Platform project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-01-19

### Added - Comprehensive Notebook Refactoring

#### New Shared Utility Library (`notebooks/lib/`)
- **`platform_utils.py`** - Platform detection (IS_FABRIC), base directory resolution, safe parquet reading
- **`storage.py`** - StorageManager class for medallion architecture (Bronze/Silver/Gold) with platform-aware writes
- **`settings.py`** - Singleton Settings class for centralized configuration management
- **`logging_utils.py`** - Structured logging with timed operations and notebook-specific logger setup
- **`config.py`** - Configuration loading and environment variable management

#### New Configuration System (`notebooks/config/`)
- **`notebook_settings.yaml`** - Environment-specific settings (local vs Fabric)
- Centralized DQ thresholds, paths, and pipeline phase configuration
- Automatic environment detection and path resolution

#### Orchestration Notebook (`00_AIMS_Orchestration.ipynb`)
- Master orchestration notebook for running all pipeline phases
- Phase 1: Data Profiling (68 files profiled in ~7.5s)
- Phase 2: Validation & Ingestion (50/68 passed, ingested to Silver)
- Phase 3: Monitoring & Reporting with key metrics
- Execution logging with JSON output

### Changed

#### Refactored Notebooks (00-08)
- Standardized imports using shared library modules
- Replaced inline configuration with centralized settings
- Added structured logging throughout
- Improved error handling and fallback mechanisms
- Platform-aware storage operations (Parquet locally, Delta Lake in Fabric)

### Fixed
- `AttributeError: 'Settings' object has no attribute 'results_dir'` → Use `validation_results_dir`
- Duplicate cell outputs in orchestration notebook cleaned up
- Consistent path handling across all notebooks

### Verified
- ✅ Full pipeline execution: 68 files processed, 0 runtime errors
- ✅ Test suite: 74/74 tests passing
- ✅ CLI commands working correctly
- ✅ Orchestration notebook: All 3 phases complete in ~72 seconds
- ✅ StorageManager: Successfully ingested 50 files to Silver layer

### Technical Details
- **Version Tag**: `v1.3.0`
- **Safety Rollback**: `git checkout v1.2.0-pre-notebook-refactor`
- **Python**: 3.11.14 in `aims_data_platform` conda environment

---

## [1.2.0] - 2026-01-18

### Added
- Pre-notebook refactor checkpoint (tag: `v1.2.0-pre-notebook-refactor`)
- Comprehensive notebook review identifying 6 major issue categories

### Fixed
- Various bug fixes from comprehensive review
- Test suite improvements

---

## [1.1.0] - 2025-12-11

### Added
- Initial data profiling implementation
- Great Expectations integration
- 68 validation configuration files generated
- Basic CLI commands for ingestion and validation

### Changed
- Improved parallel processing for batch profiling
- Enhanced error handling in DataLoader

---

## [1.0.0] - 2025-12-01

### Added
- Initial release of AIMS Data Platform
- Bronze/Silver/Gold medallion architecture
- Watermark-based incremental loading
- Microsoft Fabric compatibility
- Comprehensive documentation (170+ pages)
- CI/CD pipelines (Azure DevOps + GitHub Actions)
