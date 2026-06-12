"""
Training script for crop recommendation model (NPK prediction).

This script trains a Random Forest classifier to recommend optimal NPK
fertilizer amounts based on crop type and environmental conditions.

Usage:
    python scripts/train_crop_recommendation.py
"""
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

import joblib

from config import CROP_FEATURE_COLUMNS, DATA_PATHS, MODEL_PATHS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_crop_recommendation_model():
    """
    Train Random Forest classifier for crop recommendation.
    
    The model predicts:
    - Optimal crop type based on environmental conditions
    - NPK fertilizer amounts for recommended crops
    
    Model Details:
    - Algorithm: Random Forest Classifier
    - N Estimators: 400 trees
    - Features: N, P, K, temperature, humidity, pH, rainfall
    - Target: Crop label
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Crop Recommendation Model Training")
        logger.info("=" * 60)
        
        # Load dataset
        dataset_path = str(DATA_PATHS['crop_dataset'])
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        
        logger.info(f"Loading dataset from: {dataset_path}")
        df = pd.read_csv(dataset_path)
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Unique crops: {df['label'].nunique()}")
        
        # Define features and target
        feature_columns = CROP_FEATURE_COLUMNS
        X = df[feature_columns]
        y = df['label']
        
        logger.info(f"Features: {feature_columns}")
        logger.info(f"Target: label (crop type)")
        
        # Split data
        logger.info("\nSplitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        # Create pipeline with scaling + Random Forest
        logger.info("\nBuilding model pipeline...")
        pipe = Pipeline(steps=[
            ('scaler', StandardScaler()),
            ('clf', RandomForestClassifier(
                n_estimators=400,
                random_state=42,
                n_jobs=-1,
                verbose=1
            ))
        ])
        
        # Train model
        logger.info("Training Random Forest model...")
        pipe.fit(X_train, y_train)
        logger.info("✅ Model training completed")
        
        # Evaluate model
        logger.info("\nEvaluating model...")
        y_pred = pipe.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save model pipeline
        logger.info("\nSaving model...")
        os.makedirs(str(MODEL_PATHS['crop_recommendation'].parent), exist_ok=True)
        model_save_path = str(MODEL_PATHS['crop_recommendation'])
        joblib.dump(pipe, model_save_path)
        logger.info(f"✅ Model pipeline saved to: {model_save_path}")
        
        # Save crop options
        crop_list = sorted(df['label'].unique().tolist())
        options_save_path = str(MODEL_PATHS['crop_options'])
        joblib.dump(crop_list, options_save_path)
        logger.info(f"✅ Crop options saved to: {options_save_path}")
        logger.info(f"   Total crops: {len(crop_list)}")
        logger.info(f"   Sample crops: {', '.join(crop_list[:5])}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Training Completed Successfully!")
        logger.info("=" * 60)
        logger.info(f"Model Accuracy: {accuracy:.4f}")
        logger.info(f"Trained on: {len(crop_list)} crop types")
        logger.info(f"Model files saved to: {MODEL_PATHS['crop_recommendation'].parent}")
        
        return pipe, crop_list, accuracy
        
    except Exception as e:
        logger.error(f"❌ Error during model training: {str(e)}")
        raise


if __name__ == '__main__':
    train_crop_recommendation_model()
