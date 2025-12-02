"""
Visualization module
Creates publication-quality figures for readability analysis
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict
import os
import logging
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12


def create_all_visualizations(df: pd.DataFrame, stats: Dict, output_dir: str, search_term: str) -> List[str]:
    """
    Generate all visualization figures.
    
    Args:
        df: DataFrame with readability data
        stats: Statistical results dictionary
        output_dir: Directory to save figures
        search_term: Search term for filenames
    
    Returns:
        List of created file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    figure_paths = []
    metrics = ['GFI', 'SMOG', 'FKG', 'ARI']
    
    logger.info("Creating visualizations...")
    
    # Box plots for each metric
    for metric in metrics:
        if metric in df.columns:
            filename = os.path.join(output_dir, f"boxplot_{metric}_{search_term}.png")
            create_boxplot(df, metric, stats, filename)
            figure_paths.append(filename)
    
    # Histograms for each metric
    for metric in metrics:
        if metric in df.columns:
            filename = os.path.join(output_dir, f"histogram_{metric}_{search_term}.png")
            create_histogram(df, metric, filename)
            figure_paths.append(filename)
    
    # Summary comparison chart
    filename = os.path.join(output_dir, f"comparison_summary_{search_term}.png")
    create_comparison_chart(stats, filename)
    figure_paths.append(filename)
    
    logger.info(f"Created {len(figure_paths)} figures")
    return figure_paths


def create_boxplot(df: pd.DataFrame, metric: str, stats: Dict, filename: str):
    """Create box plot comparing source types."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create boxplot
    sns.boxplot(data=df, x='source_type', y=metric, palette=['#3498db', '#e74c3c'], ax=ax)
    
    # Add reference line at 8th grade
    ax.axhline(y=8, color='green', linestyle='--', label='Universal Readability (8th grade)', linewidth=2)
    
    # Add p-value annotation if available
    if stats and 'comparisons' in stats and metric in stats['comparisons']:
        comp = stats['comparisons'][metric]
        if 'p_value' in comp:
            p_val = comp['p_value']
            sig_text = f"p = {p_val:.4f}{'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else ' (ns)'}"
            ax.text(0.5, 0.95, sig_text, transform=ax.transAxes, 
                   ha='center', va='top', fontsize=14, weight='bold')
    
    ax.set_xlabel('Source Type', fontsize=14, weight='bold')
    ax.set_ylabel(f'{metric} Score', fontsize=14, weight='bold')
    ax.set_title(f'{metric} Readability by Source Type', fontsize=16, weight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()


def create_histogram(df: pd.DataFrame, metric: str, filename: str):
    """Create histogram showing score distribution."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    data = df[metric].dropna()
    ax.hist(data, bins=20, color='#3498db', edgecolor='black', alpha=0.7)
    
    # Add mean and median lines
    mean_val = data.mean()
    median_val = data.median()
    
    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
    ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.1f}')
    ax.axvline(8, color='orange', linestyle=':', linewidth=2, label='Universal Standard (8th grade)')
    
    ax.set_xlabel(f'{metric} Score', fontsize=14, weight='bold')
    ax.set_ylabel('Frequency', fontsize=14, weight='bold')
    ax.set_title(f'{metric} Distribution', fontsize=16, weight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()


def create_comparison_chart(stats: Dict, filename: str):
    """Create bar chart comparing mean scores by source type."""
    if not stats or 'descriptive' not in stats:
        logger.warning("No statistics available for comparison chart")
        return
    
    metrics = ['GFI', 'SMOG', 'FKG', 'ARI']
    source_types = ['Institutional', 'Private']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(metrics))
    width = 0.35
    
    institutional_means = []
    private_means = []
    institutional_stds = []
    private_stds = []
    
    for metric in metrics:
        if metric in stats['descriptive']:
            inst_stats = stats['descriptive'][metric].get('Institutional', {})
            priv_stats = stats['descriptive'][metric].get('Private', {})
            
            institutional_means.append(inst_stats.get('mean', 0))
            private_means.append(priv_stats.get('mean', 0))
            institutional_stds.append(inst_stats.get('std', 0))
            private_stds.append(priv_stats.get('std', 0))
    
    # Check if we have data to plot
    if not institutional_means and not private_means:
        logger.warning("No data available for comparison chart - skipping")
        plt.close()
        return
    
    # Ensure arrays have correct length
    if len(institutional_means) != len(metrics) or len(private_means) != len(metrics):
        logger.warning("Incomplete data for comparison chart - skipping")
        plt.close()
        return
    
    # Create bars
    ax.bar(x - width/2, institutional_means, width, yerr=institutional_stds,
           label='Institutional', color='#3498db', alpha=0.8, capsize=5)
    ax.bar(x + width/2, private_means, width, yerr=private_stds,
           label='Private', color='#e74c3c', alpha=0.8, capsize=5)
    
    # Universal standard line
    ax.axhline(y=8, color='green', linestyle='--', label='Universal Standard', linewidth=2)
    
    ax.set_ylabel('Mean Readability Score', fontsize=14, weight='bold')
    ax.set_title('Mean Readability Scores by Source Type', fontsize=16, weight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    # Test visualization
    np.random.seed(42)
    test_df = pd.DataFrame({
        'source_type': ['Institutional'] * 50 + ['Private'] * 50,
        'GFI': np.concatenate([np.random.normal(10, 2, 50), np.random.normal(12, 2.5, 50)]),
        'SMOG': np.concatenate([np.random.normal(11, 2, 50), np.random.normal(13, 2.5, 50)]),
        'FKG': np.concatenate([np.random.normal(9.5, 2, 50), np.random.normal(11.5, 2.5, 50)]),
        'ARI': np.concatenate([np.random.normal(10.5, 2, 50), np.random.normal(12.5, 2.5, 50)]),
    })
    
    test_stats = {
        'descriptive': {
            'GFI': {
                'Institutional': {'mean': 10.0, 'std': 2.0},
                'Private': {'mean': 12.0, 'std': 2.5}
            }
        }
    }
    
    os.makedirs('test_figures', exist_ok=True)
    create_all_visualizations(test_df, test_stats, 'test_figures', 'test')
    print("Test figures created in test_figures/")
