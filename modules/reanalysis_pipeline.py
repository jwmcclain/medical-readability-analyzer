"""
Re-analysis pipeline module
Handles re-running analysis on previously collected and edited data
"""

import pandas as pd
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing modules
from modules import statistics, visualization, data_manager
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_reanalysis_pipeline(
    df: pd.DataFrame,
    search_term: str,
    generate_figs: bool = True,
    run_stats: bool = True
) -> Dict:
    """
    Execute re-analysis pipeline on uploaded data.
    Skips search, scraping, classification, and readability calculation.
    Runs statistics, visualization, and export only.
    
    Args:
        df: Validated and prepared DataFrame with readability data
        search_term: Original search term (for filenames and labels)
        generate_figs: Whether to generate visualization figures
        run_stats: Whether to perform statistical analysis
    
    Returns:
        Dictionary with analysis results:
        {
            'df': DataFrame,
            'stats': Statistical results dict or None,
            'figures': List of figure paths,
            'excel_path': Path to exported Excel file,
            'search_term': Search term used
        }
    """
    logger.info(f"Starting re-analysis pipeline for '{search_term}'")
    logger.info(f"Options: generate_figs={generate_figs}, run_stats={run_stats}")
    
    results = {
        'df': df,
        'stats': None,
        'figures': [],
        'excel_path': None,
        'search_term': search_term
    }
    
    try:
        # Convert DataFrame to list of dictionaries (format expected by data_manager)
        results_list = df.to_dict('records')
        
        # Step 1: Statistical Analysis
        if run_stats:
            logger.info("Performing statistical analysis...")
            try:
                stats = statistics.perform_statistical_analysis(df)
                results['stats'] = stats
                logger.info("Statistical analysis complete")
            except Exception as e:
                logger.error(f"Error in statistical analysis: {e}")
                # Continue with other steps even if stats fail
                results['stats'] = None
        else:
            logger.info("Statistical analysis skipped (disabled)")
        
        # Step 2: Visualizations
        if generate_figs:
            logger.info("Creating visualizations...")
            try:
                output_dir = "results/figures"
                os.makedirs(output_dir, exist_ok=True)
                
                figures = visualization.create_all_visualizations(
                    df, 
                    results['stats'], 
                    output_dir, 
                    search_term
                )
                results['figures'] = figures
                logger.info(f"Generated {len(figures)} figures")
            except Exception as e:
                logger.error(f"Error creating visualizations: {e}")
                # Continue with export even if figures fail
                results['figures'] = []
        else:
            logger.info("Visualization generation skipped (disabled)")
        
        # Step 3: Export to Excel
        logger.info("Generating Excel report...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"{search_term.replace(' ', '_')}_{timestamp}_reanalyzed.xlsx"
            excel_path = os.path.join("results/data", excel_filename)
            os.makedirs("results/data", exist_ok=True)
            
            # Export using existing data_manager
            data_manager.export_to_excel(
                results_list,
                results['stats'],
                search_term,
                excel_path
            )
            
            results['excel_path'] = excel_path
            logger.info(f"Excel file saved: {excel_path}")
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise  # Re-raise export errors as they're critical
        
        logger.info("Re-analysis pipeline completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error in re-analysis pipeline: {e}")
        raise


def validate_minimal_requirements(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Check if DataFrame has minimum data required for meaningful analysis.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Tuple of (is_valid, message)
    """
    issues = []
    
    # Check for minimum number of rows
    if len(df) < 3:
        issues.append("At least 3 rows of data required")
    
    # Check for at least some readability scores
    score_columns = ['GFI', 'SMOG', 'FKG', 'ARI']
    valid_scores = df[score_columns].dropna(how='all')
    
    if len(valid_scores) < 3:
        issues.append("At least 3 rows with readability scores required")
    
    # Check for both source types (for statistical comparison)
    source_types = df['source_type'].dropna().unique()
    if len(source_types) < 2:
        issues.append(
            f"Warning: Only {len(source_types)} source type found. "
            "Statistical comparison requires both Institutional and Private sources."
        )
    
    if issues:
        return False, "\n".join(issues)
    
    return True, "Minimum requirements met"


def get_analysis_summary(df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics of the dataset.
    
    Args:
        df: DataFrame to summarize
    
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total_rows': len(df),
        'institutional_count': len(df[df['source_type'] == 'Institutional']),
        'private_count': len(df[df['source_type'] == 'Private']),
        'mean_readability': df['mean_readability'].mean() if 'mean_readability' in df.columns else None,
        'has_content': 'content' in df.columns and not df['content'].isna().all(),
        'score_columns_present': all(col in df.columns for col in ['GFI', 'SMOG', 'FKG', 'ARI'])
    }
    
    return summary


if __name__ == "__main__":
    # Test the reanalysis pipeline
    print("\nTesting Re-analysis Pipeline")
    print("="*80)
    
    # Create sample test data
    test_data = pd.DataFrame({
        'rank': [1, 2, 3, 4, 5],
        'url': [
            'https://www.mayoclinic.org/test1',
            'https://www.healthline.com/test2',
            'https://www.webmd.com/test3',
            'https://www.example.com/test4',
            'https://www.test.org/test5'
        ],
        'domain': ['mayoclinic.org', 'healthline.com', 'webmd.com', 'example.com', 'test.org'],
        'source_type': ['Institutional', 'Institutional', 'Institutional', 'Private', 'Private'],
        'GFI': [10.5, 12.3, 11.8, 14.2, 13.5],
        'SMOG': [11.2, 13.1, 12.5, 15.0, 14.3],
        'FKG': [9.8, 11.5, 10.9, 13.2, 12.7],
        'ARI': [10.1, 12.0, 11.3, 13.8, 13.1],
        'mean_readability': [10.4, 12.2, 11.6, 14.1, 13.4],
        'word_count': [500, 750, 600, 800, 700],
        'sentence_count': [25, 35, 30, 40, 35],
        'status': ['success'] * 5
    })
    
    print(f"Test DataFrame shape: {test_data.shape}")
    print(f"Source distribution: {test_data['source_type'].value_counts().to_dict()}")
    
    # Test validation
    is_valid, message = validate_minimal_requirements(test_data)
    print(f"\nValidation: {message}")
    
    # Test summary
    summary = get_analysis_summary(test_data)
    print(f"\nSummary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test pipeline
    print("\n" + "="*80)
    print("Running re-analysis pipeline with test data...")
    print("="*80)
    
    try:
        results = run_reanalysis_pipeline(
            test_data,
            search_term='test_condition',
            generate_figs=True,
            run_stats=True
        )
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"Excel file: {results['excel_path']}")
        print(f"Figures generated: {len(results['figures'])}")
        print(f"Statistics calculated: {results['stats'] is not None}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
