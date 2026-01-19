"""
Test script to validate notebook imports.
Run with: python test_nb_imports.py
"""
import sys
from pathlib import Path

# Ensure we can import from notebooks
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all new utilities can be imported correctly."""
    errors = []
    
    # Test 1: Import settings
    try:
        from notebooks.config import settings
        print(f"✅ notebooks.config.settings imported successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Bronze dir: {settings.bronze_dir}")
        print(f"   Config dir: {settings.config_dir}")
        print(f"   State dir: {settings.state_dir}")
    except Exception as e:
        errors.append(f"❌ Failed to import notebooks.config: {e}")
    
    # Test 2: Import platform_utils
    try:
        from notebooks.lib import platform_utils
        print(f"✅ notebooks.lib.platform_utils imported successfully")
        print(f"   IS_FABRIC: {platform_utils.IS_FABRIC}")
    except Exception as e:
        errors.append(f"❌ Failed to import platform_utils: {e}")
    
    # Test 3: Import logging_utils
    try:
        from notebooks.lib import logging_utils
        print(f"✅ notebooks.lib.logging_utils imported successfully")
    except Exception as e:
        errors.append(f"❌ Failed to import logging_utils: {e}")
    
    # Test 4: Import StorageManager
    try:
        from notebooks.lib.storage import StorageManager
        print(f"✅ notebooks.lib.storage.StorageManager imported successfully")
    except Exception as e:
        errors.append(f"❌ Failed to import StorageManager: {e}")
    
    # Test 5: Test specific attributes
    try:
        from notebooks.config import settings
        # Test path accessors
        assert settings.bronze_dir is not None
        assert settings.silver_dir is not None
        assert settings.state_dir is not None
        assert settings.config_dir is not None
        print(f"✅ Settings path attributes work correctly")
    except Exception as e:
        errors.append(f"❌ Settings path attributes failed: {e}")
    
    # Test 6: Test file_exists from platform_utils
    try:
        from notebooks.lib.platform_utils import file_exists
        result = file_exists(__file__)
        assert result is True, "file_exists should return True for existing file"
        print(f"✅ platform_utils.file_exists works correctly")
    except Exception as e:
        errors.append(f"❌ platform_utils.file_exists failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  {err}")
        return False
    else:
        print("✅ ALL IMPORTS VALIDATED SUCCESSFULLY")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
