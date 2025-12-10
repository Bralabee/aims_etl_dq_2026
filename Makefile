.PHONY: help setup init repair validate ingest clean test format profile adjust-thresholds validate-dq run-orchestration run-notebooks dq-pipeline data-pipeline pipeline

help:
	@echo "AIMS Data Platform - Make Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup           - Setup conda environment and dependencies"
	@echo "  make init            - Initialize the data platform"
	@echo ""
	@echo "Data Quality Operations:"
	@echo "  make profile         - Profile Bronze layer & generate DQ configs (68 tables)"
	@echo "  make adjust-thresholds - Adjust DQ thresholds to 95%"
	@echo "  make validate-dq     - Run DQ validation pipeline on Bronze layer"
	@echo "  make dq-pipeline     - Full DQ pipeline (profile → adjust → validate)"
	@echo ""
	@echo "Data Operations:"
	@echo "  make repair          - Repair corrupted parquet files"
	@echo "  make validate        - Validate source files"
	@echo "  make ingest-all      - Ingest all data sources"
	@echo "  make ingest-assets   - Ingest aims_assets only"
	@echo "  make ingest-attrs    - Ingest aims_attributes only"
	@echo "  make data-pipeline   - Full data pipeline (init → repair → validate → ingest)"
	@echo ""
	@echo "Notebook Operations:"
	@echo "  make run-orchestration - Run orchestration notebook (00_AIMS_Orchestration)"
	@echo "  make run-notebooks   - Run all AIMS notebooks sequentially (01-08)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make watermarks      - List all watermarks"
	@echo "  make history         - Show load history"
	@echo ""
	@echo "Pipelines:"
	@echo "  make pipeline        - Complete end-to-end (DQ + Data)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           - Clean generated files"
	@echo "  make test            - Run tests"
	@echo "  make format          - Format code"

setup:
	@echo "Setting up environment..."
	@bash setup.sh

init:
	@echo "Initializing platform..."
	@python -m aims_data_platform.cli init

repair:
	@echo "Repairing parquet files..."
	@python -m aims_data_platform.cli repair

validate:
	@echo "Validating source files..."
	@python -m aims_data_platform.cli validate-source

ingest-assets:
	@echo "Ingesting aims_assets..."
	@python -m aims_data_platform.cli ingest aims_assets --watermark-column LASTUPDATED

ingest-attrs:
	@echo "Ingesting aims_attributes..."
	@python -m aims_data_platform.cli ingest aims_attributes --watermark-column LASTUPDATED

ingest-all: ingest-assets ingest-attrs
	@echo "All data sources ingested!"

watermarks:
	@python -m aims_data_platform.cli list-watermarks

history:
	@python -m aims_data_platform.cli load-history --limit 20

clean:
	@echo "Cleaning generated files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

test:
	@echo "Running tests..."
	@pytest tests/ -v

format:
	@echo "Formatting code..."
	@black aims_data_platform/
	@ruff check aims_data_platform/ --fix
	@echo "Format complete!"

# DQ profiling - Generate validation configs for all Bronze tables
profile:
	@echo "📊 Profiling Bronze layer and generating DQ configs..."
	@python scripts/profile_aims_parquet.py
	@echo "Profiling complete!"

# Adjust DQ thresholds
adjust-thresholds:
	@echo "⚙️ Adjusting DQ thresholds to 95%..."
	@python scripts/adjust_thresholds.py --threshold 95
	@echo "Thresholds adjusted!"

# Run DQ validation on Bronze layer
validate-dq:
	@echo "✅ Running DQ validation pipeline..."
	@python scripts/run_validation_simple.py
	@echo "Validation complete!"

# Run orchestration notebook (requires jupyter)
run-orchestration:
	@echo "🚀 Running orchestration notebook..."
	@jupyter nbconvert --execute --to notebook --inplace notebooks/00_AIMS_Orchestration.ipynb
	@echo "Orchestration complete!"

# Run all notebooks sequentially (requires jupyter)
run-notebooks:
	@echo "📓 Running all AIMS notebooks..."
	@jupyter nbconvert --execute --to notebook --inplace notebooks/01_AIMS_Data_Profiling.ipynb
	@jupyter nbconvert --execute --to notebook --inplace notebooks/02_AIMS_Data_Ingestion.ipynb
	@jupyter nbconvert --execute --to notebook --inplace notebooks/03_AIMS_Monitoring.ipynb
	@jupyter nbconvert --execute --to notebook --inplace notebooks/07_AIMS_DQ_Matrix_and_Modeling.ipynb
	@jupyter nbconvert --execute --to notebook --inplace notebooks/08_AIMS_Business_Intelligence.ipynb
	@echo "All notebooks executed!"

# Full DQ pipeline: profile -> adjust -> validate
dq-pipeline: profile adjust-thresholds validate-dq
	@echo "✅ Full DQ pipeline completed!"

# Full data pipeline: init -> repair -> validate -> ingest
data-pipeline: init repair validate ingest-all
	@echo "✅ Full data pipeline completed!"

# Complete end-to-end pipeline: DQ + Data
pipeline: dq-pipeline data-pipeline
	@echo "✅ Complete end-to-end pipeline finished!"
