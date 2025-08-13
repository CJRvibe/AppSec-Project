import ipaddress
import socket
from urllib.parse import urlparse
import requests

# Allowed domains (whitelist)
ALLOWED_DOMAINS = ["owasp.org"]

def is_url_safe(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "Invalid scheme"

        hostname = parsed.hostname
        if hostname in ALLOWED_DOMAINS:
            return True, None

        # Resolve to IP
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)

        # No private/internal IPs
        if not ip_obj.is_global:
            return False, f"Blocked private IP {ip}"
        
        return True, None
    except Exception as e:
        return False, str(e)

def safe_fetch(url, **kwargs):
    ok, error = is_url_safe(url)
    if not ok:
        raise ValueError(f"SSRF blocked: {error}")
    return requests.get(url, **kwargs)
