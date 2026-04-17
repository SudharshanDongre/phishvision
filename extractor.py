"""
PhishVision Feature Extractor
Extracts 30 features from URLs matching the training dataset format.
All features use: -1 (phishing indicator), 0 (suspicious), 1 (legitimate)
"""

import re
import socket
import math
import logging
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PhishVision")

# ============================================================================
# CONSTANTS
# ============================================================================

SHORTENING_SERVICES = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|migre\.me|tiny\.cc|url4\.eu|su\.pr|snipurl\.com|short\.to|wp\.me|bit\.do|lnkd\.in|db\.tt|qr\.ae|adf\.ly|cutt\.ly|rebrand\.ly|shorturl\.at"

SUSPICIOUS_TLDS = {'.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.pw', '.cc', '.su', '.info', '.biz', '.click', '.link', '.work', '.date', '.racing', '.download', '.stream', '.win', '.bid', '.loan', '.trade', '.party', '.science', '.review', '.country', '.kim', '.cricket', '.accountant', '.faith', '.men', '.webcam'}

PHISHING_KEYWORDS = {'login', 'signin', 'sign-in', 'verify', 'secure', 'account', 'update', 'confirm', 'banking', 'password', 'credential', 'suspended', 'unusual', 'verify', 'wallet', 'authenticate', 'validation', 'security', 'alert', 'invoice', 'payment', 'paypal', 'apple', 'microsoft', 'google', 'amazon', 'netflix', 'facebook', 'instagram', 'whatsapp', 'support', 'helpdesk', 'service', 'recover', 'unlock', 'restore'}

TRUSTED_DOMAINS = {'google.com', 'facebook.com', 'amazon.com', 'microsoft.com', 'apple.com', 'github.com', 'stackoverflow.com', 'wikipedia.org', 'linkedin.com', 'twitter.com', 'instagram.com', 'youtube.com', 'netflix.com', 'paypal.com', 'ebay.com', 'reddit.com', 'bing.com', 'yahoo.com', 'outlook.com', 'live.com', 'office.com', 'adobe.com', 'dropbox.com', 'spotify.com', 'zoom.us', 'slack.com'}

SUSPICIOUS_PORTS = {8080, 8443, 8888, 4443, 8000, 3000, 5000, 9000}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def dns_resolves(domain):
    """Check if domain has valid DNS records."""
    try:
        socket.setdefaulttimeout(2)
        socket.getaddrinfo(domain, None)
        return True
    except Exception:
        return False

def get_domain_parts(domain):
    """Extract root domain and subdomain parts."""
    domain = domain.replace("www.", "")
    parts = domain.split(".")
    if len(parts) >= 2:
        root = ".".join(parts[-2:])
        subdomains = parts[:-2]
        return root, subdomains
    return domain, []

def calculate_entropy(text):
    """Calculate Shannon entropy of a string (high entropy = suspicious)."""
    if not text:
        return 0
    prob = {char: text.count(char) / len(text) for char in set(text)}
    return -sum(p * math.log2(p) for p in prob.values())

def count_special_chars(text):
    """Count special characters in text."""
    return len(re.findall(r'[^a-zA-Z0-9.]', text))

def has_brand_impersonation(domain, path):
    """Check if URL tries to impersonate a known brand."""
    combined = (domain + path).lower()
    for brand in ['paypal', 'apple', 'microsoft', 'google', 'amazon', 'facebook', 'netflix', 'instagram', 'whatsapp', 'bank']:
        if brand in combined:
            root, _ = get_domain_parts(domain)
            if brand not in root:
                return True
    return False

# ============================================================================
# RULE-BASED PRE-CHECKS (Catch obvious phishing)
# ============================================================================

def rule_based_check(url, domain, path):
    """
    Quick rule-based checks for obvious phishing patterns.
    Returns: (is_definitely_phishing, reason) or (False, None)
    """
    reasons = []
    
    # Rule 1: IP address as domain
    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ip_pattern, domain.split(":")[0]):
        reasons.append("IP_ADDRESS_DOMAIN")
    
    # Rule 2: Extremely long URL (>200 chars often phishing)
    if len(url) > 200:
        reasons.append("EXTREMELY_LONG_URL")
    
    # Rule 3: Multiple suspicious patterns combined
    suspicious_count = 0
    if "@" in url: suspicious_count += 1
    if "-" in domain and domain.count("-") > 2: suspicious_count += 1
    if has_brand_impersonation(domain, path): suspicious_count += 1
    if any(kw in url.lower() for kw in ['login', 'verify', 'secure', 'account', 'password']): suspicious_count += 1
    
    # Rule 4: Suspicious TLD with phishing keywords
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            if any(kw in url.lower() for kw in PHISHING_KEYWORDS):
                reasons.append("SUSPICIOUS_TLD_WITH_KEYWORDS")
            break
    
    # Rule 5: Data URI or javascript in URL
    if url.lower().startswith("data:") or url.lower().startswith("javascript:"):
        reasons.append("MALICIOUS_URI_SCHEME")
    
    # Rule 6: Excessive subdomains (>4) with phishing keywords
    _, subdomains = get_domain_parts(domain)
    if len(subdomains) > 4:
        reasons.append("EXCESSIVE_SUBDOMAINS")
    
    if reasons:
        return True, reasons
    return False, None

