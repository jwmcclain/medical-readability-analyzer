"""
Statistical analysis module
Performs descriptive and inferential statistics on readability data
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def perform_statistical_analysis(df: pd.DataFrame) -> Dict:
    """
    Perform complete statistical analysis on readability data.
    
    Args:
        df: DataFrame with readability scores and source_type
    
    Returns:
        Dictionary with descriptive stats, normality tests, and group comparisons
    """
    logger.info("Starting statistical analysis...")
    
    results = {
        'descriptive': {},
        'normality': {},
        'comparisons': {},
        'overall': {}
    }
    
    metrics = ['GFI', 'SMOG', 'FKG', 'ARI', 'mean_readability']
    
    # Overall statistics (all data combined)
    for metric in metrics:
        if metric in df.columns:
            data = df[metric].dropna()
            if len(data) > 0:
                results['overall'][metric] = calculate_descriptive_stats(data)
    
    # Statistics by source type
    for metric in metrics:
        if metric in df.columns and 'source_type' in df.columns:
            results['descriptive'][metric] = {}
            results['normality'][metric] = {}
            
            for source_type in df['source_type'].unique():
                group_data = df[df['source_type'] == source_type][metric].dropna()
                
                if len(group_data) > 0:
                    # Descriptive statistics
                    results['descriptive'][metric][source_type] = calculate_descriptive_stats(group_data)
                    
                    # Normality test
                    results['normality'][metric][source_type] = test_normality(group_data)
    
    # Group comparisons (Institutional vs Private)
    if 'source_type' in df.columns:
        for metric in metrics:
            if metric in df.columns:
                institutional = df[df['source_type'] == 'Institutional'][metric].dropna()
                private = df[df['source_type'] == 'Private'][metric].dropna()
                
                if len(institutional) > 0 and len(private) > 0:
                    results['comparisons'][metric] = compare_groups(
                        institutional, private, metric
                    )
    
    logger.info("Statistical analysis complete")
    return results


def calculate_descriptive_stats(data: pd.Series) -> Dict:
    """
    Calculate descriptive statistics for a data series.
    
    Args:
        data: pandas Series of numeric data
    
    Returns:
        Dictionary with statistical measures
    """
    return {
        'mean': float(data.mean()),
        'median': float(data.median()),
        'std': float(data.std()),
        'min': float(data.min()),
        'max': float(data.max()),
        'q25': float(data.quantile(0.25)),
        'q75': float(data.quantile(0.75)),
        'n': int(len(data)),
    }


def test_normality(data: pd.Series) -> Dict:
    """
    Test if data follows normal distribution using Shapiro-Wilk test.
    
    Args:
        data: pandas Series of numeric data
    
    Returns:
        Dictionary with test results
    """
    if len(data) < 3:
        return {
            'statistic': None,
            'p_value': None,
            'is_normal': False,
            'note': 'Sample size too small for test'
        }
    
    try:
        statistic, p_value = stats.shapiro(data)
        is_normal = p_value > 0.05
        
        return {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'is_normal': bool(is_normal),
            'interpretation': f"{'Normal' if is_normal else 'Non-normal'} distribution (p={p_value:.4f})"
        }
    except Exception as e:
        logger.error(f"Error in normality test: {e}")
        return {
            'statistic': None,
            'p_value': None,
            'is_normal': False,
            'error': str(e)
        }


def compare_groups(group1: pd.Series, group2: pd.Series, metric_name: str) -> Dict:
    """
    Compare two groups using appropriate statistical test.
    
    Args:
        group1: First group data (Institutional)
        group2: Second group data (Private)
        metric_name: Name of the metric being compared
    
    Returns:
        Dictionary with test results
    """
    # Test normality of both groups
    norm1 = test_normality(group1)
    norm2 = test_normality(group2)
    
    # Choose appropriate test
    if norm1['is_normal'] and norm2['is_normal']:
        # Both normal - use t-test
        test_name = "Independent t-test"
        try:
            statistic, p_value = stats.ttest_ind(group1, group2)
            # Calculate Cohen's d effect size
            effect_size = cohens_d(group1, group2)
        except Exception as e:
            logger.error(f"Error in t-test: {e}")
            return {'error': str(e)}
    else:
        # At least one non-normal - use Mann-Whitney U test
        test_name = "Mann-Whitney U test"
        try:
            statistic, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            # Calculate rank-biserial correlation as effect size
            effect_size = rank_biserial(group1, group2, statistic)
        except Exception as e:
            logger.error(f"Error in Mann-Whitney U test: {e}")
            return {'error': str(e)}
    
    # Interpret results
    significant = p_value < config.SIGNIFICANCE_LEVEL
    
    # Direction of difference
    mean1 = group1.mean()
    mean2 = group2.mean()
    direction = "Institutional < Private" if mean1 < mean2 else "Institutional > Private"
    
    return {
        'test_used': test_name,
        'statistic': float(statistic),
        'p_value': float(p_value),
        'significant': bool(significant),
        'effect_size': float(effect_size),
        'group1_mean': float(mean1),
        'group2_mean': float(mean2),
        'direction': direction,
        'interpretation': f"{'Significant' if significant else 'No significant'} difference (p={p_value:.4f}, effect size={effect_size:.3f})",
        'group1_normal': norm1['is_normal'],
        'group2_normal': norm2['is_normal'],
    }


def cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    # Cohen's d
    d = (group1.mean() - group2.mean()) / pooled_std
    
    return d


def rank_biserial(group1: pd.Series, group2: pd.Series, u_statistic: float) -> float:
    """
    Calculate rank-biserial correlation (effect size for Mann-Whitney U).
    
    Args:
        group1: First group data
        group2: Second group data
        u_statistic: Mann-Whitney U statistic
    
    Returns:
        Rank-biserial correlation
    """
    n1, n2 = len(group1), len(group2)
    # Rank-biserial = 1 - (2U)/(n1*n2)
    rb = 1 - (2 * u_statistic) / (n1 * n2)
    return rb


def analyze_correlations(df: pd.DataFrame) -> Dict:
    """
    Analyze correlations between metrics and with Google rank.
    
    Args:
        df: DataFrame with readability scores and rank
    
    Returns:
        Dictionary with correlation matrices
    """
    metrics = ['GFI', 'SMOG', 'FKG', 'ARI']
    available_metrics = [m for m in metrics if m in df.columns]
    
    if 'rank' in df.columns:
        available_metrics.append('rank')
    
    if len(available_metrics) < 2:
        return {'error': 'Insufficient metrics for correlation analysis'}
    
    # Calculate Spearman correlations (non-parametric)
    corr_matrix = df[available_metrics].corr(method='spearman')
    
    return {
        'correlation_matrix': corr_matrix.to_dict(),
        'interpretation': interpret_correlations(corr_matrix)
    }


def interpret_correlations(corr_matrix: pd.DataFrame) -> list:
    """
    Interpret notable correlations.
    
    Args:
        corr_matrix: Correlation matrix DataFrame
    
    Returns:
        List of interpretation strings
    """
    interpretations = []
    
    for i, col1 in enumerate(corr_matrix.columns):
        for j, col2 in enumerate(corr_matrix.columns):
            if i < j:  # Only upper triangle
                corr = corr_matrix.loc[col1, col2]
                if abs(corr) > 0.7:
                    strength = "strong"
                elif abs(corr) > 0.4:
                    strength = "moderate"
                else:
                    continue
                
                direction = "positive" if corr > 0 else "negative"
                interpretations.append(
                    f"{strength.capitalize()} {direction} correlation between {col1} and {col2} (r={corr:.3f})"
                )
    
    return interpretations


def generate_summary_report(stats_results: Dict, df: pd.DataFrame) -> str:
    """
    Generate a text summary of statistical findings.
    
    Args:
        stats_results: Results from perform_statistical_analysis
        df: Original DataFrame
    
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("="*80)
    lines.append("STATISTICAL ANALYSIS SUMMARY")
    lines.append("="*80)
    
    # Overall statistics
    lines.append("\n1. OVERALL READABILITY")
    lines.append("-"*80)
    for metric, stats in stats_results.get('overall', {}).items():
        if stats:
            lines.append(f"\n{metric}:")
            lines.append(f"  Mean: {stats['mean']:.2f} (SD: {stats['std']:.2f})")
            lines.append(f"  Median: {stats['median']:.2f}")
            lines.append(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
    
    # Group comparisons
    lines.append("\n\n2. INSTITUTIONAL VS. PRIVATE COMPARISON")
    lines.append("-"*80)
    for metric, comparison in stats_results.get('comparisons', {}).items():
        if 'error' not in comparison:
            lines.append(f"\n{metric}:")
            lines.append(f"  Test: {comparison['test_used']}")
            lines.append(f"  Institutional mean: {comparison['group1_mean']:.2f}")
            lines.append(f"  Private mean: {comparison['group2_mean']:.2f}")
            lines.append(f"  P-value: {comparison['p_value']:.4f}")
            lines.append(f"  {'*** SIGNIFICANT ***' if comparison['significant'] else 'Not significant'}")
            lines.append(f"  Effect size: {comparison['effect_size']:.3f}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)
    
    # Create sample dataset
    n_institutional = 30
    n_private = 40
    
    test_data = pd.DataFrame({
        'source_type': ['Institutional'] * n_institutional + ['Private'] * n_private,
        'GFI': np.concatenate([
            np.random.normal(10, 2, n_institutional),
            np.random.normal(12, 2.5, n_private)
        ]),
        'SMOG': np.concatenate([
            np.random.normal(11, 2, n_institutional),
            np.random.normal(13, 2.5, n_private)
        ]),
        'FKG': np.concatenate([
            np.random.normal(9.5, 2, n_institutional),
            np.random.normal(11.5, 2.5, n_private)
        ]),
        'ARI': np.concatenate([
            np.random.normal(10.5, 2, n_institutional),
            np.random.normal(12.5, 2.5, n_private)
        ]),
    })
    
    test_data['mean_readability'] = test_data[['GFI', 'SMOG', 'FKG', 'ARI']].mean(axis=1)
    
    print("Running statistical analysis on sample data...")
    results = perform_statistical_analysis(test_data)
    
    summary = generate_summary_report(results, test_data)
    print(summary)
