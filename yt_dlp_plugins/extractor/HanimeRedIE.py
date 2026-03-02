import json
import re
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, int_or_none, str_or_none

class HanimeRedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.red/(?:(?:videos/hentai|hentai/video)/)?(?P<id>[a-z0-9\-]+)/?'
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)
        
        # Method 1: __NUXT__ Extraction (Updated Regex)
        data_str = self._search_regex(
            [r'window\.__NUXT__\s*=\s*({.*?});', r'<script[^>]*>window\.__NUXT__\s*=\s*({.*?})</script>'], 
            page, 'nuxt data', default=None
        )

        # Method 2: DATA Extraction (Fallback)
        if not data_str:
            data_str = self._search_regex(
                r'window\.__DATA__\s*=\s*({.*?});', 
                page, 'window data', default=None
            )

        formats = []
        title = video_id

        if data_str:
            try:
                # Cleaning JS object to make it valid JSON
                clean_json = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', data_str)
                data = self._parse_json(clean_json, video_id)
                
                # Digging deep into the state tree
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
                                    'format_id': str_or_none(stream.get('id'))
                                })
            except:
                pass

        # Method 3: Direct API Fallback (Agar page parsing fail ho jaye)
        if not formats:
            api_data = self._download_json(
                f"https://hanime.red/api/v8/video?id={video_id}", 
                video_id, fatal=False, note="Trying API fallback"
            )
            if api_data and 'hentai_video' in api_data:
                title = api_data['hentai_video'].get('name', title)
                for server in api_data.get('videos_manifest', {}).get('servers', []):
                    for stream in server.get('streams', []):
                        if stream.get('url'):
                            formats.append({
                                'url': stream['url'],
                                'height': int_or_none(stream.get('height')),
                                'ext': 'mp4'
                            })

        if not formats:
            raise ExtractorError("Could not find any video streams. Site might be protected by Cloudflare.", expected=True)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18
        }
