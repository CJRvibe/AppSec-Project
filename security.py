import ipaddress
import dns.resolver
from urllib.parse import urlparse
import requests

DOMAINS_ALLOWLIST = ["owasp.org", "example.com"]
DNS_RESOLVER = dns.resolver.Resolver()
DNS_RESOLVER.nameservers = ["1.1.1.1"]  # or Google's 8.8.8.8

def is_valid_ip(ip_str):
    ip = ipaddress.ip_address(ip_str)
    return ip.is_global  # Only allow public IPs

def resolve_domain(domain):
    try:
        answers = DNS_RESOLVER.resolve(domain, "A")  # IPv4
        return [r.to_text() for r in answers]
    except:
        return []

def is_domain_safe(url):
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in ["http", "https"]:
        return False

    # Check hostname
    hostname = parsed.hostname
    if not hostname:
        return False

    # Check if domain is in allowlist (optional, stricter)
    if hostname not in DOMAINS_ALLOWLIST:
        return False

    # DNS resolution safety
    ip_list = resolve_domain(hostname)
    for ip in ip_list:
        if not is_valid_ip(ip):
            return False

    return True

def safe_fetch_url(url):
    if not is_domain_safe(url):
        raise ValueError("Unsafe or disallowed URL.")
    
    response = requests.get(url, timeout=5)
    return response.text
