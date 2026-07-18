import pandas as pd
from typing import Dict, Tuple

class TextProcessor:
    """Processor to normalize casing, trim whitespaces, and unify categorical string fields."""
    
    # Specific normalization maps for cities
    CITY_NORMALIZATION: Dict[str, str] = {
        "bangalore": "Bengaluru",
        "bengaluru": "Bengaluru",
        "bengaluru city": "Bengaluru",
        "hyd": "Hyderabad",
        "hyderabad": "Hyderabad",
        "secunderabad": "Hyderabad",
        "dallas": "Dallas",
        "dallas tx": "Dallas",
        "austin": "Austin",
        "houston": "Houston",
        "san antonio": "San Antonio",
        "el paso": "El Paso"
    }

    @classmethod
    def process(cls, df: pd.DataFrame, sheet_name: str) -> Tuple[pd.DataFrame, int]:
        """Trims whitespace and normalizes text fields in a DataFrame.
        
        Args:
            df: Raw input DataFrame (copy will be modified).
            sheet_name: Name of the sheet being processed.
            
        Returns:
            Tuple[pd.DataFrame, int]: Processed DataFrame and count of values modified.
        """
        processed_df = df.copy()
        modifications_count = 0
        
        # Select all object (string) columns
        string_cols = processed_df.select_dtypes(include=["object"]).columns
        
        for col in string_cols:
            # 1. Trim whitespace
            non_null_mask = processed_df[col].notnull()
            
            # String coercion if mixed types
            processed_df.loc[non_null_mask, col] = processed_df.loc[non_null_mask, col].astype(str).str.strip()
            
            # 2. Specific normalizations
            if col == "City" or col == "Destination_Hub" or col == "Origin_Hub":
                # Normalize city names or hubs based on maps
                for i in processed_df[non_null_mask].index:
                    val = str(processed_df.loc[i, col])
                    val_lower = val.lower().strip()
                    
                    if val_lower in cls.CITY_NORMALIZATION:
                        normalized = cls.CITY_NORMALIZATION[val_lower]
                        if val != normalized:
                            processed_df.loc[i, col] = normalized
                            modifications_count += 1
                            
                    elif col == "City":
                        # Default title case for other cities
                        title_val = val.title()
                        if val != title_val:
                            processed_df.loc[i, col] = title_val
                            modifications_count += 1
                            
            elif col == "SLA_Status":
                # SLA statuses MET / MISSED should be upper
                for i in processed_df[non_null_mask].index:
                    val = str(processed_df.loc[i, col])
                    upper_val = val.upper().strip()
                    if val != upper_val:
                        processed_df.loc[i, col] = upper_val
                        modifications_count += 1
                        
            elif col in ["TPR_Name", "Part_Name", "Category", "Hub_Name", "Coverage_Region"]:
                # Default Title Case for descriptive names
                for i in processed_df[non_null_mask].index:
                    val = str(processed_df.loc[i, col])
                    # If it starts with TPR- or HUB- keep it as uppercase, otherwise Title
                    if val.upper().startswith("TPR-") or val.upper().startswith("HUB-"):
                        upper_val = val.upper()
                        if val != upper_val:
                            processed_df.loc[i, col] = upper_val
                            modifications_count += 1
                    else:
                        title_val = val.title()
                        if val != title_val:
                            processed_df.loc[i, col] = title_val
                            modifications_count += 1

        return processed_df, modifications_count
