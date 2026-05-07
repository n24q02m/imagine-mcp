<<<<<<< SEARCH
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateRequest:
    media_type: str
    prompt: str
    provider: str | None
    tier: str
    reference_image_url: str | None = None
    job_id: str | None = None
    aspect_ratio: str = "16:9"
    duration_seconds: int = 8


import concurrent.futures
=======
from __future__ import annotations

import concurrent.futures
import importlib
import ipaddress
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    InvalidURLError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import detect_media_type
from imagine_mcp.models import UNSUPPORTED, get_model_id


@dataclass(frozen=True)
class GenerateRequest:
    media_type: str
    prompt: str
    provider: str | None
    tier: str
    reference_image_url: str | None = None
    job_id: str | None = None
    aspect_ratio: str = "16:9"
    duration_seconds: int = 8
>>>>>>> REPLACE
<<<<<<< SEARCH
import importlib
import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    InvalidURLError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import detect_media_type
from imagine_mcp.models import UNSUPPORTED, get_model_id
=======
>>>>>>> REPLACE
