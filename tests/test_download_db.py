"""
Testes para o utilitário de download e empacotamento do banco de dados (download_db.py).
"""

import sqlite3
import zipfile
from pathlib import Path

from download_db import (
    is_database_ready,
    package_database,
    verify_database_integrity,
)


def test_is_database_ready_false_non_existent(tmp_path):
    assert is_database_ready(tmp_path / "non_existent.db") is False


def test_is_database_ready_false_too_small(tmp_path):
    small_file = tmp_path / "small.db"
    small_file.write_bytes(b"dummy")
    assert is_database_ready(small_file) is False


def test_verify_database_integrity_valid_and_invalid(tmp_path):
    valid_db = tmp_path / "valid.db"
    conn = sqlite3.connect(valid_db)
    conn.execute("CREATE TABLE test (id INT)")
    conn.commit()
    conn.close()

    assert verify_database_integrity(valid_db) is True

    corrupt_db = tmp_path / "corrupt.db"
    corrupt_db.write_bytes(b"not a sqlite database")
    assert verify_database_integrity(corrupt_db) is False


def test_package_database(tmp_path):
    mock_db = tmp_path / "mock.db"
    conn = sqlite3.connect(mock_db)
    conn.execute("CREATE TABLE test (id INT, name TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'matrix')")
    conn.commit()
    conn.close()

    mock_zip = tmp_path / "mock.zip"
    packaged = package_database(source_db=mock_db, output_zip=mock_zip)

    assert packaged.exists()
    with zipfile.ZipFile(packaged, "r") as zf:
        assert "mock.db" in zf.namelist()
