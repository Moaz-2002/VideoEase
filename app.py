from flask import Flask, render_template, request, jsonify, send_file, abort
import os
import time
from ytdlp_utils import YTDLPHelper

app = Flask(__name__)

# Initialize YTDLPHelper
ytdlp_helper = YTDLPHelper(temp_dir='temp_files')


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/system-info', methods=['GET'])
def system_info():
    """Return system capabilities (e.g. FFmpeg availability)."""
    return jsonify({
        'ffmpeg_available': ytdlp_helper.ffmpeg_available,
    })


@app.route('/api/fetch-video-info', methods=['POST'])
def fetch_video_info():
    """API endpoint to fetch video information"""
    try:
        data = request.json
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        video_info = ytdlp_helper.get_video_info(url)

        return jsonify({
            'title': video_info.get('title', 'Unknown Title'),
            'thumbnail': video_info.get('thumbnail', ''),
            'duration': video_info.get('duration_formatted', 'Unknown'),
            'author': video_info.get('uploader', 'Unknown Channel'),
            'view_count': video_info.get('view_count', 0),
            'like_count': video_info.get('like_count', 0),
            'formats': video_info.get('formats', []),
            'ffmpeg_available': video_info.get('ffmpeg_available', False),
        })

    except Exception as e:
        app.logger.error(f"Error fetching video info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def start_download():
    """API endpoint to initiate a download"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        format_id = data.get('format_id')
        quality = data.get('quality')

        if not all([url, format_id, quality]):
            return jsonify({'error': 'Missing required parameters'}), 400

        download_info = ytdlp_helper.start_download(url, format_id, quality)

        return jsonify({'download_token': download_info['token']})

    except Exception as e:
        app.logger.error(f"Error starting download: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-status/<token>', methods=['GET'])
def check_download_status(token):
    """API endpoint to check the status of a download"""
    try:
        status = ytdlp_helper.get_download_status(token)

        if not status:
            return jsonify({'error': 'Invalid download token'}), 404

        return jsonify({
            'status': status['status'],
            'progress': status['progress'],
            'speed': status.get('speed'),
            'eta': status.get('eta'),
            'error': status.get('error'),
            'filename': os.path.basename(status['output_path']) if status.get('output_path') else None,
        })

    except Exception as e:
        app.logger.error(f"Error checking download status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-file/<token>', methods=['GET'])
def download_file(token):
    """Stream the downloaded file to the browser, then clean up."""
    try:
        status = ytdlp_helper.get_download_status(token)

        if not status:
            abort(404)

        if status['status'] != 'complete':
            return jsonify({'error': 'Download not yet complete'}), 400

        output_path = status.get('output_path')
        if not output_path or not os.path.exists(output_path):
            return jsonify({'error': 'File not found on server'}), 404

        filename = os.path.basename(output_path)

        # Send file, then schedule cleanup
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            max_age=0,
        )

        @response.call_on_close
        def cleanup():
            ytdlp_helper.cleanup_download(token)

        return response

    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup/<token>', methods=['DELETE'])
def cleanup_download(token):
    """Manually clean up a download token and its temp file."""
    ytdlp_helper.cleanup_download(token)
    return jsonify({'success': True})


@app.route('/api/placeholder/<int:width>/<int:height>')
def placeholder_image(width, height):
    """Generate a placeholder SVG image."""
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#1a1a2e"/>
        <text x="50%" y="50%" font-family="Arial" font-size="20" text-anchor="middle"
              dominant-baseline="middle" fill="#4a4a6a">{width}x{height}</text>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}


def setup():
    if not os.path.exists('temp_files'):
        os.makedirs('temp_files')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')


if __name__ == "__main__":
    with app.app_context():
        setup()
    app.run(debug=True)
