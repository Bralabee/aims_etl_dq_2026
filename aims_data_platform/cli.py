"""Main CLI application for AIMS data platform."""
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import logging

from .config import config
from .watermark_manager import WatermarkManager
from .ingestion import DataIngester
from .data_quality import DataQualityValidator

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="AIMS Data Platform - Federated, governed data ingestion with Great Expectations"
)
console = Console()


@app.command()
def init():
    """Initialize the data platform (create directories, databases, etc.)."""
    rprint("[bold blue]Initializing AIMS Data Platform...[/bold blue]")
    
    try:
        # Create directories
        config.ensure_directories()
        rprint("✓ Created necessary directories")
        
        # Initialize watermark manager
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        rprint("✓ Initialized watermark database")
        
        # Display configuration
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.get_config_dict().items():
            table.add_row(key, str(value))
        
        console.print(table)
        
        rprint("[bold green]✓ Initialization complete![/bold green]")
        
    except Exception as e:
        rprint(f"[bold red]✗ Initialization failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def repair(
    source_dir: Path = typer.Option(
        None,
        help="Source directory (defaults to config SOURCE_DATA_PATH)"
    ),
    output_dir: Path = typer.Option(
        None,
        help="Output directory (defaults to config REPAIRED_DATA_PATH)"
    )
):
    """Repair corrupted parquet files."""
    source_dir = source_dir or config.SOURCE_DATA_PATH
    output_dir = output_dir or config.REPAIRED_DATA_PATH
    
    rprint(f"[bold blue]Repairing parquet files...[/bold blue]")
    rprint(f"Source: {source_dir}")
    rprint(f"Output: {output_dir}")
    
    try:
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        ingester = DataIngester(watermark_mgr, engine="fastparquet")
        
        results = ingester.repair_directory(source_dir, output_dir)
        
        # Display results
        table = Table(title="Repair Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Files", str(results["total_files"]))
        table.add_row("Successful", str(results["successful"]))
        table.add_row("Failed", str(results["failed"]))
        
        console.print(table)
        
        if results["successful"] > 0:
            rprint("[bold green]✓ Repair complete![/bold green]")
        else:
            rprint("[bold red]✗ No files could be repaired[/bold red]")
            raise typer.Exit(code=1)
        
    except Exception as e:
        rprint(f"[bold red]✗ Repair failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def validate_source(
    source_dir: Path = typer.Option(
        None,
        help="Source directory to validate"
    )
):
    """Validate source parquet files."""
    source_dir = source_dir or config.SOURCE_DATA_PATH
    
    rprint(f"[bold blue]Validating source files in: {source_dir}[/bold blue]")
    
    try:
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        ingester = DataIngester(watermark_mgr, engine="fastparquet")
        
        results = ingester.validate_source_files(source_dir)
        
        # Display results
        table = Table(title="Validation Results")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Rows", justify="right")
        table.add_column("Size (MB)", justify="right")
        
        for file_info in results["file_info"]:
            status_color = "green" if file_info["status"] == "valid" else "red"
            table.add_row(
                file_info["file"],
                f"[{status_color}]{file_info['status']}[/{status_color}]",
                f"{file_info.get('rows', 'N/A'):,}" if 'rows' in file_info else "N/A",
                f"{file_info['size_mb']:.2f}"
            )
        
        console.print(table)
        
        rprint(f"\n[bold]Summary:[/bold] {results['valid']} valid, {results['corrupted']} corrupted")
        
    except Exception as e:
        rprint(f"[bold red]✗ Validation failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def ingest(
    source_name: str = typer.Argument(..., help="Name of the data source"),
    source_path: Path = typer.Option(
        None,
        help="Path to source directory or file"
    ),
    watermark_column: str = typer.Option(
        None,
        help="Column to use as watermark"
    ),
    validate: bool = typer.Option(
        True,
        help="Run data quality validation"
    )
):
    """Ingest data incrementally."""
    source_path = source_path or config.REPAIRED_DATA_PATH
    watermark_column = watermark_column or config.DEFAULT_WATERMARK_COLUMN
    
    rprint(f"[bold blue]Ingesting data: {source_name}[/bold blue]")
    rprint(f"Source: {source_path}")
    rprint(f"Watermark column: {watermark_column}")
    
    try:
        # Initialize components
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        ingester = DataIngester(watermark_mgr, engine="fastparquet")
        
        # Get source files
        if source_path.is_dir():
            source_files = list(source_path.glob(f"*{source_name}*.parquet"))
        else:
            source_files = [source_path]
        
        if not source_files:
            rprint(f"[bold red]✗ No source files found[/bold red]")
            raise typer.Exit(code=1)
        
        rprint(f"Found {len(source_files)} source file(s)")
        
        # Ingest
        result = ingester.ingest_incremental(
            source_name=source_name,
            source_files=source_files,
            target_path=config.TARGET_DATA_PATH,
            watermark_column=watermark_column
        )
        
        # Display results
        table = Table(title="Ingestion Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in result.items():
            table.add_row(key, str(value))
        
        console.print(table)
        
        # Validate if requested
        if validate and result["status"] == "success":
            rprint("\n[bold blue]Running data quality validation...[/bold blue]")
            
            validator = DataQualityValidator()
            import pandas as pd
            df = pd.read_parquet(result["target_file"])
            
            validation_results = validator.validate_dataframe(
                df,
                suite_name=source_name
            )
            
            rprint(
                f"Validation: {validation_results['statistics']['success_percent']:.1f}% passed"
            )
        
        if result["status"] == "success":
            rprint("[bold green]✓ Ingestion complete![/bold green]")
        else:
            rprint(f"[bold yellow]⚠ {result['status']}[/bold yellow]")
        
    except Exception as e:
        rprint(f"[bold red]✗ Ingestion failed: {e}[/bold red]")
        logger.exception("Ingestion error")
        raise typer.Exit(code=1)


@app.command()
def list_watermarks():
    """List all watermarks."""
    rprint("[bold blue]Current Watermarks:[/bold blue]\n")
    
    try:
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        df = watermark_mgr.list_watermarks()
        
        if len(df) == 0:
            rprint("[yellow]No watermarks found[/yellow]")
            return
        
        table = Table()
        for col in df.columns:
            table.add_column(col, style="cyan")
        
        for _, row in df.iterrows():
            table.add_row(*[str(val) for val in row])
        
        console.print(table)
        
    except Exception as e:
        rprint(f"[bold red]✗ Failed to list watermarks: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def load_history(
    source_name: str = typer.Option(None, help="Filter by source name"),
    limit: int = typer.Option(10, help="Number of records to show")
):
    """Show load history."""
    rprint("[bold blue]Load History:[/bold blue]\n")
    
    try:
        watermark_mgr = WatermarkManager(config.WATERMARK_DB_PATH)
        df = watermark_mgr.get_load_history(source_name, limit)
        
        if len(df) == 0:
            rprint("[yellow]No load history found[/yellow]")
            return
        
        table = Table()
        for col in df.columns:
            table.add_column(col, style="cyan")
        
        for _, row in df.iterrows():
            table.add_row(*[str(val) for val in row])
        
        console.print(table)
        
    except Exception as e:
        rprint(f"[bold red]✗ Failed to get load history: {e}[/bold red]")
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