# ============================================================================
# MAIN FEATURE EXTRACTION (30 features matching dataset)
# ============================================================================

def extract_features(url, debug=True):
    """
    Extract 30 features from URL matching the training dataset format.
    
    Feature mapping to dataset columns:
    0: having_IP_Address        1: URL_Length               2: Shortining_Service
    3: having_At_Symbol         4: double_slash_redirecting 5: Prefix_Suffix
    6: having_Sub_Domain        7: SSLfinal_State           8: Domain_registeration_length
    9: Favicon                  10: port                    11: HTTPS_token
    12: Request_URL             13: URL_of_Anchor           14: Links_in_tags
    15: SFH                     16: Submitting_to_email     17: Abnormal_URL
    18: Redirect                19: on_mouseover            20: RightClick
    21: popUpWidnow             22: Iframe                  23: age_of_domain
    24: DNSRecord               25: web_traffic             26: Page_Rank
    27: Google_Index            28: Links_pointing_to_page  29: Statistical_report
    
    Values: -1 (phishing), 0 (suspicious), 1 (legitimate)
    """
    features = []
    
    # Parse URL
    try:
        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        scheme = parsed.scheme.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()
        domain_clean = domain.split(":")[0]
        port = parsed.port
        full_path = path + ("?" + query if query else "")
    except Exception as e:
        logger.error(f"URL parsing error: {e}")
        domain, scheme, path, query, domain_clean, port, full_path = "", "", "", "", "", None, ""
    
    root_domain, subdomains = get_domain_parts(domain_clean)
    
    # Run rule-based pre-check
    is_phishing_by_rules, rule_reasons = rule_based_check(url, domain_clean, path)
    
    # ========================================================================
    # FEATURE 1: having_IP_Address (-1 if IP, 1 if domain)
    # ========================================================================
    ip_pattern = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
    f1 = -1 if re.match(ip_pattern, domain_clean) else 1
    features.append(f1)
    
    # ========================================================================
    # FEATURE 2: URL_Length (-1 if >75, 0 if 54-75, 1 if <54)
    # ========================================================================
    url_len = len(url)
    if url_len < 54:
        f2 = 1
    elif url_len <= 75:
        f2 = 0
    else:
        f2 = -1
    features.append(f2)
    
    # ========================================================================
    # FEATURE 3: Shortining_Service (-1 if uses shortener, 1 otherwise)
    # ========================================================================
    f3 = -1 if re.search(SHORTENING_SERVICES, url, re.IGNORECASE) else 1
    features.append(f3)
    
    # ========================================================================
    # FEATURE 4: having_At_Symbol (-1 if @ present, 1 otherwise)
    # ========================================================================
    f4 = -1 if "@" in url else 1
    features.append(f4)
    
    # ========================================================================
    # FEATURE 5: double_slash_redirecting (-1 if // after position 7, 1 otherwise)
    # ========================================================================
    f5 = -1 if url.rfind("//") > 7 else 1
    features.append(f5)
    
    # ========================================================================
    # FEATURE 6: Prefix_Suffix (-1 if dash in domain, 1 otherwise)
    # ========================================================================
    f6 = -1 if "-" in domain_clean else 1
    features.append(f6)
    
    # ========================================================================
    # FEATURE 7: having_Sub_Domain (-1 if >2 dots, 0 if 2 dots, 1 if <=1 dot)
    # ========================================================================
    dot_count = domain_clean.replace("www.", "").count(".")
    if dot_count <= 1:
        f7 = 1
    elif dot_count == 2:
        f7 = 0
    else:
        f7 = -1
    features.append(f7)
    
    # ========================================================================
    # FEATURE 8: SSLfinal_State (1 if HTTPS with valid cert pattern, -1 otherwise)
    # ========================================================================
    if scheme == "https":
        # Additional check: trusted domain gets 1, suspicious gets 0
        if root_domain in TRUSTED_DOMAINS:
            f8 = 1
        else:
            f8 = 1  # HTTPS is still good
    else:
        f8 = -1
    features.append(f8)
    
    # ========================================================================
    # FEATURE 9: Domain_registeration_length (heuristic based on domain characteristics)
    # Short/random domains likely have short registration
    # ========================================================================
    domain_entropy = calculate_entropy(domain_clean.replace(".", ""))
    if root_domain in TRUSTED_DOMAINS:
        f9 = 1  # Trusted = long registration
    elif domain_entropy > 4.0 or len(root_domain.split(".")[0]) < 4:
        f9 = -1  # High entropy or very short = likely short registration
    else:
        f9 = 0  # Unknown
    features.append(f9)
    
    # ========================================================================
    # FEATURE 10: Favicon (heuristic: suspicious TLD or IP = likely no proper favicon)
    # ========================================================================
    if f1 == -1:  # IP address
        f10 = -1
    elif any(domain_clean.endswith(tld) for tld in SUSPICIOUS_TLDS):
        f10 = -1
    elif root_domain in TRUSTED_DOMAINS:
        f10 = 1
    else:
        f10 = 1  # Assume most sites have favicons
    features.append(f10)
    
    # ========================================================================
    # FEATURE 11: port (-1 if non-standard port, 1 otherwise)
    # ========================================================================
    if port and port not in [80, 443]:
        f11 = -1
    elif ":" in domain and any(str(p) in domain for p in SUSPICIOUS_PORTS):
        f11 = -1
    else:
        f11 = 1
    features.append(f11)
    
    # ========================================================================
    # FEATURE 12: HTTPS_token (-1 if "https" appears in domain, 1 otherwise)
    # Phishers put "https" in domain to look legitimate
    # ========================================================================
    f12 = -1 if "https" in domain_clean or "http" in domain_clean else 1
    features.append(f12)
    
    # ========================================================================
    # FEATURE 13: Request_URL (heuristic: external resources indicator)
    # ========================================================================
    # Can't check actual page content, use URL patterns
    if len(subdomains) > 2 or has_brand_impersonation(domain_clean, path):
        f13 = -1
    elif root_domain in TRUSTED_DOMAINS:
        f13 = 1
    else:
        f13 = 0
    features.append(f13)
    
    # ========================================================================
    # FEATURE 14: URL_of_Anchor (heuristic based on URL structure)
    # ========================================================================
    # Suspicious if path contains many special chars or looks obfuscated
    path_special_chars = count_special_chars(path)
    if path_special_chars > 10:
        f14 = -1
    elif path_special_chars > 5:
        f14 = 0
    else:
        f14 = 1
    features.append(f14)
    
    # ========================================================================
    # FEATURE 15: Links_in_tags (heuristic)
    # ========================================================================
    # Use similar logic to Request_URL
    f15 = f13
    features.append(f15)
    
    # ========================================================================
    # FEATURE 16: SFH (Server Form Handler - heuristic)
    # Check for form/login indicators in path
    # ========================================================================
    form_indicators = ['login', 'signin', 'auth', 'submit', 'form', 'verify', 'confirm']
    if any(ind in full_path for ind in form_indicators):
        if root_domain not in TRUSTED_DOMAINS:
            f16 = -1
        else:
            f16 = 1
    else:
        f16 = 1
    features.append(f16)
    
    # ========================================================================
    # FEATURE 17: Submitting_to_email (-1 if mailto: in URL, 1 otherwise)
    # ========================================================================
    f17 = -1 if "mailto:" in url.lower() or "mail=" in query else 1
    features.append(f17)
    
    # ========================================================================
    # FEATURE 18: Abnormal_URL (heuristic: domain mismatch indicators)
    # ========================================================================
    if has_brand_impersonation(domain_clean, path):
        f18 = -1
    elif f1 == -1 or f7 == -1:  # IP or many subdomains
        f18 = -1
    elif root_domain in TRUSTED_DOMAINS:
        f18 = 1
    else:
        f18 = 1
    features.append(f18)
    
    # ========================================================================
    # FEATURE 19: Redirect (heuristic: multiple redirects in URL)
    # ========================================================================
    redirect_count = url.count("//") - 1 + url.lower().count("redirect") + url.lower().count("url=")
    if redirect_count >= 2:
        f19 = -1
    elif redirect_count == 1:
        f19 = 0
    else:
        f19 = 0  # Can't determine without page content
    features.append(f19)
    
    # ========================================================================
    # FEATURE 20: on_mouseover (can't check without JS, use heuristic)
    # ========================================================================
    # Suspicious domains more likely to use this trick
    if is_phishing_by_rules:
        f20 = -1
    else:
        f20 = 1
    features.append(f20)
    
    # ========================================================================
    # FEATURE 21: RightClick (can't check without page, use heuristic)
    # ========================================================================
    f21 = 1 if root_domain in TRUSTED_DOMAINS else 1
    features.append(f21)
    
    # ========================================================================
    # FEATURE 22: popUpWidnow (can't check without page, use heuristic)
    # ========================================================================
    # Suspicious patterns indicate popups likely
    if any(domain_clean.endswith(tld) for tld in SUSPICIOUS_TLDS) and f16 == -1:
        f22 = -1
    else:
        f22 = 1
    features.append(f22)
    
    # ========================================================================
    # FEATURE 23: Iframe (can't check without page, use heuristic)
    # ========================================================================
    f23 = 1  # Default to legitimate
    features.append(f23)
    
    # ========================================================================
    # FEATURE 24: age_of_domain (heuristic based on domain characteristics)
    # ========================================================================
    if root_domain in TRUSTED_DOMAINS:
        f24 = 1  # Old domain
    elif any(domain_clean.endswith(tld) for tld in SUSPICIOUS_TLDS):
        f24 = -1  # Likely new
    elif domain_entropy > 4.0:
        f24 = -1  # Random-looking = new
    else:
        f24 = 0  # Unknown
    features.append(f24)
    
    # ========================================================================
    # FEATURE 25: DNSRecord (check if domain resolves)
    # ========================================================================
    try:
        has_dns = dns_resolves(domain_clean)
        f25 = 1 if has_dns else -1
    except:
        f25 = 0  # Unknown
    features.append(f25)
    
    # ========================================================================
    # FEATURE 26: web_traffic (heuristic: trusted = high traffic)
    # ========================================================================
    if root_domain in TRUSTED_DOMAINS:
        f26 = 1
    elif any(domain_clean.endswith(tld) for tld in SUSPICIOUS_TLDS):
        f26 = -1
    else:
        f26 = 0
    features.append(f26)
    
    # ========================================================================
    # FEATURE 27: Page_Rank (heuristic based on domain reputation)
    # ========================================================================
    if root_domain in TRUSTED_DOMAINS:
        f27 = 1
    elif is_phishing_by_rules:
        f27 = -1
    else:
        f27 = 0
    features.append(f27)
    
    # ========================================================================
    # FEATURE 28: Google_Index (heuristic: trusted domains are indexed)
    # ========================================================================
    if root_domain in TRUSTED_DOMAINS:
        f28 = 1
    elif f1 == -1:  # IP addresses usually not indexed
        f28 = -1
    else:
        f28 = 1  # Most sites are indexed
    features.append(f28)
    
    # ========================================================================
    # FEATURE 29: Links_pointing_to_page (heuristic)
    # ========================================================================
    if root_domain in TRUSTED_DOMAINS:
        f29 = 1
    elif any(domain_clean.endswith(tld) for tld in SUSPICIOUS_TLDS):
        f29 = -1
    else:
        f29 = 0
    features.append(f29)
    
    # ========================================================================
    # FEATURE 30: Statistical_report (heuristic: flagged by rules = bad)
    # ========================================================================
    if is_phishing_by_rules:
        f30 = -1
    elif root_domain in TRUSTED_DOMAINS:
        f30 = 1
    else:
        f30 = 1  # Default
    features.append(f30)
    
    # ========================================================================
    # DEBUG LOGGING
    # ========================================================================
    if debug:
        feature_names = [
            "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
            "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State",
            "Domain_registeration_length", "Favicon", "port", "HTTPS_token",
            "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
            "Submitting_to_email", "Abnormal_URL", "Redirect", "on_mouseover",
            "RightClick", "popUpWidnow", "Iframe", "age_of_domain",
            "DNSRecord", "web_traffic", "Page_Rank", "Google_Index",
            "Links_pointing_to_page", "Statistical_report"
        ]
        logger.debug(f"\n{'='*60}")
        logger.debug(f"URL: {url}")
        logger.debug(f"Domain: {domain_clean} | Root: {root_domain}")
        logger.debug(f"Rule-based phishing: {is_phishing_by_rules} | Reasons: {rule_reasons}")
        logger.debug(f"Features:")
        for i, (name, val) in enumerate(zip(feature_names, features)):
            indicator = "⚠️" if val == -1 else ("❓" if val == 0 else "✓")
            logger.debug(f"  {i+1:2}. {name:30} = {val:2} {indicator}")
        logger.debug(f"Phishing indicators (=-1): {features.count(-1)}/30")
        logger.debug(f"{'='*60}\n")
    
    return features


def get_feature_summary(url):
    """Get a human-readable summary of feature extraction."""
    features = extract_features(url, debug=False)
    phishing_count = features.count(-1)
    suspicious_count = features.count(0)
    safe_count = features.count(1)
    
    return {
        "url": url,
        "features": features,
        "phishing_indicators": phishing_count,
        "suspicious_indicators": suspicious_count,
        "safe_indicators": safe_count,
        "risk_score": round((phishing_count * 2 + suspicious_count) / 60 * 100, 1)
    }