"""
Evaluation script for crop recommendation model.

This script evaluates the trained Random Forest model with detailed metrics,
including accuracy, precision, recall, and confusion matrix visualization.

Usage:
    python scripts/evaluate_crop_recommendation.py
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)

from app.utils.model_loader import ModelLoader
from config import DATA_PATHS, MODEL_PATHS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate_model():
    """
    Comprehensive evaluation of the crop recommendation model.
    """
    try:
        logger.info("=" * 60)
        logger.info("Evaluating Crop Recommendation Model")
        logger.info("=" * 60)
        
        # Load dataset
        logger.info(f"\nLoading dataset from: {DATA_PATHS['crop_dataset']}")
        df = pd.read_csv(str(DATA_PATHS['crop_dataset']))
        
        # Prepare data
        feature_columns = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        X = df[feature_columns]
        y = df['label']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Load trained model
        logger.info(f"\nLoading model from: {MODEL_PATHS['crop_recommendation']}")
        model = ModelLoader.load_crop_recommendation_model(str(MODEL_PATHS['crop_recommendation']))
        
        # Make predictions
        logger.info("\nGenerating predictions...")
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        logger.info("\n" + "=" * 60)
        logger.info("Performance Metrics")
        logger.info("=" * 60)
        
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        precision = precision_score(y_test, y_pred_test, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred_test, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred_test, average='weighted', zero_division=0)
        
        logger.info(f"\n✅ Training Accuracy: {train_acc:.4f} ({train_acc*100:.2f}%)")
        logger.info(f"✅ Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
        logger.info(f"✅ Precision (weighted): {precision:.4f}")
        logger.info(f"✅ Recall (weighted): {recall:.4f}")
        logger.info(f"✅ F1-Score (weighted): {f1:.4f}")
        
        # Classification report
        logger.info("\n" + "=" * 60)
        logger.info("Classification Report (Top 5 Classes)")
        logger.info("=" * 60)
        report = classification_report(y_test, y_pred_test, output_dict=True)
        
        # Get top classes by support
        class_support = {
            k: v['support'] for k, v in report.items()
            if k not in ['accuracy', 'macro avg', 'weighted avg']
        }
        top_classes = sorted(class_support.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for crop, support in top_classes:
            metrics = report[crop]
            logger.info(f"\n{crop}:")
            logger.info(f"  Precision: {metrics['precision']:.3f}")
            logger.info(f"  Recall: {metrics['recall']:.3f}")
            logger.info(f"  F1-Score: {metrics['f1-score']:.3f}")
            logger.info(f"  Support: {int(metrics['support'])}")
        
        # Confusion matrix
        logger.info("\nGenerating confusion matrix...")
        cm = confusion_matrix(y_test, y_pred_test, labels=model.classes_)
        
        plt.figure(figsize=(14, 10))
        sns.heatmap(cm, annot=False, fmt="d", cmap="Blues",
                   xticklabels=model.classes_,
                   yticklabels=model.classes_,
                   cbar_kws={'label': 'Count'})
        plt.title("Confusion Matrix - Crop Recommendation Model")
        plt.xlabel("Predicted Label")
        plt.ylabel("Actual Label")
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        confusion_matrix_path = project_root / 'confusion_matrix.png'
        plt.savefig(confusion_matrix_path, dpi=100, bbox_inches='tight')
        logger.info(f"✅ Confusion matrix saved to: {confusion_matrix_path}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Evaluation Complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error during evaluation: {str(e)}")
        raise


if __name__ == '__main__':
    # Fix project_root reference
    project_root = Path(__file__).resolve().parent.parent
    evaluate_model()
