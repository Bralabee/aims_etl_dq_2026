# Fabric API Compatibility Guide - v1.4.0

**Version:** 1.4.0  
**Last Updated:** 2026-01-19  
**Status:** Production Ready

This document describes the Fabric API compatibility fixes implemented in v1.4.0.

## 🔧 API Compatibility Issues Fixed

### 1. `mssparkutils.fs.mv()` - No `recurse` Parameter

**Issue:** The `fs.mv()` function in MS Fabric does NOT accept a `recurse` parameter.

**Before (Broken):**
```python
mssparkutils.fs.mv(src, dst, recurse=True)  # ERROR!
```

**After (Fixed):**
```python
mssparkutils.fs.mv(src, dst)  # Works correctly
```

**Affected Files:**
- `aims_data_platform/landing_zone_manager.py`

### 2. `isDirectory()` Method May Not Exist

**Issue:** File objects from `fs.ls()` may not have an `isDirectory()` method.

**Before (Broken):**
```python
for f in mssparkutils.fs.ls(path):
    if f.isDirectory():  # AttributeError on some files
        ...
```

**After (Fixed):**
```python
for f in mssparkutils.fs.ls(path):
    # Use isDir attribute instead
    is_dir = getattr(f, 'isDir', False) or getattr(f, 'isDirectory', lambda: False)()
    if callable(is_dir):
        is_dir = is_dir()
    ...
```

**Affected Files:**
- `aims_data_platform/landing_zone_manager.py`

### 3. `shutil.rmtree()` on Fabric Paths

**Issue:** Local `shutil.rmtree()` doesn't work on Fabric lakehouse paths.

**Before (Broken):**
```python
import shutil
shutil.rmtree(str(silver_dir / table_name))  # Fails on /lakehouse/default/Files
```

**After (Fixed):**
```python
from notebooks.lib.platform_utils import IS_FABRIC

if IS_FABRIC:
    from notebookutils import mssparkutils
    mssparkutils.fs.rm(path_str, recurse=True)
else:
    import shutil
    shutil.rmtree(path_str)
```

**Affected Files:**
- `notebooks/lib/storage.py` (`clear_layer()` method)
- `notebooks/lib/storage.py` (`_write_parquet()` method)

## 📦 Platform-Aware Classes

### PlatformFileOps

Located in `aims_data_platform/landing_zone_manager.py`:

```python
class PlatformFileOps:
    """Platform-aware file operations for Local and MS Fabric."""
    
    def __init__(self, is_fabric: bool = None):
        self.is_fabric = is_fabric if is_fabric is not None else IS_FABRIC
        if self.is_fabric:
            from notebookutils import mssparkutils
            self.fs = mssparkutils.fs
    
    def copy_file(self, src: str, dst: str) -> bool:
        """Copy file (platform-aware)."""
        if self.is_fabric:
            self.fs.cp(src, dst)
        else:
            shutil.copy2(src, dst)
        return True
    
    def move_file(self, src: str, dst: str) -> bool:
        """Move file (platform-aware)."""
        if self.is_fabric:
            self.fs.mv(src, dst)  # No recurse parameter!
        else:
            shutil.move(src, dst)
        return True
    
    def remove_directory(self, path: str) -> bool:
        """Remove directory recursively (platform-aware)."""
        if self.is_fabric:
            self.fs.rm(path, recurse=True)
        else:
            shutil.rmtree(path)
        return True
    
    def list_files(self, path: str) -> List[str]:
        """List files in directory (platform-aware)."""
        if self.is_fabric:
            files = []
            for f in self.fs.ls(path):
                is_dir = getattr(f, 'isDir', False)
                if callable(is_dir):
                    is_dir = is_dir()
                if not is_dir:
                    files.append(f.path)
            return files
        else:
            return [str(p) for p in Path(path).glob("*") if p.is_file()]
```

### StorageManager.clear_layer()

Located in `notebooks/lib/storage.py`:

```python
def clear_layer(self, layer: str) -> None:
    """
    Clear all data from a medallion layer (platform-aware).
    
    Args:
        layer: One of 'bronze', 'silver', 'gold'
    """
    layer_dir = self._get_layer_dir(layer)
    
    if IS_FABRIC:
        from notebookutils import mssparkutils
        for item in layer_dir.iterdir():
            if item.is_dir():
                mssparkutils.fs.rm(str(item), recurse=True)
            else:
                mssparkutils.fs.rm(str(item))
    else:
        import shutil
        for item in layer_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
```

## 🧪 Testing Fabric Compatibility

### Local Testing with Fabric Flag

```python
# Force Fabric mode for testing
python scripts/run_full_pipeline.py --fabric
```

### Verification Checklist

- [ ] `fs.mv()` calls have no `recurse` parameter
- [ ] `fs.rm()` calls DO have `recurse=True` parameter
- [ ] File listing uses `isDir` attribute, not `isDirectory()` method
- [ ] All path operations handle both `/lakehouse/...` and local paths
- [ ] `StorageManager.clear_layer()` uses platform detection

## 📋 Summary Table

| Operation | Local API | Fabric API | Notes |
|-----------|-----------|------------|-------|
| Copy file | `shutil.copy2()` | `fs.cp()` | - |
| Move file | `shutil.move()` | `fs.mv()` | **No recurse param** |
| Delete dir | `shutil.rmtree()` | `fs.rm(recurse=True)` | - |
| Delete file | `Path.unlink()` | `fs.rm()` | - |
| List files | `Path.glob()` | `fs.ls()` + `isDir` | **Use isDir attr** |
| Check exists | `Path.exists()` | N/A (use try/except) | - |

## 🔗 Related Documentation

- [FABRIC_DEPLOYMENT_GUIDE.md](FABRIC_DEPLOYMENT_GUIDE.md)
- [Landing Zone Management](../03_Implementation_Guides/LANDING_ZONE_MANAGEMENT.md)
- [CHANGELOG.md](../../CHANGELOG.md)
