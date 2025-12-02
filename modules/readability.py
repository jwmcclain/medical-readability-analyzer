"""
Readability calculation module
Calculates multiple readability metrics for text content
Uses textstat library for validated formulas
"""

import textstat
import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_readability(text: str) -> Optional[Dict[str, float]]:
    """
    Calculate all readability metrics for given text.
    
    Args:
        text: Cleaned text content
    
    Returns:
        Dictionary with readability scores or None if text too short
    """
    if not text:
        logger.warning("Empty text provided for readability calculation")
        return None
    
    # Validate text length
    words = text.split()
    word_count = len(words)
    
    if word_count < config.MIN_WORD_COUNT:
        logger.warning(f"Text too short for analysis: {word_count} words")
        return None
    
    try:
        # Calculate all four required metrics
        metrics = {
            'GFI': textstat.gunning_fog(text),
            'SMOG': textstat.smog_index(text),
            'FKG': textstat.flesch_kincaid_grade(text),
            'ARI': textstat.automated_readability_index(text),
            'word_count': word_count,
            'sentence_count': textstat.sentence_count(text),
            'syllable_count': textstat.syllable_count(text),
        }
        
        # Validate scores
        for key in ['GFI', 'SMOG', 'FKG', 'ARI']:
            value = metrics[key]
            if pd.isna(value) or value < 0 or value > 30:
                logger.warning(f"Unusual {key} score: {value}")
                metrics[key] = None
        
        # Calculate mean readability (average of 4 metrics)
        valid_scores = [v for k, v in metrics.items() 
                       if k in ['GFI', 'SMOG', 'FKG', 'ARI'] and v is not None]
        
        if valid_scores:
            metrics['mean_readability'] = np.mean(valid_scores)
        else:
            metrics['mean_readability'] = None
        
        logger.info(f"Readability calculated - Mean: {metrics.get('mean_readability', 'N/A'):.1f}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating readability: {e}")
        return None


def batch_calculate_readability(texts: list) -> list:
    """
    Calculate readability for multiple texts.
    
    Args:
        texts: List of text strings
    
    Returns:
        List of readability dictionaries
    """
    results = []
    
    for i, text in enumerate(texts):
        logger.info(f"Processing text {i+1}/{len(texts)}")
        metrics = calculate_readability(text)
        results.append(metrics)
    
    return results


def categorize_readability(score: float) -> str:
    """
    Categorize readability score into levels.
    
    Args:
        score: Readability score (grade level)
    
    Returns:
        Category string
    """
    if pd.isna(score):
        return "Unknown"
    elif score <= 8:
        return "Universal (≤8th grade)"
    elif score <= 10:
        return "Acceptable (8-10th grade)"
    else:
        return "Difficult (>10th grade)"


def get_readability_interpretation(metric: str, score: float) -> str:
    """
    Get human-readable interpretation of readability score.
    
    Args:
        metric: Metric name (GFI, SMOG, FKG, ARI)
        score: Numeric score
    
    Returns:
        Interpretation string
    """
    if pd.isna(score):
        return "Score not available"
    
    if metric in ['GFI', 'FKG', 'ARI']:
        return f"Grade {int(score)} reading level"
    elif metric == 'SMOG':
        return f"Grade {int(score)} comprehension level"
    else:
        return f"Score: {score:.1f}"


def compare_to_standards(scores: Dict[str, float]) -> Dict[str, str]:
    """
    Compare readability scores to recommended standards.
    
    Args:
        scores: Dictionary of readability scores
    
    Returns:
        Dictionary of comparisons to standards
    """
    comparisons = {}
    
    # NIH recommends 7th-8th grade
    # AMA recommends 6th grade
    standards = {
        'NIH': 8.0,
        'AMA': 6.0,
        'Universal': 8.0
    }
    
    for metric in ['GFI', 'SMOG', 'FKG', 'ARI']:
        score = scores.get(metric)
        if score and not pd.isna(score):
            if score <= standards['AMA']:
                comparisons[metric] = "Excellent - Meets AMA standard (≤6th grade)"
            elif score <= standards['NIH']:
                comparisons[metric] = "Good - Meets NIH standard (≤8th grade)"
            elif score <= 10:
                comparisons[metric] = "Acceptable - Within reasonable range"
            else:
                comparisons[metric] = "Poor - Exceeds recommended levels"
        else:
            comparisons[metric] = "Not available"
    
    return comparisons


