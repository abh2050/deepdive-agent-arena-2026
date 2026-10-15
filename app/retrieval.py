"""External web search is not an LLM call. Treat all retrieved pages as untrusted data."""
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from app.models import Evidence
from app.config import SEARCH_RESULTS_PER_QUERY

ALLOWED_SCHEMES = {'http', 'https'}

def source_quality(url: str) -> float:
    host = (urlparse(url).hostname or '').lower()
    if host.endswith(('.gov', '.edu')): return 0.95
    if host in {'who.int', 'worldbank.org', 'iea.org', 'sec.gov'}: return 0.95
    if host.endswith(('.org',)): return 0.7
    return 0.5  # heuristic only; not a truth guarantee

def safe_url(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or '').lower()
    if p.scheme not in ALLOWED_SCHEMES or not host:
        return False
    if p.username or p.password or host == 'localhost' or host.endswith('.local'):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Some HTTP stacks accept legacy integer/octal/hex IPv4 spellings even
        # though ipaddress rejects them (for example, 2130706433 -> 127.0.0.1).
        try:
            address = ipaddress.ip_address(socket.inet_aton(host))
        except OSError:
            return True
    return address.is_global

class WebRetriever:
    def _fetch_page(self, url: str) -> str | None:
        if not safe_url(url):
            return None
        try:
            with httpx.Client(timeout=10, follow_redirects=True, headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 DeepDiveResearch/0.1'}) as client:
                r = client.get(url)
                if not safe_url(str(r.url)):
                    return None
                r.raise_for_status()
                if 'text/html' not in r.headers.get('content-type', ''):
                    return None
                soup = BeautifulSoup(r.text[:600000], 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    tag.decompose()
                extracted = ' '.join(soup.stripped_strings)[:8500]
                if len(extracted) < 100:
                    return None
                return extracted
        except Exception:
            return None

    def search(self, query: str, subquestion: str) -> list[Evidence]:
        output = []
        raw_items = []
        # 1. Try DuckDuckGo text / news
        try:
            try:
                from ddgs import DDGS
            except ImportError:  # Backward compatibility for existing installs.
                from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                try:
                    res = list(ddgs.text(query, max_results=SEARCH_RESULTS_PER_QUERY))
                    if res:
                        raw_items.extend(res)
                except Exception:
                    pass
                if not raw_items:
                    try:
                        news_res = list(ddgs.news(query, max_results=SEARCH_RESULTS_PER_QUERY))
                        if news_res:
                            raw_items.extend(news_res)
                    except Exception:
                        pass
        except Exception:
            pass

        # 2. Wikipedia full-text search fallback if search engine returned nothing
        if not raw_items:
            try:
                import urllib.parse
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&utf8=1"
                with httpx.Client(timeout=8, headers={'User-Agent': 'DeepDiveResearch/0.1 (Research bot)'}) as client:
                    resp = client.get(wiki_url)
                    if resp.status_code == 200:
                        data = resp.json().get('query', {}).get('search', [])
                        for item in data[:SEARCH_RESULTS_PER_QUERY]:
                            title = item.get('title', '')
                            if title:
                                url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                                raw_items.append({'title': title, 'url': url, 'snippet': item.get('snippet', '')})
            except Exception:
                pass

        for item in raw_items:
            url = item.get('href') or item.get('url') or ''
            if not url or not safe_url(url):
                continue
            title = item.get('title') or ''
            extracted = self._fetch_page(url)
            if not extracted:
                continue
            key = hashlib.sha256((url + extracted[:100]).encode()).hexdigest()[:14]
            output.append(Evidence(
                evidence_id='e_' + key,
                subquestion=subquestion,
                url=url,
                title=title,
                excerpt=extracted,
                quality=source_quality(url)
            ))
            if len(output) >= SEARCH_RESULTS_PER_QUERY:
                break
        return output

