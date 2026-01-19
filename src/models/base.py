"""
Base data model wrapper for validated DataFrames.

Provides consistent interface for accessing and serializing validated data.
Document-specific models (BalanceSheetModel, PLModel) will extend this.
"""
from typing import Any, Dict, List, Tuple

import pandas as pd


class DataModel:
    """
    Base wrapper class for validated pandas DataFrames.

    Provides common accessors and serialization methods.
    Designed for subclassing by document-specific models.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize model with a validated DataFrame.

        Args:
            df: Validated pandas DataFrame
        """
        self._df = df

    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the underlying DataFrame (read-only).

        Returns:
            The wrapped pandas DataFrame
        """
        return self._df

    @property
    def columns(self) -> List[str]:
        """
        Get list of column names.

        Returns:
            List of column names from DataFrame
        """
        return self._df.columns.tolist()

    @property
    def shape(self) -> Tuple[int, int]:
        """
        Get shape of the DataFrame.

        Returns:
            Tuple of (num_rows, num_columns)
        """
        return self._df.shape

    def head(self, n: int = 5) -> pd.DataFrame:
        """
        Get first n rows of the DataFrame.

        Args:
            n: Number of rows to return (default: 5)

        Returns:
            DataFrame with first n rows
        """
        return self._df.head(n)

    def to_dict(self, orient: str = 'records') -> Any:
        """
        Convert DataFrame to dictionary for serialization.

        Args:
            orient: Format for dictionary conversion. Options:
                   'records': list of dicts (one per row)
                   'dict': dict of column -> {index -> value}
                   'list': dict of column -> list of values
                   Default: 'records'

        Returns:
            Dictionary representation of DataFrame
        """
        return self._df.to_dict(orient=orient)

    @classmethod
    def from_dict(cls, data: Any, orient: str = 'records') -> 'DataModel':
        """
        Create DataModel from dictionary.

        Args:
            data: Dictionary data (format depends on orient)
            orient: Format of input dictionary. Options:
                   'records': list of dicts (one per row) - use pd.DataFrame(data)
                   'dict': dict of column -> {index -> value}
                   'list': dict of column -> list of values
                   Default: 'records'

        Returns:
            New DataModel instance with DataFrame created from dict
        """
        # pd.DataFrame.from_dict doesn't support 'records' orient
        # For 'records', use pd.DataFrame constructor directly
        if orient == 'records':
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame.from_dict(data, orient=orient)
        return cls(df)
