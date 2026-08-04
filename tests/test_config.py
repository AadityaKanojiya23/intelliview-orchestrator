import os
from unittest.mock import MagicMock, patch
import pytest

from config import Settings, get_aws_secrets


def test_local_dev_fallback(monkeypatch):
    """Test that local dev settings load cleanly from environment/defaults."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")

    settings = Settings()
    assert settings.environment == "development"
    assert settings.postgres_host == "localhost"


@patch("boto3.session.Session")
def test_production_aws_secrets(mock_session_class, monkeypatch):
    """Test that production environment fetches and overrides settings from AWS Secrets Manager."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AWS_SECRET_NAME", "test-secrets")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    # Clear LRU cache before testing
    get_aws_secrets.cache_clear()

    # Mock AWS client call
    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {
        "SecretString": '{"POSTGRES_HOST": "prod-db-cluster.aws.com", "POSTGRES_USER": "prod_user"}'
    }
    mock_session_class.return_value.client.return_value = mock_client

    settings = Settings()

    assert settings.postgres_host == "prod-db-cluster.aws.com"
    assert settings.postgres_user == "prod_user"
    mock_client.get_secret_value.assert_called_once_with(SecretId="test-secrets")