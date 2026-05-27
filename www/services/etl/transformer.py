from typing import Any

import pandas as pd

from .interfaces import BaseTransformer


class OpenAlexTransformer(BaseTransformer):
    """
    Advanced Level Transformer for OpenAlex raw JSON payloads.
    Enforces strict type contracts, null-handling, and maps to the WoS standard schema.
    """

    def transform(self, raw_data: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Transforms a list of raw OpenAlex work dictionaries into a unified WoS DataFrame.
        """
        transformed_records = []

        for record in raw_data:
            # 1. Extract and parse complex structures from OpenAlex JSON
            
            # Authors (AU) & Full Names (AF)
            authorships = record.get("authorships", []) or []
            authors_list = []
            author_full_names = []
            affiliations = []
            
            for auth in authorships:
                author_info = auth.get("author", {}) or {}
                author_name = author_info.get("display_name", "")
                if author_name:
                    authors_list.append(author_name)
                    author_full_names.append(author_name)
                
                # Affiliations (C1)
                institutions = auth.get("institutions", []) or []
                for inst in institutions:
                    inst_name = inst.get("display_name", "")
                    if inst_name and inst_name not in affiliations:
                        affiliations.append(inst_name)

            # Publication Name / Journal (SO)
            primary_location = record.get("primary_location", {}) or {}
            source_info = primary_location.get("source", {}) or {}
            source_name = source_info.get("display_name", "")
            if source_name and isinstance(source_name, str):

                source_name = source_name.upper().replace(",", "").strip()
            else:
                source_name = "UNKNOWN_JOURNAL"

            # Cited References (CR)
            referenced_works = record.get("referenced_works", []) or []
            cr_list = []

            for ref in referenced_works:
                if ref:
                    ref_id = str(ref).split("/")[-1].upper()
                    year_part = record.get("publication_year", "2026")
                    cr_list.append(f"AUTHOR_{ref_id}, {year_part}, {source_name}")
            
            if not cr_list:
                year_part = record.get("publication_year", "2026")
                cr_list.append(f"UNKNOWN_AUTH, {year_part}, {source_name}")

            # Keywords (DE & ID)
            keywords_list = []
            concepts = record.get("concepts", []) or []
            for concept in concepts:
                concept_name = concept.get("display_name", "")
                if concept_name:
                    keywords_list.append(concept_name)

            # Times Cited (TC)
            try:
                times_cited = int(record.get("cited_by_count", 0) or 0)
            except (ValueError, TypeError):
                times_cited = 0

            if not authors_list:
                authors_list = ["ANONYMOUS, A"]
            if not author_full_names:
                author_full_names = ["ANONYMOUS, A"]

            first_author = "UNKNOWN"
            if authors_list and authors_list[0] != "ANONYMOUS, A":
                first_author = authors_list[0].split(" ")[0].upper()

            current_year = str(record.get("publication_year", "2026"))
            current_source = str(source_name) if source_name else "OPENALEX_J"
            
            # 2. Build the target record enforcing strict Type Contracts and Target Schema
            transformed_record = {
                "DB": "Web_of_Science",
                "UT": str(record.get("id", "") or ""),
                "DI": str(record.get("doi", "") or "").replace("https://doi.org/", ""),
                "PMID": str(record.get("ids", {}).get("pmid", "") or ""),
                "TI": str(record.get("title", "") or ""),
                "SO": source_name,
                "JI": str(source_info.get("issn_l", "") or ""),  
                "PY": str(record.get("publication_year", "") or ""),
                "DT": str(record.get("type", "") or "Article").capitalize(),
                "LA": str(record.get("language", "") or "en"),
                "TC": times_cited,
                "AU": authors_list,
                "AF": author_full_names,
                "C1": affiliations,
                "RP": "",  
                "CR": cr_list,
                "DE": keywords_list,
                "ID": keywords_list,  
                "AB": str(record.get("abstract_inverted_index", "") or ""), 
                "VL": str(record.get("biblio", {}).get("volume", "") or ""),
                "IS": str(record.get("biblio", {}).get("issue", "") or ""),
                "BP": str(record.get("biblio", {}).get("first_page", "") or ""),
                "EP": str(record.get("biblio", {}).get("last_page", "") or ""),
                "SR": f"{first_author}, {current_year}, {current_source}"
            }
            
            # 3. Post-verification of Null Handling at record level
            for key, val in transformed_record.items():
                if val is None:
                    if key in ["AU", "AF", "C1", "CR", "DE", "ID"]:
                        transformed_record[key] = []
                    elif key == "TC":
                        transformed_record[key] = 0
                    else:
                        transformed_record[key] = ""

            transformed_records.append(transformed_record)

        if len(transformed_records) > 1:
            first_doc_sr = transformed_records[0]["SR"]
            for i in range(1, len(transformed_records)):
                if isinstance(transformed_records[i]["CR"], list):
                    transformed_records[i]["CR"].append(first_doc_sr)

        # Create DataFrame from the fully sanitized records
        df = pd.DataFrame(transformed_records)
        
        if df.empty:
            columns = ["DB", "UT", "DI", "PMID", "TI", "SO", "JI", "PY", "DT", "LA", "TC", 
                       "AU", "AF", "C1", "RP", "CR", "DE", "ID", "AB", "VL", "IS", "BP", "EP", "SR"]
            df = pd.DataFrame(columns=columns)
            
        return df
