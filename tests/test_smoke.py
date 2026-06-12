"""Smoke tests — verify app factory and key endpoints."""
import pytest

from app import create_app
from config import DATA_PATHS, MODEL_PATHS


@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_artifact_paths_exist():
    assert MODEL_PATHS["disease_detection"].is_file()
    assert MODEL_PATHS["crop_recommendation"].is_file()
    assert MODEL_PATHS["crop_options"].is_file()
    assert DATA_PATHS["crop_dataset"].is_file()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AgriSense" in response.data or b"disease" in response.data.lower()


def test_predict_missing_image(client):
    response = client.post("/predict", json={})
    assert response.status_code == 400


def test_available_crops(client):
    response = client.get("/api/recommendation/available-crops")
    assert response.status_code == 200
    data = response.get_json()
    assert "crops" in data
    assert data["count"] > 0


def test_recommend_crop(client):
    response = client.post(
        "/api/recommendation/recommend-crop",
        json={"temperature": 25, "humidity": 80, "ph": 6.5, "rainfall": 200},
    )
    assert response.status_code == 200
    assert "recommended_crop" in response.get_json()
