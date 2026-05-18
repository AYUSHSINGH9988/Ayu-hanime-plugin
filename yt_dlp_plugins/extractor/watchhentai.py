import re
from urllib.parse import unquote
from yt_dlp.extractor.common import InfoExtractor

class WatchHentaiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?watchhentai\.net/videos/(?P<id>[^/?#&]+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        
        # Ye headers bohot zaroori hain (Anti-Leech bypass ke liye)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
            'Referer': url
        }
        
        webpage = self._download_webpage(url, video_id, headers=headers)
        
        title_match = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title', default=video_id
        )
        title = title_match.strip()
        
        mp4_match = re.search(r'(https?://[^\s\'"<>]*?\.mp4)', webpage)
        
        if not mp4_match:
            return {'id': video_id, 'title': title}
            
        raw_link = mp4_match.group(1).replace('\\/', '/')
        
        if "?source=" in raw_link:
            raw_link = unquote(raw_link.split("?source=")[1].split('&')[0])
            
        clean_base = raw_link.replace('.mp4', '')
        resolutions = [('1080', '_1080p.mp4'), ('720', '_720p.mp4'), ('480', '_480p.mp4')]
        
        formats = []
        
        if "_1080p" in raw_link or "_720p" in raw_link:
            formats.append({
                'url': raw_link, 
                'ext': 'mp4',
                'http_headers': headers
            })
        else:
            found_working = False
            for height, res_suffix in resolutions:
                test_url = clean_base + res_suffix
                try:
                    req = self._request_webpage(
                        test_url, video_id, f'Checking {height}p', 
                        method='HEAD', fatal=False, headers=headers
                    )
                    if req:
                        formats.append({
                            'format_id': f'{height}p',
                            'url': test_url, 
                            'ext': 'mp4', 
                            'height': int(height),
                            'http_headers': headers
                        })
                        found_working = True
                except Exception:
                    continue
                    
            if not found_working:
                formats.append({
                    'url': raw_link, 
                    'ext': 'mp4',
                    'http_headers': headers
                })
                
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18,
            'http_headers': headers
        }
