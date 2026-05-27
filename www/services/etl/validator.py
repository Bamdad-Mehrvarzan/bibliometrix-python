import pandas as pd
import numpy as np

from .interfaces import BaseValidator


class BibliometrixValidator(BaseValidator):
    """
    Phase 5: Validation Module.
    Programmatically verifies schema integrity, mandatory columns, type contracts, 
    and ensures absolute absence of null/NaN values before final export.
    """

    # The Target Schema Glossary from Section 4.2
    MANDATORY_COLUMNS = {
        "DB": str, "UT": str, "DI": str, "PMID": str, "TI": str, "SO": str,
        "JI": str, "PY": str, "DT": str, "LA": str, "TC": int, "AU": list,
        "AF": list, "C1": list, "RP": str, "CR": list, "DE": list, "ID": list,
        "AB": str, "VL": str, "IS": str, "BP": str, "EP": str, "SR": str
    }

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Runs programmatic checks on the standardized DataFrame.
        Raises ValueError if any contract is violated.
        """
        if df is None:
            raise ValueError("[Validation Error] DataFrame is None.")

        # 1. Verify all mandatory columns exist
        missing_cols = [col for col in self.MANDATORY_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"[Validation Error] Missing mandatory columns: {missing_cols}")

        # 2. Verify absolute absence of NaN / None / NaT values
        null_counts = df.isna().sum().sum()
        if null_counts > 0:
            # Pinpoint exactly which columns contain illegal nulls for debugging
            cols_with_nulls = df.columns[df.isna().any()].tolist()
            raise ValueError(f"[Validation Error] Forbidden NaN/None values detected in columns: {cols_with_nulls}")

        # 3. Enforce strict Type Contracts
        for col, expected_type in self.MANDATORY_COLUMNS.items():
            for index, value in df[col].items():
                if not isinstance(value, expected_type):
                    # Edge case handling for Pandas internal numeric types vs Python int
                    if expected_type is int and isinstance(value, (int, np.integer)):
                        continue
                    raise TypeError(
                        f"[Validation Error] Type mismatch at column '{col}', row {index}. "
                        f"Expected {expected_type.__name__}, got {type(value).__name__}."
                    )

        print(f"[Validation] Success! Passed all schema, nullability, and contract checks for {len(df)} rows.")
        return True


def apply_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phase 4: Calculated Fields.
    Invokes the existing internal library logic to generate the Short Reference (SR) field.
    Formats as 'FirstAuthor_Surname, Publication_Year, Journal_Name'.
    """
    print("[Calculated Fields] Generating Short Reference (SR) keys...")
    
    for index, row in df.iterrows():
        # Fallback manual generation in case the core package functions are not exposed properly in the environment
        try:
            # We attempt to import dynamically from the hosting repository if available
            from www.services.parsers import create_sr  # Adjust based on exact upstream layout if needed
            sr_value = create_sr(row)
        except ImportError:
            # Robust, exact replication of the standard Bibliometrix SR rule: FirstAuthor, Year, Journal
            authors = row.get("AU", [])
            year = str(row.get("PY", ""))
            journal = str(row.get("SO", ""))
            
            first_author = "UNKNOWN"
            if authors and len(authors) > 0:
                # Extract surname from 'Surname Initials' or 'Surname, Firstname'
                raw_author = authors[0]
                first_author = raw_author.split(",")[0].split(" ")[0].strip().upper()
            
            # Formulate standard SR string
            sr_value = f"{first_author}, {year}, {journal}"
        
        df.at[index, "SR"] = sr_value

    return df
