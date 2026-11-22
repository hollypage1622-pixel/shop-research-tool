"""Website checker: fetches a shop's website and extracts sales-relevant signals.

Standard library only (urllib + re), so the tool runs anywhere Python 3.10+ does.
"""

from __future__ import annotations

import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field

USER_AGENT = (
    "Mozilla/5.0 (compatible; shop-research-tool/1.0; "
    "+https://github.com/) AppleWebKit/537.36"
)

FREE_BUILDERS = {
    "jimdo": ("jimdofree.com", "jimdosite.com", "jimdo.com"),
    "wix": ("wixsite.com",),
    "weebly": ("weebly.com",),
    "ameba-ownd": ("amebaownd.com",),
    "peraichi": ("peraichi.com",),
    "google-sites": ("sites.google.com",),
    "wordpress-com": ("wordpress.com",),
    "strikingly": ("strikingly.com",),
    "webnode": ("webnode.jp", "webnode.com"),
}

SNS_PATTERNS = {
    "instagram": r"instagram\.com/",
    "x": r"(twitter\.com/|x\.com/)",
    "facebook": r"facebook\.com/",
    "line": r"(line\.me/|lin\.ee/)",
}


@dataclass
class SiteCheck:
    url: str
    reachable: bool = False
    status_code: int | None = None
    final_url: str = ""
    is_https: bool = False
    has_viewport: bool = False  # <meta name="viewport"> -> mobile friendly signal
    free_builder: str = ""
    last_modified: str = ""
    copyright_year: int | None = None
    sns: list[str] = field(default_factory=list)
    has_tel_link: bool = False
    title: str = ""
    error: str = ""


def detect_free_builder(url: str) -> str:
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    for name, domains in FREE_BUILDERS.items():
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    return ""


def parse_html_signals(html: str) -> dict:
    """Extract signals from raw HTML (kept separate for unit testing)."""
    lower = html.lower()
    signals = {
        "has_viewport": 'name="viewport"' in lower or "name='viewport'" in lower,
        "sns": [name for name, pat in SNS_PATTERNS.items() if re.search(pat, lower)],
        "has_tel_link": 'href="tel:' in lower or "href='tel:" in lower,
        "copyright_year": None,
        "title": "",
    }
    years = re.findall(r"(?:©|&copy;|copyright)\s*(\d{4})", lower)
    if years:
        signals["copyright_year"] = max(int(y) for y in years)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        signals["title"] = re.sub(r"\s+", " ", m.group(1)).strip()[:80]
    return signals


def check_site(url: str, timeout: float = 10.0) -> SiteCheck:
    result = SiteCheck(url=url)
    result.free_builder = detect_free_builder(url)
    result.is_https = url.lower().startswith("https://")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # small shops often have broken certs; we only read signals

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            result.reachable = True
            result.status_code = resp.status
            result.final_url = resp.geturl()
            result.last_modified = resp.headers.get("Last-Modified", "")
            if not result.free_builder:
                result.free_builder = detect_free_builder(result.final_url)
            body = resp.read(512_000)  # first 512KB is enough for signal checks
    except urllib.error.HTTPError as exc:
        # A 4xx/5xx still proves the site exists (large chains often 403 bots).
        result.reachable = True
        result.status_code = exc.code
        result.final_url = exc.geturl() or url
        result.error = f"HTTP {exc.code}"
        try:
            body = exc.read(512_000)
        except OSError:
            body = b""
        if not body:
            return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.error = str(exc)[:120]
        return result

    html = body.decode("utf-8", errors="ignore")
    signals = parse_html_signals(html)
    result.has_viewport = signals["has_viewport"]
    result.sns = signals["sns"]
    result.has_tel_link = signals["has_tel_link"]
    result.copyright_year = signals["copyright_year"]
    result.title = signals["title"]
    return result
