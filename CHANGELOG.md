# Changelog

All notable changes to the AIMS Data Platform project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-01-20

### Fixed - Fabric Configuration Loading

#### Root Cause
- Settings failed to load YAML config when running from wheel package in Fabric
- `_paths` dict was empty, causing fallback to hardcoded `"data/bronze"` (lowercase)
- Result: Wrong path `/lakehouse/default/Files/data/bronze` instead of `/lakehouse/default/Files/Bronze`

#### Configuration Loading Improvements (`settings.py`)
- **Enhanced `_find_config_file()`** - Now searches Fabric user-uploaded path FIRST: `/lakehouse/default/Files/notebooks/config/notebook_settings.yaml`
- **Added `importlib.resources` fallback** - Loads YAML from wheel package resources when file paths don't work
- **Added `_get_default_config()`** - Hardcoded fallback with correct Fabric paths (capitalized Bronze/Silver/Gold)
- **Added `_load_yaml_config()` multi-tier loading** - File → Package Resources → Defaults

#### Wheel Package Updates
- **Version**: 1.3.1
- **Includes**: `notebook_settings.yaml` in wheel
- **Package data**: Added `[tool.setuptools.package-data]` for YAML files

### Verified
- ✅ All 9 notebooks have try/except fallback patterns
- ✅ Settings returns correct Fabric paths: `/lakehouse/default/Files/Bronze` (capitalized)
- ✅ Wheel contents in sync with source files
- ✅ End-to-end import tests pass for both Local and Fabric environments
- ✅ `fabric_paths` section in YAML correctly defines: Bronze, Silver, Gold

### Technical Details
- **Wheel**: `aims_data_platform-1.3.1-py3-none-any.whl` (68K)
- **Config Search Order**:
  1. `/lakehouse/default/Files/notebooks/config/notebook_settings.yaml`
  2. Package location (relative to settings.py)
  3. Current working directory
  4. Project root
  5. `importlib.resources` from wheel
  6. Hardcoded `_get_default_config()` fallback

---

## [1.4.0] - 2026-01-19

### Added - Landing Zone Management & Complete Overwrite Strategy

#### Landing Zone Architecture
- **\`LandingZoneManager\`** - Full lifecycle management for SFTP file ingestion
- **\`PlatformFileOps\`** - Cross-platform file operations (Local + MS Fabric)
- **\`NotificationManager\`** - Teams webhook and SMTP email notifications
- **\`RunSummary\`** - Dataclass for run metadata and notification content
- **\`create_landing_zone_manager()\`** - Factory function with auto-detection

#### Complete Overwrite Strategy
- **No append/delta behavior** - Each pipeline run produces fresh data
- **Raw files archived** - Date-stamped folders in \`archive/YYYY-MM-DD_run_xxx/\`
- **Silver cleared before write** - Ensures no residual data accumulation
- **Platform-aware removal** - Uses \`mssparkutils.fs.rm()\` on Fabric, \`shutil\` locally

#### New Methods
- **\`StorageManager.clear_layer()\`** - Platform-aware layer clearing
- **\`PlatformFileOps.remove_directory()\`** - Cross-platform directory removal
- **\`LandingZoneManager.archive_landing_files()\`** - Archive with metadata

### Changed

#### Pipeline Flow (Complete Overwrite)
\`\`\`
SFTP Drop → landing/ → COPY to Bronze/ → Validate → Silver/
                ↓
           archive/YYYY-MM-DD_run_xxx/
                ↓
           Landing zone cleared ✅
\`\`\`

#### Platform Detection Enhanced
- Triple-check before Fabric operations: \`is_fabric\` AND \`mssparkutils available\` AND \`is_fabric_path\`
- Path detection recognizes: \`abfss://\`, \`/lakehouse/\`, \`lakehouse/\`
- Graceful fallback to local operations if mssparkutils unavailable

#### run_full_pipeline.py
- Added \`--fabric\` flag for testing Fabric mode locally
- Uses \`PlatformFileOps\` for Silver clearing
- Phase 0: Landing → Bronze (if files present)
- Phase 3: Archive & Notify with cleanup

### Fixed
- **\`mssparkutils.fs.mv()\`** - Removed unsupported \`recurse\` parameter
- **\`is_directory()\`** - Replaced \`isDirectory()\` with \`fs.ls()\` + \`isDir\` attribute check
- **\`clear_layer()\`** - Now platform-aware for Fabric paths
- **\`_write_parquet()\`** - Uses \`mssparkutils.fs.rm()\` for Fabric overwrite

### Technical Details
- **Version**: 1.4.0
- **Commits**: 3e60be0, 9d09553, 9421550, a006de0, 29bf503
- **Tests**: 74/74 passing (100%)
- **Pipeline Duration**: ~60 seconds

---

## [1.3.0] - 2026-01-19

### Added - Comprehensive Notebook Refactoring

#### New Shared Utility Library (\`notebooks/lib/\`)
- **\`platform_utils.py\`** - Platform detection (IS_FABRIC), base directory resolution, safe parquet reading
- **\`storage.py\`** - StorageManager class for medallion architecture (Bronze/Silver/Gold) with platform-aware writes
- **\`settings.py\`** - Singleton Settings class for centralized configuration management
- **\`logging_utils.py\`** - Structured logging with timed operations and notebook-specific logger setup
- **\`config.py\`** - Configuration loading and environment variable management

#### New Configuration System (\`notebooks/config/\`)
- **\`notebook_settings.yaml\`** - Environment-specific settings (local vs Fabric)
- Centralized DQ thresholds, paths, and pipeline phase configuration
- Automatic environment detection and path resolution

#### Orchestration Notebook (\`00_AIMS_Orchestration.ipynb\`)
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
- \`AttributeError: 'Settings' object has no attribute 'results_dir'\` → Use \`validation_results_dir\`
- Duplicate cell outputs in orchestration notebook cleaned up
- Consistent path handling across all notebooks

### Verified
- ✅ Full pipeline execution: 68 files processed, 0 runtime errors
- ✅ Test suite: 74/74 tests passing
- ✅ CLI commands working correctly
- ✅ Orchestration notebook: All 3 phases complete in ~72 seconds
- ✅ StorageManager: Successfully ingested 50 files to Silver layer

### Technical Details
- **Version Tag**: \`v1.3.0\`
- **Safety Rollback**: \`git checkout v1.2.0-pre-notebook-refactor\`
- **Python**: 3.11.14 in \`aims_data_platform\` conda environment

---

## [1.2.0] - 2026-01-18

### Added
- Pre-notebook refactor checkpoint (tag: \`v1.2.0-pre-notebook-refactor\`)
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
