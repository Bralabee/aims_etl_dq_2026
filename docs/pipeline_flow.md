# AIMS Data Pipeline Flow

This diagram shows the complete data flow from SFTP ingestion through to archive.

```mermaid
flowchart TD
    subgraph External["External Source"]
        SFTP[("🔄 SFTP Server")]
    end

    subgraph Landing["Landing Zone"]
        LZ[("📥 landing/")]
    end

    subgraph Pipeline["Data Pipeline"]
        START((▶ Pipeline Start))
        LIST["list_landing_files()<br/>Discover *.parquet files"]
        COPY["move_landing_to_bronze()<br/><b>COPIES</b> files to Bronze"]
        VALIDATE["Validation Engine<br/>Great Expectations DQ checks"]
        WRITE["Write valid data<br/>to Silver layer"]
        ARCHIVE["archive_landing_files()<br/><b>MOVES</b> files to archive"]
        END((✅ Complete))
    end

    subgraph Storage["Data Lakehouse"]
        BRONZE[("🥉 Bronze/<br/>Raw Data")]
        SILVER[("🥈 Silver/<br/>Validated Data")]
        ARCH[("📦 archive/<br/>YYYY-MM-DD_run_xxx/")]
    end

    subgraph Artifacts["Archive Contents"]
        META["_run_metadata.json<br/>files, errors, platform"]
        SUMMARY["_run_summary.json<br/>DQ stats, pass rate"]
    end

    %% Flow
    SFTP -->|"Weekly fetch"| LZ
    LZ --> START
    START --> LIST
    LIST -->|"Files found"| COPY
    COPY -->|"Copy"| BRONZE
    BRONZE --> VALIDATE
    VALIDATE -->|"Valid rows"| WRITE
    WRITE --> SILVER
    VALIDATE -->|"After processing"| ARCHIVE
    ARCHIVE -->|"Move originals"| ARCH
    ARCH --- META
    ARCH --- SUMMARY
    ARCHIVE --> END

    %% Styling
    style SFTP fill:#4a90d9,stroke:#2d5a87,color:#fff
    style LZ fill:#f9c74f,stroke:#c9a227,color:#000
    style BRONZE fill:#cd7f32,stroke:#8b5a2b,color:#fff
    style SILVER fill:#c0c0c0,stroke:#808080,color:#000
    style ARCH fill:#90EE90,stroke:#228B22,color:#000
    style START fill:#28a745,stroke:#1e7b34,color:#fff
    style END fill:#28a745,stroke:#1e7b34,color:#fff
    style COPY fill:#17a2b8,stroke:#117a8b,color:#fff
    style ARCHIVE fill:#17a2b8,stroke:#117a8b,color:#fff
    style META fill:#e9ecef,stroke:#6c757d
    style SUMMARY fill:#e9ecef,stroke:#6c757d
```

## Key Points

| Step | Action | Method |
|------|--------|--------|
| 1 | SFTP drops files | External process |
| 2 | Discover files | `list_landing_files()` |
| 3 | **COPY** to Bronze | `move_landing_to_bronze()` |
| 4 | Validate data | Great Expectations |
| 5 | Write to Silver | Spark DataFrame |
| 6 | **MOVE** to archive | `archive_landing_files()` |
| 7 | Landing cleared | Ready for next fetch |

> **Important**: Files are **copied** to Bronze first, then **moved** to archive. This ensures Bronze always has data for processing while originals are preserved in dated archive folders.
