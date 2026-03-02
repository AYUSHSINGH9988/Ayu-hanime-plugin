import json
import re
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, int_or_none, str_or_none

class HanimeRedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.red/(?:(?:videos/hentai|hentai/video)/)?(?P<id>[a-z0-9\-]+)/?'
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)
        
        nuxt_data_str = self._search_regex(
            r'<script[^>]*>window\.__NUXT__\s*=\s*({.*?});?</script>', 
            page, 
            'nuxt data',
            default=None
        )

        if not nuxt_data_str:
            raise ExtractorError("Could not find __NUXT__ data", expected=True)

        try:
            nuxt_data = self._parse_json(
                nuxt_data_str, 
                video_id, 
                transform_source=lambda x: re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', x)
            )
        except Exception as e:
            raise ExtractorError(f"Failed to parse NUXT data: {str(e)}")

        formats = []
        title = video_id

        try:
            video_info = nuxt_data.get('state', {}).get('data', {}).get('video', {}).get('hentai_video', {})
            title = video_info.get('name') or self._html_search_regex(r'<title>([^<]+)</title>', page, 'title', default=video_id)
            
            videos_manifest = nuxt_data.get('state', {}).get('data', {}).get('video', {}).get('videos_manifest', {})
            servers = videos_manifest.get('servers', [])
            
            if servers:
                 for server in servers:
                     for stream in server.get('streams', []):
                         stream_url = stream.get('url')
                         if stream_url:
                            formats.append({
                                'url': stream_url,
                                'ext': 'mp4',
                                'format_id': str_or_none(stream.get('id')) or f"{stream.get('height', 'unknown')}p",
                                'height': int_or_none(stream.get('height')),
                                'filesize_approx': int_or_none(stream.get('filesize_mbs'), invscale=1000000)
                            })
            
            if not formats:
                api_url = f"https://hanime.red/api/v8/video?id={video_id}"
                api_response = self._download_json(api_url, video_id, fatal=False)
                
                if api_response and 'hentai_video' in api_response:
                     title = api_response['hentai_video'].get('name', title)
                     if 'videos_manifest' in api_response and 'servers' in api_response['videos_manifest']:
                         for server in api_response['videos_manifest']['servers']:
                             for stream in server.get('streams', []):
                                 stream_url = stream.get('url')
                                 if stream_url:
                                     formats.append({
                                         'url': stream_url,
                                         'ext': 'mp4',
                                         'format_id': str_or_none(stream.get('id')),
                                         'height': int_or_none(stream.get('height'))
                                     })

        except Exception as e:
            raise ExtractorError(f"Error extracting metadata: {str(e)}")

        if not formats:
            raise ExtractorError("No video streams found.", expected=True)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18
        }
