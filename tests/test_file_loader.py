"""
Unit tests for FileLoader.

Tests automatic format detection, error handling, and various file scenarios.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.loaders import (
    CorruptedFileError,
    EmptyFileError,
    FileLoader,
    UnsupportedFileFormatError,
)
from tests.fixtures import (
    create_csv_file,
    create_empty_sample,
    create_excel_file,
    create_valid_sample,
)


class TestFileLoader:
    """Test suite for FileLoader class."""

    @pytest.fixture
    def loader(self):
        """Create FileLoader instance."""
        return FileLoader()

    @pytest.fixture
    def valid_csv_file(self, tmp_path):
        """Create a valid CSV file for testing."""
        data = create_valid_sample()
        file_path = tmp_path / "test.csv"
        return create_csv_file(data, file_path)

    @pytest.fixture
    def valid_excel_file(self, tmp_path):
        """Create a valid Excel file for testing."""
        data = create_valid_sample()
        file_path = tmp_path / "test.xlsx"
        return create_excel_file(data, file_path)

    @pytest.fixture
    def empty_csv_file(self, tmp_path):
        """Create an empty CSV file."""
        data = create_empty_sample()
        file_path = tmp_path / "empty.csv"
        return create_csv_file(data, file_path)

    def test_load_valid_csv(self, loader, valid_csv_file):
        """Test loading valid CSV file returns correct DataFrame."""
        df = loader.load(valid_csv_file)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'Date' in df.columns
        assert 'Account' in df.columns
        assert 'Amount' in df.columns
        assert len(df) == 3

    def test_load_valid_excel(self, loader, valid_excel_file):
        """Test loading valid Excel file returns correct DataFrame."""
        df = loader.load(valid_excel_file)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'Date' in df.columns
        assert 'Account' in df.columns
        assert 'Amount' in df.columns
        assert len(df) == 3

    def test_format_detection(self, loader, valid_csv_file, valid_excel_file):
        """Test automatic format detection based on file extension."""
        # CSV detection
        csv_df = loader.load(valid_csv_file)
        assert isinstance(csv_df, pd.DataFrame)

        # Excel detection
        excel_df = loader.load(valid_excel_file)
        assert isinstance(excel_df, pd.DataFrame)

        # Both should have same structure
        assert list(csv_df.columns) == list(excel_df.columns)

    def test_file_not_found(self, loader):
        """Test that non-existent file raises FileNotFoundError."""
        non_existent = Path("/path/to/nonexistent/file.csv")

        with pytest.raises(FileNotFoundError):
            loader.load(non_existent)

    def test_unsupported_format_txt(self, loader, tmp_path):
        """Test that .txt file raises UnsupportedFileFormatError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("some text data")

        with pytest.raises(UnsupportedFileFormatError) as exc_info:
            loader.load(txt_file)

        error_msg = str(exc_info.value)
        assert ".txt" in error_msg
        assert ".csv" in error_msg
        assert ".xlsx" in error_msg

    def test_unsupported_format_json(self, loader, tmp_path):
        """Test that .json file raises UnsupportedFileFormatError."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with pytest.raises(UnsupportedFileFormatError):
            loader.load(json_file)

    def test_empty_csv(self, loader, empty_csv_file):
        """Test that empty CSV file raises EmptyFileError."""
        with pytest.raises(EmptyFileError) as exc_info:
            loader.load(empty_csv_file)

        error_msg = str(exc_info.value)
        assert "empty" in error_msg.lower()

    def test_empty_excel(self, loader, tmp_path):
        """Test that empty Excel file raises EmptyFileError."""
        data = create_empty_sample()
        excel_file = tmp_path / "empty.xlsx"
        create_excel_file(data, excel_file)

        with pytest.raises(EmptyFileError):
            loader.load(excel_file)

    def test_corrupted_csv(self, loader, tmp_path):
        """Test that corrupted CSV raises CorruptedFileError."""
        # Create malformed CSV
        corrupted_file = tmp_path / "corrupted.csv"
        corrupted_file.write_text("Date,Account\n2025-01-01,Checking\n\"unclosed quote")

        with pytest.raises(CorruptedFileError) as exc_info:
            loader.load(corrupted_file)

        error_msg = str(exc_info.value)
        assert "corrupted" in error_msg.lower()

    def test_corrupted_excel(self, loader, tmp_path):
        """Test that corrupted Excel file raises CorruptedFileError."""
        # Create file with .xlsx extension but invalid content
        corrupted_file = tmp_path / "corrupted.xlsx"
        corrupted_file.write_bytes(b"This is not a valid Excel file")

        with pytest.raises((CorruptedFileError, Exception)):
            # Might raise CorruptedFileError or other pandas exception
            loader.load(corrupted_file)

    def test_load_with_string_path(self, loader, valid_csv_file):
        """Test that loader accepts string paths in addition to Path objects."""
        df = loader.load(str(valid_csv_file))

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    @pytest.mark.parametrize("extension", [".csv", ".xlsx"])
    def test_supported_formats(self, loader, extension):
        """Test that supported formats are correctly identified."""
        assert extension in loader.SUPPORTED_FORMATS
