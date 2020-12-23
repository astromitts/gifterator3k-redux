from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests


def _format_site_data(content):
    description = content.head.find('meta', {'property': 'og:description'})
    if description:
        description = description['content']
    else:
        description = None

    title = content.head.find('meta', {'property': 'og:title'})
    if title:
        title = title['content']
    else:
        title = content.title.text

    canonical = content.head.find('link', {'rel': 'canonical'})
    if canonical:
        canonical = canonical['href']
    else:
        canonical = self.target_url
    pagedata = {
        'title': title,
        'description': description,
        'url': canonical,
    }
    return pagedata

def get_offsite_link_metadata(target_url):
    pagedata = {
        'title': None,
        'description': None,
        'url': target_url,
    }
    try:
        req = requests.get(
            target_url,
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
            }
        )

        content = BeautifulSoup(req.content, "html.parser")
        parsed_url = urlparse(target_url)
        # amazon is the woooorrrrst and blocks automated HTTP calls
        if req.status_code == 200:
            if parsed_url.hostname == 'www.amazon.com':
                pagedata = pagedata = {
                    'title': None,
                    'description': None,
                    'url': self.target_url.replace('?{}'.format(parsed_url.query), ''),
                    'image': None,
                }
            else:
                pagedata = _format_site_data(content)
    except Exception:
        pass
    return pagedata
