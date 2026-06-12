"""
Exploratory Data Analysis (EDA) script.

Generates visualizations and statistics for the crop recommendation dataset.

Usage:
    python scripts/eda.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import DATA_PATHS

# Set style
sns.set_style("whitegrid")


def exploratory_data_analysis():
    """
    Perform exploratory data analysis on crop dataset.
    """
    print("=" * 60)
    print("Crop Dataset - Exploratory Data Analysis")
    print("=" * 60)
    
    # Load dataset
    df = pd.read_csv(str(DATA_PATHS['crop_dataset']))
    
    # Basic statistics
    print(f"\nDataset Shape: {df.shape}")
    print(f"Features: {list(df.columns)}")
    print(f"\nData Types:\n{df.dtypes}")
    print(f"\nMissing Values:\n{df.isnull().sum()}")
    
    # Statistics per feature
    print("\n" + "=" * 60)
    print("Feature Statistics")
    print("=" * 60)
    print(df.describe())
    
    # Crop distribution
    print("\n" + "=" * 60)
    print("Crop Distribution")
    print("=" * 60)
    crop_counts = df['label'].value_counts()
    print(f"Total unique crops: {len(crop_counts)}")
    print(f"\nTop 10 crops:")
    print(crop_counts.head(10))
    
    # Generate visualizations
    print("\n" + "=" * 60)
    print("Generating visualizations...")
    print("=" * 60)
    
    # 1. Crop distribution
    fig, ax = plt.subplots(figsize=(14, 6))
    crop_counts.head(15).plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title("Top 15 Crops in Dataset")
    ax.set_xlabel("Crop Type")
    ax.set_ylabel("Count")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(str(project_root / 'crop_distribution.png'), dpi=100, bbox_inches='tight')
    print("✅ Saved: crop_distribution.png")
    
    # 2. Feature correlation
    fig, ax = plt.subplots(figsize=(10, 8))
    correlation = df.drop(columns=['label']).corr()
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0, ax=ax, fmt='.2f')
    ax.set_title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(str(project_root / 'feature_correlation.png'), dpi=100, bbox_inches='tight')
    print("✅ Saved: feature_correlation.png")
    
    # 3. Feature distributions
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    for idx, feature in enumerate(features[:6]):
        ax = axes[idx // 3, idx % 3]
        df[feature].hist(bins=30, ax=ax, color='steelblue', edgecolor='black')
        ax.set_title(f"{feature} Distribution")
        ax.set_xlabel(feature)
        ax.set_ylabel("Frequency")
    
    plt.tight_layout()
    plt.savefig(str(project_root / 'feature_distributions.png'), dpi=100, bbox_inches='tight')
    print("✅ Saved: feature_distributions.png")
    
    print("\n" + "=" * 60)
    print("EDA Complete!")
    print("=" * 60)


if __name__ == '__main__':
    exploratory_data_analysis()
