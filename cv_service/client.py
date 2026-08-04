import os
import requests


class CVClient:
    """Client for communicating with the CV microservice."""

    def __init__(self):
        self.base_url = os.getenv(
            "CV_SERVICE_URL",
            "http://localhost:8001",
        )

    def analyze_video(self, session_id: str) -> dict:
        """Send a video analysis request to the CV service."""
        response = requests.post(
            f"{self.base_url}/analyze-video",
            json={"session_id": session_id},
            timeout=120,
        )

        response.raise_for_status()

        return response.json()