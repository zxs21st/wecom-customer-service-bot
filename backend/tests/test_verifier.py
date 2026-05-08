import pytest
from unittest.mock import patch, MagicMock
from app.gateway.verifier import verify_url, decrypt_message, verify_signature


def test_verify_url_success():
    with patch("app.gateway.verifier.get_crypto") as mock_crypto:
        mock_instance = MagicMock()
        mock_instance.check_signature.return_value = "verified_echostr"
        mock_crypto.return_value = mock_instance

        result = verify_url("sig", "123", "nonce", "echo")
        assert result == "verified_echostr"
        mock_instance.check_signature.assert_called_once_with("sig", "123", "nonce", "echo")


def test_verify_signature_valid():
    with patch("app.gateway.verifier.decrypt_message") as mock_decrypt:
        mock_decrypt.return_value = "<xml>...</xml>"
        assert verify_signature("sig", "123", "nonce", "<encrypted>") is True


def test_verify_signature_invalid():
    with patch("app.gateway.verifier.decrypt_message") as mock_decrypt:
        from wechatpy.exceptions import InvalidSignatureException
        mock_decrypt.side_effect = InvalidSignatureException
        assert verify_signature("bad", "123", "nonce", "<encrypted>") is False
