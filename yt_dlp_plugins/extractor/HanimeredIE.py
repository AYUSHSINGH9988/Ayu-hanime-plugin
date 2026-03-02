import json
import re
import time
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, int_or_none, str_or_none

class HanimeRedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.red/(?:(?:videos/hentai|hentai/video)/)?(?P<id>[a-z0-9\-]+)/?'
    
    # Browser Headers taaki Cloudflare ko lage ki asli banda hai
    _COMMON_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://hanime.red/',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        
        # Step 1: Webpage download with headers
        page = self._download_webpage(
            url, video_id, 
            headers=self._COMMON_HEADERS,
            note='Downloading page with browser headers'
        )
        
        # Thoda wait taaki cloudflare ko doubt na ho
        time.sleep(1)

        # Method 1: __NUXT__ Extraction
        data_str = self._search_regex(
            [r'window\.__NUXT__\s*=\s*({.*?});', r'window\.__NUXT__\s*=\s*({.*?})<'], 
            page, 'nuxt data', default=None
        )

        formats = []
        title = video_id

        if data_str:
            try:
                # Key cleaning (making it valid JSON)
                clean_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', data_str)
                data = self._parse_json(clean_json, video_id)
                
                state_data = data.get('state', {}).get('data', {}) or data.get('data', {})
                video_info = state_data.get('video', {}).get('hentai_video', {}) or state_data.get('hentai_video', {})
                
                if video_info:
                    title = video_info.get('name', video_id)
                    manifest = state_data.get('video', {}).get('videos_manifest', {}) or state_data.get('videos_manifest', {})
                    for server in manifest.get('servers', []):
                        for stream in server.get('streams', []):
                            if stream.get('url'):
                                formats.append({
                                    'url': stream['url'],
                                    'ext': 'mp4',
                                    'height': int_or_none(stream.get('height')),
                                    'format_id': str_or_none(stream.get('id')),
                                    'vcodec': 'h246'
                                })
            except:
                pass

        # Method 2: API Fallback WITH HEADERS
        if not formats:
            api_headers = self._COMMON_HEADERS.copy()
            api_headers.update({
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            api_url = f"https://hanime.red/api/v8/video?id={video_id}"
            try:
                api_data = self._download_json(
                    api_url, video_id, 
                    headers=api_headers,
                    fatal=False, 
                    note="Trying API with specific headers"
                )
                
                if api_data and 'hentai_video' in api_data:
                    title = api_data['hentai_video'].get('name', title)
                    for server in api_data.get('videos_manifest', {}).get('servers', []):
                        for stream in server.get('streams', []):
                            if stream.get('url'):
                                formats.append({
                                    'url': stream['url'],
                                    'height': int_or_none(stream.get('height')),
                                    'ext': 'mp4',
                                    'vcodec': 'h246'
                                })
            except Exception as e:
                self.to_screen(f"API Fallback failed: {str(e)}")

        if not formats:
            # Agar ab bhi nahi mil raha, toh site ne IP block kar diya hai
            raise ExtractorError("Cloudflare blocked the request. Try using a Proxy or wait for some time.", expected=True)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18
        }
