import os
import uuid
import time
import shutil
import threading
from yt_dlp import YoutubeDL


def check_ffmpeg():
    """Return True if FFmpeg is available on PATH."""
    return shutil.which('ffmpeg') is not None


class YTDLPHelper:
    def __init__(self, temp_dir='temp_files'):
        """Initialize the YTDLPHelper with a temporary directory for downloads."""
        self.temp_dir = temp_dir
        self.downloads = {}
        self.ffmpeg_available = check_ffmpeg()

        # Create temp directory if it doesn't exist
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    def get_video_info(self, url):
        """
        Get information about a YouTube video.

        Args:
            url (str): The YouTube video URL

        Returns:
            dict: Information about the video and available formats
        """
        # BUG FIX 1: Removed 'extract_flat': True — it suppressed all format details.
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                raise Exception("Could not retrieve video information")

            # Format duration
            duration = info.get('duration', 0) or 0
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)

            if hours > 0:
                duration_formatted = f"{hours}:{minutes:02}:{seconds:02}"
            else:
                duration_formatted = f"{minutes:02}:{seconds:02}"

            # Get available formats
            formats = []

            if info.get('formats'):
                # Filter distinct video resolutions (must have video codec)
                video_formats = []
                for fmt in info['formats']:
                    vcodec = fmt.get('vcodec', 'none')
                    height = fmt.get('height')
                    if height and vcodec and vcodec != 'none':
                        # Keep only the best format_id for each resolution
                        existing = next((vf for vf in video_formats if vf['height'] == height), None)
                        filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                        if not existing:
                            video_formats.append({
                                'height': height,
                                'format_id': fmt.get('format_id'),
                                'filesize': filesize,
                            })
                        else:
                            # Prefer the entry with more filesize info
                            if filesize and not existing['filesize']:
                                existing['filesize'] = filesize
                                existing['format_id'] = fmt.get('format_id')

                # Sort by height descending
                video_formats.sort(key=lambda x: x['height'], reverse=True)

                for fmt in video_formats:
                    h = fmt['height']
                    if h >= 2160:
                        quality = f"{h}p 4K"
                    elif h >= 1080:
                        quality = f"{h}p Full HD"
                    elif h >= 720:
                        quality = f"{h}p HD"
                    else:
                        quality = f"{h}p"

                    filesize = fmt.get('filesize', 0)
                    if filesize and filesize > 0:
                        if filesize < 1024 * 1024:
                            filesize_formatted = f"{filesize / 1024:.1f} KB"
                        else:
                            filesize_formatted = f"{filesize / (1024 * 1024):.1f} MB"
                    else:
                        filesize_formatted = None

                    formats.append({
                        'format_id': fmt['format_id'],
                        'quality': quality,
                        'filesize': filesize,
                        'filesize_formatted': filesize_formatted,
                        'type': 'video',
                    })

            # Add audio-only option (mp3) — only if FFmpeg is available
            if self.ffmpeg_available:
                formats.append({
                    'format_id': 'bestaudio/best',
                    'quality': 'MP3',
                    'filesize': 0,
                    'filesize_formatted': None,
                    'type': 'audio',
                })

            return {
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader') or info.get('channel', 'Unknown'),
                'duration': duration,
                'duration_formatted': duration_formatted,
                'thumbnail': info.get('thumbnail'),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'formats': formats,
                'ffmpeg_available': self.ffmpeg_available,
            }

    def start_download(self, url, format_id, quality):
        """
        Start downloading a video in the specified format.

        Args:
            url (str): The YouTube video URL
            format_id (str): The format ID to download
            quality (str): Quality label for reference

        Returns:
            dict: Download token and initial status
        """
        token = str(uuid.uuid4())

        self.downloads[token] = {
            'status': 'queued',
            'progress': 0,
            'url': url,
            'format_id': format_id,
            'quality': quality,
            'output_path': None,
            'error': None,
            'started_at': time.time(),
        }

        thread = threading.Thread(
            target=self._download_worker,
            args=(token, url, format_id, quality)
        )
        thread.daemon = True
        thread.start()

        return {'token': token, 'status': 'queued'}

    def _download_worker(self, token, url, format_id, quality):
        """
        Worker function to perform the download in a separate thread.
        """
        try:
            self.downloads[token]['status'] = 'downloading'

            output_template = os.path.join(self.temp_dir, f'{token}.%(ext)s')

            if quality == 'MP3':
                # Audio-only download → convert to MP3 via FFmpeg
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [lambda d: self._progress_hook(d, token)],
                }
            else:
                # BUG FIX 2: Use a robust format selector that handles combined streams.
                # Falls back gracefully if the specific format_id doesn't have a separate audio.
                ydl_opts = {
                    'format': f'{format_id}+bestaudio/bestvideo+bestaudio/best',
                    'outtmpl': output_template,
                    'merge_output_format': 'mp4',
                    'progress_hooks': [lambda d: self._progress_hook(d, token)],
                }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.downloads[token]['status'] = 'processing'

            # BUG FIX 3: Compare bare filenames using startswith(token), not full paths.
            found_path = None
            for filename in os.listdir(self.temp_dir):
                if filename.startswith(token):
                    full_path = os.path.join(self.temp_dir, filename)
                    if os.path.isfile(full_path):
                        found_path = full_path
                        break

            if not found_path:
                raise FileNotFoundError(f"Downloaded file not found for token {token}")

            self.downloads[token]['output_path'] = found_path
            self.downloads[token]['status'] = 'complete'
            self.downloads[token]['progress'] = 100

        except Exception as e:
            self.downloads[token]['status'] = 'error'
            self.downloads[token]['error'] = str(e)

    def _progress_hook(self, d, token):
        """Progress hook for yt-dlp."""
        if token not in self.downloads:
            return

        status = self.downloads[token]

        if d['status'] == 'downloading':
            if d.get('total_bytes') and d['total_bytes'] > 0:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif d.get('total_bytes_estimate') and d['total_bytes_estimate'] > 0:
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                elapsed = time.time() - status['started_at']
                progress = min(90, elapsed / 2)

            self.downloads[token]['progress'] = progress
            # Store speed and eta for richer UI
            self.downloads[token]['speed'] = d.get('speed')
            self.downloads[token]['eta'] = d.get('eta')

        elif d['status'] == 'finished':
            self.downloads[token]['status'] = 'processing'
            self.downloads[token]['progress'] = 95

    def get_download_status(self, token):
        """Get the status of a download."""
        return self.downloads.get(token)

    def cleanup_download(self, token):
        """Delete the temp file for a completed download."""
        entry = self.downloads.get(token)
        if entry and entry.get('output_path'):
            try:
                os.remove(entry['output_path'])
            except OSError:
                pass
        self.downloads.pop(token, None)