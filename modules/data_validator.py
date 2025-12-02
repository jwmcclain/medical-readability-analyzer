"""
Data validation module for re-analysis feature
Validates uploaded Excel files to ensure they contain proper data structure
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, List
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_uploaded_file(file_path: str) -> Tuple[bool, str, pd.DataFrame]:
    """
    Validate uploaded Excel file for re-analysis.
    
    Args:
        file_path: Path to uploaded XLSX file
    
    Returns:
        Tuple of (is_valid, message, dataframe)
        - is_valid: Boolean indicating if file is valid
        - message: Success or error message
        - dataframe: Parsed DataFrame if valid, None if invalid
    """
    logger.info(f"Validating uploaded file: {file_path}")
    
    try:
        # Step 1: Check file format
        if not file_path.endswith('.xlsx'):
            return False, "❌ File must be in XLSX format.", None
        
        # Step 2: Try to load the Excel file
        try:
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        except Exception as e:
            return False, f"❌ Unable to read Excel file. It may be corrupted. Error: {str(e)}", None
        
        # Step 3: Check for Readability_Data sheet
        if 'Readability_Data' not in excel_file.sheet_names:
            available_sheets = ", ".join(excel_file.sheet_names)
            return False, f"❌ File must contain a 'Readability_Data' sheet. Found sheets: {available_sheets}", None
        
        # Step 4: Load the Readability_Data sheet
        df = pd.read_excel(file_path, sheet_name='Readability_Data', engine='openpyxl')
        
        if df.empty:
            return False, "❌ The Readability_Data sheet is empty.", None
        
        # Step 5: Check for required columns
        required_columns = ['rank', 'url', 'domain', 'source_type', 'GFI', 'SMOG', 'FKG', 'ARI']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"❌ Missing required columns: {', '.join(missing_columns)}", None
        
        # Step 6: Validate source_type values
        valid_source_types = ['Institutional', 'Private']
        invalid_sources = df[~df['source_type'].isin(valid_source_types + [np.nan])]['source_type'].unique()
        
        if len(invalid_sources) > 0:
            return False, f"❌ Invalid source_type values found: {', '.join(map(str, invalid_sources))}. Must be 'Institutional' or 'Private'.", None
        
        # Step 7: Validate readability scores are in reasonable range
        score_columns = ['GFI', 'SMOG', 'FKG', 'ARI']
        validation_errors = []
        
        for col in score_columns:
            if col in df.columns:
                # Check for values outside reasonable range (0-30)
                invalid_scores = df[
                    (df[col].notna()) & 
                    ((df[col] < 0) | (df[col] > 30))
                ]
                
                if not invalid_scores.empty:
                    invalid_rows = invalid_scores['rank'].tolist() if 'rank' in df.columns else invalid_scores.index.tolist()
                    validation_errors.append(
                        f"Column '{col}' has values outside range 0-30 in rows: {invalid_rows[:5]}" + 
                        (f"... and {len(invalid_rows) - 5} more" if len(invalid_rows) > 5 else "")
                    )
        
        if validation_errors:
            return False, "❌ Data validation errors:\n" + "\n".join(validation_errors), None
        
        # Step 8: Check if we have enough data for analysis
        valid_scores = df[score_columns].dropna(how='all')
        if len(valid_scores) < 3:
            return False, "❌ Insufficient data for analysis. Need at least 3 rows with readability scores.", None
        
        # Step 9: Validate URLs are present
        if df['url'].isna().all():
            return False, "❌ No valid URLs found in the data.", None
        
        # Step 10: Check for at least some classified sources
        if df['source_type'].isna().all():
            return False, "❌ No source classifications found. The 'source_type' column is empty.", None
        
        # Step 11: Log data summary
        total_rows = len(df)
        institutional_count = len(df[df['source_type'] == 'Institutional'])
        private_count = len(df[df['source_type'] == 'Private'])
        valid_readability_count = len(valid_scores)
        
        logger.info(f"File validation successful:")
        logger.info(f"  Total rows: {total_rows}")
        logger.info(f"  Institutional sources: {institutional_count}")
        logger.info(f"  Private sources: {private_count}")
        logger.info(f"  Rows with readability scores: {valid_readability_count}")
        
        # Construct success message
        success_message = f"""✅ File validated successfully!
        
**Data Summary:**
- Total URLs: {total_rows}
- Institutional sources: {institutional_count}
- Private sources: {private_count}
- Rows with readability scores: {valid_readability_count}

Ready for re-analysis."""
        
        return True, success_message, df
        
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return False, f"❌ Unexpected error while validating file: {str(e)}", None


def check_optional_columns(df: pd.DataFrame) -> List[str]:
    """
    Check which optional columns are present in the DataFrame.
    
    Args:
        df: DataFrame to check
    
    Returns:
        List of missing optional column names
    """
    optional_columns = [
        'mean_readability',
        'word_count', 
        'sentence_count',
        'classification_confidence',
        'content',
        'status'
    ]
    
    missing = [col for col in optional_columns if col not in df.columns]
    return missing


def prepare_dataframe_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare validated DataFrame for re-analysis.
    Calculates mean_readability if missing.
    
    Args:
        df: Validated DataFrame
    
    Returns:
        Prepared DataFrame ready for analysis
    """
    df_prepared = df.copy()
    
    # Calculate mean_readability if not present
    if 'mean_readability' not in df_prepared.columns:
        logger.info("Calculating mean_readability from individual metrics...")
        score_columns = ['GFI', 'SMOG', 'FKG', 'ARI']
        
        # Calculate mean for each row
        df_prepared['mean_readability'] = df_prepared[score_columns].mean(axis=1, skipna=True)
        logger.info("mean_readability calculated successfully")
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['rank', 'GFI', 'SMOG', 'FKG', 'ARI', 'mean_readability']
    for col in numeric_columns:
        if col in df_prepared.columns:
            df_prepared[col] = pd.to_numeric(df_prepared[col], errors='coerce')
    
    # Ensure string columns are properly typed
    string_columns = ['url', 'domain', 'source_type']
    for col in string_columns:
        if col in df_prepared.columns:
            df_prepared[col] = df_prepared[col].astype(str)
    
    return df_prepared


if __name__ == "__main__":
    # Test the validation module
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\nValidating file: {test_file}")
        print("="*80)
        
        is_valid, message, df = validate_uploaded_file(test_file)
        
        print(message)
        
        if is_valid:
            print(f"\nDataFrame shape: {df.shape}")
            print(f"\nColumns found: {', '.join(df.columns)}")
            
            missing_optional = check_optional_columns(df)
            if missing_optional:
                print(f"\nMissing optional columns: {', '.join(missing_optional)}")
            
            df_prepared = prepare_dataframe_for_analysis(df)
            print(f"\nPrepared DataFrame ready for analysis!")
            print(f"Mean readability calculated: {'mean_readability' in df_prepared.columns}")
    else:
        print("Usage: python data_validator.py <path_to_excel_file>")
