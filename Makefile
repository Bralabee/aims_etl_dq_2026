.PHONY: help setup init repair validate ingest clean test format

help:
	@echo "AIMS Data Platform - Make Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup      - Setup conda environment and dependencies"
	@echo "  make init       - Initialize the data platform"
	@echo ""
	@echo "Data Operations:"
	@echo "  make repair     - Repair corrupted parquet files"
	@echo "  make validate   - Validate source files"
	@echo "  make ingest-all - Ingest all data sources"
	@echo "  make ingest-assets - Ingest aims_assets only"
	@echo "  make ingest-attrs  - Ingest aims_attributes only"
	@echo ""
	@echo "Monitoring:"
	@echo "  make watermarks - List all watermarks"
	@echo "  make history    - Show load history"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Clean generated files"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code"

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

# Full pipeline
pipeline: init repair validate ingest-all
	@echo "Full pipeline complete!"
