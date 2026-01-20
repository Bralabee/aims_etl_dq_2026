# AIMS Data Platform

![CI Status](https://github.com/Bralabee/aims_etl_dq_2026/actions/workflows/ci-cd.yml/badge.svg)
![Azure DevOps](https://dev.azure.com/{org}/AIMS-Data-Platform/_apis/build/status/aims-pipeline)
![Test Coverage](https://img.shields.io/badge/tests-74%2F74%20passing-brightgreen)
![DQ Pass Rate](https://img.shields.io/badge/DQ%20validation-73.5%25-yellow)
![Production Ready](https://img.shields.io/badge/production%20ready-90%25-green)

# AIMS Data Platform - Local Development Environment

**Version:** 1.3.1  
**Status:** Production Ready - Dual Platform Support (Local + MS Fabric)  
**Last Updated:** 2026-01-20

A comprehensive, governed data ingestion platform designed for SFTP-based file ingestion, data quality validation via Great Expectations, dual CLI/Notebook functionality, and seamless integration with Microsoft Fabric.

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Bronze Tables** | 68 |
| **DQ Configs Generated** | 68 |
| **Validation Pass Rate** | 73.5% (50/68) |
| **Average Quality Score** | 98.8% |
| **Test Suite** | 74/74 passing (100%) |
| **Notebooks Validated** | 9/9 passing (100%) |
| **Documentation** | 180+ pages |
| **CI/CD Pipelines** | Azure DevOps + GitHub Actions |
| **Platform Support** | Local + Microsoft Fabric |

## 🆕 What's New in v1.4.0

### Landing Zone Architecture
- **SFTP Integration** - Weekly file drops to landing zone
- **Auto-Archive** - Processed files archived with date stamps
- **Complete Overwrite** - No delta/append, fresh data each run
- **Notifications** - Teams webhook and email support

### Dual Platform Support
- **Platform Detection** - Auto-detects Local vs MS Fabric environment
- **Cross-Platform Ops** - \`PlatformFileOps\` class for file operations
- **Fabric API Compatible** - Uses \`mssparkutils.fs\` for lakehouse paths

## Key Features

- ✅ **Landing Zone Management** - SFTP drop → archive flow with notifications
- ✅ **Complete Overwrite Strategy** - No residual data, fresh runs each time
- ✅ **Dual Platform** - Seamless Local ↔ MS Fabric operation
- ✅ **Dual Functionality** - Complete CLI scripts AND interactive Jupyter notebooks
- ✅ **Incremental Loading** - Watermark-based incremental data ingestion
- ✅ **Data Quality** - Great Expectations validation (68 configs, 98.8% avg score)
- ✅ **Automated Profiling** - Auto-generates DQ configs via \`fabric_data_quality\`
- ✅ **Medallion Architecture** - Bronze → Silver → Gold layer transformation
- ✅ **CI/CD Integration** - Azure DevOps and GitHub Actions workflows
- ✅ **Governance** - Full audit trail with load history and watermarks
- ✅ **Production Ready** - 90% deployment ready with comprehensive testing

## 🔄 Data Flow

\`\`\`mermaid
flowchart TD
    SFTP[SFTP Server] -->|Weekly fetch| LZ[landing/]
    LZ -->|Copy| BRONZE[Bronze/]
    BRONZE -->|Validate| SILVER[Silver/]
    LZ -->|Archive| ARCH[archive/YYYY-MM-DD/]
    SILVER -->|Transform| GOLD[Gold/]
\`\`\`

**Pipeline Phases:**
1. **Phase 0**: Landing → Bronze (if files present)
2. **Phase 1**: Data Profiling (68 files, ~7.5s)
3. **Phase 2**: Validation & Silver Ingestion (50/68 passed)
4. **Phase 3**: Archive, Cleanup & Notify

## 🚀 Quick Start (5 Minutes)

\`\`\`bash
# 1. Navigate to project
cd /home/sanmi/Documents/HS2/HS2_PROJECTS_2025/1_AIMS_LOCAL_2026

# 2. Activate environment
conda activate aims_data_platform

# 3. Run full pipeline
python scripts/run_full_pipeline.py --skip-profiling

# Expected output:
# ✅ 50/68 passing (73.5%)
# ✅ Archive created
# ✅ Landing zone cleared
\`\`\`

### Pipeline Options

\`\`\`bash
# Full pipeline with all phases
python scripts/run_full_pipeline.py

# Skip profiling (faster)
python scripts/run_full_pipeline.py --skip-profiling

# Dry run (no archive/notifications)
python scripts/run_full_pipeline.py --dry-run

# Custom threshold
python scripts/run_full_pipeline.py --threshold 90.0

# Force Fabric mode (testing)
python scripts/run_full_pipeline.py --fabric

# Disable notifications
python scripts/run_full_pipeline.py --no-notify
\`\`\`

## 📁 Project Structure

\`\`\`
AIMS_LOCAL/
├── aims_data_platform/           # Core package
│   ├── landing_zone_manager.py   # 🆕 Landing zone + archival
│   ├── ingestion.py              # Data ingestion logic
│   ├── config.py                 # Configuration management
│   └── watermark_manager.py      # Watermark tracking
├── notebooks/                    # Jupyter notebooks (00-08)
│   ├── lib/                      # Shared utilities
│   │   ├── platform_utils.py     # Platform detection
│   │   ├── storage.py            # StorageManager (Bronze/Silver/Gold)
│   │   ├── settings.py           # Centralized config
│   │   └── logging_utils.py      # Logging setup
│   └── config/
│       └── notebook_settings.yaml
├── scripts/
│   ├── run_full_pipeline.py      # 🆕 Full pipeline orchestrator
│   └── run_validation_simple.py  # Simple validation
├── data/
│   ├── landing/                  # 🆕 SFTP drop zone
│   ├── archive/                  # 🆕 Date-stamped archives
│   ├── Samples_LH_Bronze_*/      # Bronze layer
│   ├── Silver/                   # Silver layer (validated)
│   └── Gold/                     # Gold layer (analytics-ready)
├── config/
│   └── data_quality/             # 68 DQ validation configs
└── docs/                         # 180+ pages documentation
\`\`\`

## 🔧 Landing Zone Management

### How It Works

1. **SFTP drops files** to \`data/landing/\`
2. **Pipeline discovers** files via \`list_landing_files()\`
3. **Files copied** to Bronze for processing
4. **Validation runs** with Great Expectations
5. **Valid data** written to Silver (complete overwrite)
6. **Original files archived** to \`archive/YYYY-MM-DD_run_xxx/\`
7. **Landing cleared** for next SFTP fetch
8. **Notifications sent** via Teams/Email

### Archive Contents

\`\`\`
archive/2026-01-19_run_20260119_152807/
├── aims_assets.parquet           # Original file
├── aims_attributes.parquet       # Original file
├── _run_metadata.json            # Files list, errors, platform
└── _run_summary.json             # DQ stats, pass rate
\`\`\`

### Configuration

\`\`\`python
from aims_data_platform import create_landing_zone_manager

manager = create_landing_zone_manager(
    teams_webhook_url="https://outlook.office.com/webhook/...",
    email_config={
        "smtp_server": "smtp.office365.com",
        "email_from": "data-platform@company.com",
        "email_to": ["team@company.com"]
    }
)
\`\`\`

## 🌐 Platform Support

### Auto-Detection

The platform automatically detects the runtime environment:

| Environment | Detection | Path Format |
|-------------|-----------|-------------|
| **Local** | Default | \`/home/user/project/data/\` |
| **MS Fabric** | \`/lakehouse/default/Files\` exists | \`/lakehouse/default/Files/\` or \`abfss://\` |

### Platform-Aware Operations

\`\`\`python
from aims_data_platform import PlatformFileOps, IS_FABRIC

# Auto-detected operations
ops = PlatformFileOps()
ops.copy_file(src, dst)      # Uses mssparkutils on Fabric
ops.move_file(src, dst)      # Uses mssparkutils on Fabric
ops.remove_directory(path)   # Uses mssparkutils.fs.rm on Fabric
\`\`\`

### Fabric Deployment

See [docs/02_Fabric_Migration/](docs/02_Fabric_Migration/) for:
- Notebook upload instructions
- Lakehouse configuration
- mssparkutils API reference
- Environment variable setup

## 📚 Documentation

### 🎯 Start Here
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Get started in 5 minutes
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[docs/pipeline_flow.md](docs/pipeline_flow.md)** - Visual pipeline diagram

### 🔧 Implementation Guides
- **[docs/03_Implementation_Guides/LANDING_ZONE_MANAGEMENT.md](docs/03_Implementation_Guides/LANDING_ZONE_MANAGEMENT.md)** - Landing zone setup
- **[docs/03_Implementation_Guides/ORCHESTRATION_GUIDE.md](docs/03_Implementation_Guides/ORCHESTRATION_GUIDE.md)** - Pipeline orchestration
- **[docs/02_Fabric_Migration/FABRIC_DEPLOYMENT_GUIDE.md](docs/02_Fabric_Migration/FABRIC_DEPLOYMENT_GUIDE.md)** - MS Fabric deployment

### 📖 Reference
- **[notebooks/README.md](notebooks/README.md)** - Notebook documentation
- **[notebooks/lib/README.md](notebooks/lib/README.md)** - Shared library reference

## 🧪 Testing

\`\`\`bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=aims_data_platform --cov-report=html

# Expected: 74/74 passing (100%)
\`\`\`

## 📈 Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | 100% (74/74) | ≥95% |
| DQ Pass Rate | 73.5% | ≥85% |
| Avg Quality Score | 98.8% | ≥95% |
| Pipeline Duration | ~60s | <120s |
| Documentation | 180+ pages | Complete |

## 🔐 Security

- No credentials stored in code
- Environment variables for sensitive config
- Teams webhook URLs via environment
- SMTP credentials via secure config

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Proprietary - HS2

## 🆘 Support

For issues or questions, contact the HS2 Data Team.

---

**Built with ❤️ for HS2 Data Platform Team**
