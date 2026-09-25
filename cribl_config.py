import os

from dotenv import load_dotenv


# Load .env from the current project
load_dotenv()


def load_servers():
    """
    Load Cribl server definitions from environment variables.

    Example:

        CRIBL_SERVERS=cribl01,cribl02

        CRIBL_APPS03_URL=http://cribl01.example.local:9000
        CRIBL_APPS03_TOKEN=...

        CRIBL_APPS04_URL=http://cribl02.example.local:9000
        CRIBL_APPS04_TOKEN=...
    """

    names = os.getenv(
        "CRIBL_SERVERS",
        "",
    )

    if not names:
        raise RuntimeError(
            "CRIBL_SERVERS is not configured."
        )

    servers = {}

    for name in names.split(","):

        name = name.strip()

        if not name:
            continue

        prefix = f"CRIBL_{name.upper()}"

        url = os.getenv(
            f"{prefix}_URL"
        )

        token = os.getenv(
            f"{prefix}_TOKEN"
        )

        if not url:
            raise RuntimeError(
                f"{prefix}_URL is missing."
            )

        if not token:
            raise RuntimeError(
                f"{prefix}_TOKEN is missing."
            )

        servers[name] = {
            "url": url.rstrip("/"),
            "token": token,
        }

    if not servers:
        raise RuntimeError(
            "No Cribl servers have been configured."
        )

    return servers


def verify_ssl():
    """
    Return TLS certificate verification setting.

    CRIBL_VERIFY_SSL=true
    CRIBL_VERIFY_SSL=false
    """

    value = os.getenv(
        "CRIBL_VERIFY_SSL",
        "true",
    )

    return value.lower() in (
        "true",
        "1",
        "yes",
        "on",
    )
