from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseExtractor(ABC):
    """
    Abstract Base Class for extracting data from various sources (APIs).
    Handles API connections, pagination, and rate limiting.
    """
    @abstractmethod
    def extract(self, query: str, max_results: int = 100) -> list[dict[str, Any]]:
        """
        Extracts raw payloads from the source API based on a search query.
        """
        pass


class BaseTransformer(ABC):
    """
    Abstract Base Class for transforming raw data into the unified WoS schema.
    Handles column mapping, type enforcing, and null cleaning.
    """
    @abstractmethod
    def transform(self, raw_data: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Transforms raw source data into a standardized Pandas DataFrame.
        """
        pass


class BaseValidator(ABC):
    """
    Abstract Base Class for validating the final schema before loading.
    Ensures structural integrity and type safety.
    """
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validates the schema, types, and constraints of the final DataFrame.
        Raises ValueError if validation fails.
        """
        pass
