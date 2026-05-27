import pandas as pd

from .extractor import OpenAlexExtractor
from .transformer import OpenAlexTransformer
from .validator import BibliometrixValidator, apply_calculated_fields


class BibliometrixETLDispatcher:
    """
    The central Dispatcher/Orchestrator for the Bibliometrix ETL pipeline.
    Acts as the source-agnostic single entry-point mimicking R's convert2df().
    """
    def __init__(self):
        self.validator = BibliometrixValidator()

    def run_api_pipeline(self, platform: str, query: str, max_results: int = 100) -> pd.DataFrame:
        """
        Orchestrates the 5 phases of ETL based on the selected platform.
        """
        platform_clean = platform.lower().strip()
        
        # Dispatcher Pattern: Resolve components dynamically based on chosen platform
        if platform_clean == "openalex":
            extractor = OpenAlexExtractor()
            transformer = OpenAlexTransformer()
        elif platform_clean == "pubmed":
            # PubMed placeholder as required by the Advanced track layout
            raise NotImplementedError("PubMed API Extractor component is currently under maintenance.")
        else:
            raise ValueError(f"[Pipeline Error] Unsupported platform selection: '{platform}'")

        print(f"\n[Pipeline] Starting Advanced ETL for platform: {platform_clean.upper()}")
        print(f"[Pipeline] Search Query: '{query}' | Targeting up to {max_results} records.")
        print("-" * 60)

        # Phase 1: EXTRACT
        raw_data = extractor.extract(query, max_results=max_results)
        if not raw_data:
            print("[Pipeline] Warning: No raw data records could be extracted.")
            
        # Phase 2 & 3: TRANSFORM (Rename via Lookup & Strict Type Enforcements)
        df = transformer.transform(raw_data)
        print(f"[Pipeline] Transform phase complete. Structural DataFrame initialized.")

        # Phase 4: CALCULATED FIELDS (System Derivations)
        df = apply_calculated_fields(df)

        # Phase 5: VALIDATION (Strict Schema Safety Check)
        self.validator.validate(df)

        print("-" * 60)
        print(f"[Pipeline] SUCCESS: Standardized DataFrame is completely ready for analytical functions.\n")
        return df


def convert2df_api(platform: str, query: str, max_results: int = 100) -> pd.DataFrame:
    """
    Unified entry-point function for automated API bibliographic data extraction.
    Replicates the conceptual robustness of convert2df() from the R environment.
    """
    dispatcher = BibliometrixETLDispatcher()
    return dispatcher.run_api_pipeline(platform, query, max_results)
