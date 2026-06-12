"""
Prediction utilities and testing scripts.
Provides CLI interface for testing disease detection and crop recommendations.

Usage:
    python scripts/test_predictions.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.disease_detection import DiseaseDetectionService
from app.services.crop_recommendation import CropRecommendationService


def test_disease_detection():
    """Test disease detection service."""
    print("\n" + "=" * 60)
    print("Testing Disease Detection Service")
    print("=" * 60)
    
    try:
        service = DiseaseDetectionService()
        print("✅ Disease detection service loaded successfully")
        print("Available classes:", service.classes)
    except Exception as e:
        print(f"❌ Error loading disease detection service: {str(e)}")


def test_crop_recommendation():
    """Test crop recommendation service."""
    print("\n" + "=" * 60)
    print("Testing Crop Recommendation Service")
    print("=" * 60)
    
    try:
        service = CropRecommendationService()
        print("✅ Crop recommendation service loaded successfully")
        
        crops = service.get_available_crops()
        print(f"✅ Available crops: {len(crops)} total")
        print(f"   Sample crops: {', '.join(crops[:5])}")
        
        # Test NPK prediction
        test_crop = 'rice'
        if test_crop in crops:
            result = service.predict_npk(test_crop, {
                'temperature': 24.0,
                'humidity': 80.0,
                'ph': 6.5,
                'rainfall': 220.0
            })
            print(f"\n✅ NPK Prediction for {test_crop}:")
            print(f"   N: {result['N']} kg/ha")
            print(f"   P: {result['P']} kg/ha")
            print(f"   K: {result['K']} kg/ha")
        
        # Test crop recommendation
        recommendation = service.recommend_crop(
            temperature=24.0,
            humidity=80.0,
            ph=6.5,
            rainfall=220.0
        )
        print(f"\n✅ Crop Recommendation: {recommendation['recommended_crop']}")
        
    except Exception as e:
        print(f"❌ Error in crop recommendation service: {str(e)}")


if __name__ == '__main__':
    test_disease_detection()
    test_crop_recommendation()
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
