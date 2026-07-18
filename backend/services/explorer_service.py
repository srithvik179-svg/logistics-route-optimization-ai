import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from backend.utils.logger import logger

class ExplorerService:
    """Service to handle dataset profiling, global search, stacking filters, sorting, and pagination."""

    @staticmethod
    def get_memory_usage(df: pd.DataFrame) -> str:
        """Returns the formatted memory usage of a DataFrame."""
        try:
            bytes_used = df.memory_usage(deep=True).sum()
            if bytes_used < 1024:
                return f"{bytes_used} Bytes"
            elif bytes_used < 1024 * 1024:
                return f"{round(bytes_used / 1024, 2)} KB"
            else:
                return f"{round(bytes_used / (1024 * 1024), 2)} MB"
        except Exception as e:
            logger.error(f"Error calculating memory usage: {str(e)}")
            return "Unknown"

    @staticmethod
    def profile_column(df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Profiles a single column, generating statistics and sample values.
        
        Args:
            df: DataFrame containing the column.
            col: Name of the column.
            
        Returns:
            Dict: Profiling statistics (name, type, nulls, duplicates, uniques, samples).
        """
        if col not in df.columns:
            raise ValueError(f"Column '{col}' does not exist in the dataset.")
            
        series = df[col]
        total_rows = len(series)
        
        # Determine Data Type
        dt = str(series.dtype)
        if pd.api.types.is_datetime64_any_dtype(series):
            dt = "datetime"
        elif pd.api.types.is_bool_dtype(series):
            dt = "boolean"
        elif pd.api.types.is_numeric_dtype(series):
            dt = "numeric"
        elif pd.api.types.is_object_dtype(series) or isinstance(series.dtype, pd.CategoricalDtype):
            dt = "text"
            
        null_count = int(series.isnull().sum())
        duplicate_count = int(series.duplicated().sum())
        unique_count = int(series.nunique(dropna=True))
        
        # Get sample values (top 15 unique, non-null values)
        raw_samples = series.dropna().unique()
        samples = []
        for val in raw_samples[:15]:
            if isinstance(val, (pd.Timestamp, np.datetime64)):
                samples.append(str(val))
            elif isinstance(val, (float, np.float64)):
                if np.isnan(val):
                    continue
                samples.append(float(val))
            elif isinstance(val, (int, np.int64)):
                samples.append(int(val))
            else:
                samples.append(str(val))

        return {
            "column_name": col,
            "data_type": dt,
            "total_count": total_rows,
            "null_count": null_count,
            "duplicate_count": duplicate_count,
            "unique_count": unique_count,
            "sample_values": samples
        }

    @classmethod
    def query_dataframe(
        cls,
        df: pd.DataFrame,
        page: int = 1,
        page_size: int = 10,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        search_query: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[pd.DataFrame, int]:
        """Applies search, stacking filters, sorting, and paginates a DataFrame.
        
        Args:
            df: Source DataFrame.
            page: 1-indexed page number.
            page_size: Number of records per page.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.
            search_query: Global search text.
            filters: Stackable filters list of dicts: [{'column': '...', 'operator': '...', 'value': '...'}]
            
        Returns:
            Tuple[pd.DataFrame, int]: Paginated DataFrame and total record count matching queries.
        """
        filtered_df = df.copy()
        
        # 1. Apply stackable filters
        if filters:
            for f in filters:
                col = f.get("column")
                op = f.get("operator")
                val = f.get("value")
                
                if not col or col not in filtered_df.columns:
                    continue
                    
                series = filtered_df[col]
                
                try:
                    # Filter based on type
                    if pd.api.types.is_datetime64_any_dtype(series):
                        dt_val = pd.to_datetime(val, errors='coerce')
                        if pd.isnull(dt_val):
                            continue
                        if op == "before":
                            filtered_df = filtered_df[filtered_df[col] < dt_val]
                        elif op == "after":
                            filtered_df = filtered_df[filtered_df[col] > dt_val]
                        elif op == "on_date":
                            filtered_df = filtered_df[filtered_df[col].dt.date == dt_val.date()]
                            
                    elif pd.api.types.is_numeric_dtype(series):
                        num_val = float(val)
                        if op == "==":
                            filtered_df = filtered_df[filtered_df[col] == num_val]
                        elif op == ">":
                            filtered_df = filtered_df[filtered_df[col] > num_val]
                        elif op == "<":
                            filtered_df = filtered_df[filtered_df[col] < num_val]
                        elif op == ">=":
                            filtered_df = filtered_df[filtered_df[col] >= num_val]
                        elif op == "<=":
                            filtered_df = filtered_df[filtered_df[col] <= num_val]
                            
                    elif pd.api.types.is_bool_dtype(series):
                        bool_val = str(val).lower() in ["true", "1", "yes"]
                        if op == "is_true":
                            filtered_df = filtered_df[filtered_df[col] == True]
                        elif op == "is_false":
                            filtered_df = filtered_df[filtered_df[col] == False]
                            
                    else:  # Text/Categorical
                        str_val = str(val).strip().lower()
                        if op == "contains":
                            filtered_df = filtered_df[filtered_df[col].astype(str).str.lower().str.contains(str_val, na=False)]
                        elif op == "equals":
                            filtered_df = filtered_df[filtered_df[col].astype(str).str.lower() == str_val]
                        elif op == "starts_with":
                            filtered_df = filtered_df[filtered_df[col].astype(str).str.lower().str.startswith(str_val, na=False)]
                            
                except Exception as e:
                    logger.warning(f"ExplorerService: Failed applying filter on '{col}': {str(e)}")
                    continue

        # 2. Apply global search
        if search_query:
            search_str = str(search_query).strip().lower()
            if search_str:
                # Build an OR mask across all columns
                mask = pd.Series(False, index=filtered_df.index)
                for col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.lower().str.contains(search_str, na=False)
                filtered_df = filtered_df[mask]

        total_count = len(filtered_df)

        # 3. Apply sorting
        if sort_by and sort_by in filtered_df.columns:
            ascending = sort_order.lower() == "asc" if sort_order else True
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

        # 4. Paginate / Slice
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_df = filtered_df.iloc[start_idx:end_idx].copy()
        
        return paginated_df, total_count
