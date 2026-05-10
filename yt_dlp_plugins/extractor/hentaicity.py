import re
import secrets
from yt_dlp.extractor.common import InfoExtractor

class HentaiCityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hentaicity\.com/[^/]+/(?P<id>[^/?#&]+)'
    _TESTS = [] 

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>(.+?)\s*-\s*HentaiCity</title>', webpage, 'title', 
            default=f"HC_Video_{secrets.token_hex(2)}"
        )

        video_url = self._html_search_regex(
            r'<source[^>]+src=["\']([^"\']+)["\']', webpage, 'source url', default=None
        )

        if not video_url:
            video_url = self._search_regex(
                r'file:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', webpage, 'm3u8 url', default=None
            )

        if not video_url:
            video_url = self._search_regex(
                r'src["\']?\s*:\s*["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', webpage, 'fallback url', fatal=True
            )

        formats = []
        if '.m3u8' in video_url:
            formats = self._extract_m3u8_formats(
                video_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False
            )
        else:
            formats = [{'url': video_url, 'ext': 'mp4'}]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18,
        }