def analyze_readability_distribution(scores_list: list) -> Dict:
    """
    Analyze distribution of readability scores.
    
    Args:
        scores_list: List of readability dictionaries
    
    Returns:
        Statistics dictionary
    """
    # Extract valid scores for each metric
    metrics_data = {
        'GFI': [],
        'SMOG': [],
        'FKG': [],
        'ARI': [],
        'mean_readability': []
    }
    
    for scores in scores_list:
        if scores:
            for metric in metrics_data.keys():
                value = scores.get(metric)
                if value is not None and not pd.isna(value):
                    metrics_data[metric].append(value)
    
    # Calculate statistics
    stats = {}
    for metric, values in metrics_data.items():
        if values:
            stats[metric] = {
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'count': len(values),
                'universal_count': sum(1 for v in values if v <= 8),
                'universal_pct': sum(1 for v in values if v <= 8) / len(values) * 100
            }
        else:
            stats[metric] = None
    
    return stats


def validate_readability_consistency(scores: Dict[str, float], threshold: float = 10.0) -> tuple:
    """
    Check if readability scores are consistent across metrics.
    
    Args:
        scores: Dictionary of readability scores
        threshold: Maximum acceptable difference between metrics
    
    Returns:
        Tuple of (is_consistent, message)
    """
    metric_scores = [scores.get(m) for m in ['GFI', 'SMOG', 'FKG', 'ARI']
                     if scores.get(m) is not None and not pd.isna(scores.get(m))]
    
    if len(metric_scores) < 2:
        return True, "Insufficient scores for consistency check"
    
    score_range = max(metric_scores) - min(metric_scores)
    
    if score_range > threshold:
        return False, f"Large discrepancy between metrics (range: {score_range:.1f})"
    else:
        return True, f"Scores are consistent (range: {score_range:.1f})"


if __name__ == "__main__":
    # Test the readability module
    test_text = """
    Hypertension, also known as high blood pressure, is a common condition. 
    It occurs when the force of the blood against your artery walls is too high.
    Over time, high blood pressure can lead to health problems such as heart disease.
    Blood pressure is determined by the amount of blood your heart pumps and the resistance to blood flow in your arteries.
    The more blood your heart pumps and the narrower your arteries, the higher your blood pressure.
    You can have high blood pressure for years without any symptoms.
    Even without symptoms, damage to blood vessels and your heart continues and can be detected.
    Uncontrolled high blood pressure increases your risk of serious health problems.
    High blood pressure generally develops over many years.
    It can affect nearly everyone eventually.
    Fortunately, high blood pressure can be easily detected.
    Once you know you have high blood pressure, you can work with your doctor to control it.
    """
    
    print("\nCalculating readability for test text...")
    print("="*80)
    
    metrics = calculate_readability(test_text)
    
    if metrics:
        print(f"\nWord count: {metrics['word_count']}")
        print(f"Sentence count: {metrics['sentence_count']}")
        print(f"\nReadability Scores:")
        print(f"  Gunning Fog Index (GFI):           {metrics['GFI']:.2f}")
        print(f"  SMOG Index:                        {metrics['SMOG']:.2f}")
        print(f"  Flesch-Kincaid Grade (FKG):        {metrics['FKG']:.2f}")
        print(f"  Automated Readability Index (ARI): {metrics['ARI']:.2f}")
        print(f"  Mean Readability:                  {metrics['mean_readability']:.2f}")
        
        print(f"\nCategory: {categorize_readability(metrics['mean_readability'])}")
        
        print(f"\nStandards Comparison:")
        comparisons = compare_to_standards(metrics)
        for metric, comparison in comparisons.items():
            print(f"  {metric}: {comparison}")
        
        is_consistent, msg = validate_readability_consistency(metrics)
        print(f"\nConsistency check: {msg}")
