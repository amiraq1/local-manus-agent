"""Tests for model import functionality."""
import hashlib
import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.model_import import (
    start_import,
    receive_chunk,
    finish_import,
    cancel_import,
    get_import_status,
    IMPORTED_DIR,
    UPLOADS_DIR,
    _active_imports,
)


def _cleanup():
    """Clean up test artifacts."""
    _active_imports.clear()
    # Clean test files from imported dir
    for f in IMPORTED_DIR.glob("test_*"):
        f.unlink(missing_ok=True)
    # Clean upload dirs
    for d in UPLOADS_DIR.iterdir():
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)


def test_import_small_litertlm():
    """Test importing a small fake .litertlm file."""
    _cleanup()

    # Start import
    result = start_import("test_model.litertlm", 1024, "Test Model")
    assert result["accepted"] is True
    assert "import_id" in result
    assert result["total_chunks"] == 1

    import_id = result["import_id"]

    # Upload single chunk
    fake_data = b"FAKE_LITERT_MODEL_DATA" * 50  # ~1KB
    chunk_result = receive_chunk(import_id, 0, fake_data)
    assert chunk_result["success"] is True
    assert chunk_result["received"] == 1

    # Finish
    finish_result = finish_import(import_id)
    assert finish_result["success"] is True
    assert finish_result["sha256"] == hashlib.sha256(fake_data).hexdigest()
    assert "model_id" in finish_result
    assert finish_result["path"].endswith("test_model.litertlm")

    # Verify file exists
    assert Path(finish_result["path"]).exists()

    _cleanup()
    print("PASS: test_import_small_litertlm")


def test_reject_exe():
    """Test that .exe files are rejected."""
    result = start_import("malware.exe", 5000)
    assert result["accepted"] is False
    assert "Only .litertlm" in result["error"]
    print("PASS: test_reject_exe")


def test_reject_bat():
    """Test that .bat files are rejected."""
    result = start_import("script.bat", 5000)
    assert result["accepted"] is False
    print("PASS: test_reject_bat")


def test_reject_path_traversal():
    """Test that path traversal is sanitized - the basename is used safely."""
    _cleanup()

    # Path with ../ gets sanitized to just the basename
    result = start_import("../../../etc/passwd.litertlm", 5000)
    # The sanitizer strips path components, so it accepts with safe name
    assert result["accepted"] is True
    assert result["filename"] == "passwd.litertlm"
    # Clean up
    cancel_import(result["import_id"])

    # Filename with .. in it should be rejected by sanitizer
    result2 = start_import("..bad.litertlm", 5000)
    assert result2["accepted"] is False

    _cleanup()
    print("PASS: test_reject_path_traversal")


def test_reject_dotdot_in_name():
    """Test that .. in filename is rejected."""
    result = start_import("..bad.litertlm", 5000)
    # Contains ".." so sanitizer rejects it
    assert result["accepted"] is False
    print("PASS: test_reject_dotdot_in_name")


def test_reject_oversized():
    """Test that files over 8GB are rejected."""
    result = start_import("huge.litertlm", 9 * 1024 * 1024 * 1024)
    assert result["accepted"] is False
    assert "too large" in result["error"]
    print("PASS: test_reject_oversized")


def test_chunk_upload_multi():
    """Test multi-chunk upload."""
    _cleanup()

    # 150MB file = 3 chunks of 50MB
    file_size = 150 * 1024 * 1024
    result = start_import("test_large.litertlm", file_size, "Large Model")
    assert result["accepted"] is True
    assert result["total_chunks"] == 3

    import_id = result["import_id"]

    # Upload 3 chunks
    chunks = []
    for i in range(3):
        chunk_data = bytes([i % 256]) * (50 * 1024 * 1024)
        chunks.append(chunk_data)
        chunk_result = receive_chunk(import_id, i, chunk_data)
        assert chunk_result["success"] is True
        assert chunk_result["received"] == i + 1

    # Check status
    status = get_import_status(import_id)
    assert status["progress"] == 100
    assert status["received_chunks"] == 3

    # Finish
    finish_result = finish_import(import_id)
    assert finish_result["success"] is True

    # Verify sha256
    expected_hash = hashlib.sha256()
    for c in chunks:
        expected_hash.update(c)
    assert finish_result["sha256"] == expected_hash.hexdigest()

    # Verify file size
    assert finish_result["size"] == file_size

    _cleanup()
    print("PASS: test_chunk_upload_multi")


def test_cancel_import():
    """Test cancelling an import."""
    _cleanup()

    result = start_import("test_cancel.litertlm", 1024)
    assert result["accepted"] is True
    import_id = result["import_id"]

    # Cancel
    cancel_result = cancel_import(import_id)
    assert cancel_result["success"] is True

    # Verify session is gone
    status = get_import_status(import_id)
    assert "error" in status

    _cleanup()
    print("PASS: test_cancel_import")


def test_imported_model_registered():
    """Test that imported model appears in user config."""
    _cleanup()

    from app.user_config_manager import load_user_config

    result = start_import("test_reg.litertlm", 100, "Registered Model")
    import_id = result["import_id"]
    receive_chunk(import_id, 0, b"MODEL_DATA_FOR_REG_TEST")
    finish_result = finish_import(import_id)
    assert finish_result["success"] is True

    # Check user config
    cfg = load_user_config()
    imported = cfg.get("imported_models", [])
    found = any(m["id"] == finish_result["model_id"] for m in imported)
    assert found, "Imported model not found in user_config"

    _cleanup()
    print("PASS: test_imported_model_registered")


if __name__ == "__main__":
    test_reject_exe()
    test_reject_bat()
    test_reject_path_traversal()
    test_reject_dotdot_in_name()
    test_reject_oversized()
    test_import_small_litertlm()
    test_cancel_import()
    test_imported_model_registered()
    # Skip multi-chunk test in quick runs (allocates 150MB)
    # test_chunk_upload_multi()
    print("\n✅ All model import tests passed!")
