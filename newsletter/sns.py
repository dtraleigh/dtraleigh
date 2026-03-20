import base64
import logging
import re
from urllib.parse import urlparse

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1, SHA256
from cryptography.x509 import load_pem_x509_certificate

logger = logging.getLogger(__name__)

_cert_cache = {}

_SNS_HOST_PATTERN = re.compile(r"^sns\.[a-z0-9-]+\.amazonaws\.com$")

# Fields used to build the canonical signing string, per SNS message type.
_NOTIFICATION_FIELDS = ("Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type")
_SUBSCRIPTION_FIELDS = ("Message", "MessageId", "SubscribeURL", "Timestamp", "Token", "TopicArn", "Type")


def _validate_cert_url(url):
    """Validate that the SigningCertURL is a legitimate AWS SNS endpoint."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    if not _SNS_HOST_PATTERN.match(parsed.hostname or ""):
        return False
    if not parsed.path.endswith(".pem"):
        return False
    return True


def _get_certificate(url):
    """Fetch and cache the X.509 certificate from the given URL."""
    if url in _cert_cache:
        return _cert_cache[url]

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    cert = load_pem_x509_certificate(response.content)
    _cert_cache[url] = cert
    return cert


def _build_canonical_message(body):
    """Build the canonical signing string per the SNS signature spec."""
    msg_type = body.get("Type", "")
    if msg_type == "Notification":
        fields = _NOTIFICATION_FIELDS
    else:
        fields = _SUBSCRIPTION_FIELDS

    parts = []
    for field in fields:
        value = body.get(field)
        if value is not None:
            parts.append(f"{field}\n{value}\n")
    return "".join(parts)


def verify_sns_signature(body):
    """Verify the cryptographic signature of an SNS message.

    Returns True if the signature is valid, False otherwise.
    """
    cert_url = body.get("SigningCertURL") or body.get("SigningCertUrl", "")
    if not _validate_cert_url(cert_url):
        logger.warning("Invalid SNS SigningCertURL: %s", cert_url)
        return False

    try:
        cert = _get_certificate(cert_url)
    except Exception:
        logger.warning("Failed to fetch SNS signing certificate from %s", cert_url, exc_info=True)
        return False

    canonical = _build_canonical_message(body)
    signature = base64.b64decode(body.get("Signature", ""))

    sig_version = body.get("SignatureVersion", "1")
    if sig_version == "2":
        hash_algo = SHA256()
    else:
        hash_algo = SHA1()

    try:
        cert.public_key().verify(signature, canonical.encode("utf-8"), PKCS1v15(), hash_algo)
        return True
    except InvalidSignature:
        logger.warning("SNS signature verification failed")
        return False
    except Exception:
        logger.warning("SNS signature verification error", exc_info=True)
        return False
