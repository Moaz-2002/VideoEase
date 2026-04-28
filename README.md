<div align="center">

# ⬇ VideoEase

**A fast, free, and private YouTube video downloader — built with Flask & yt-dlp**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=flat-square&logo=youtube&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎬 **Multi-quality downloads** | All resolutions from 144p up to 4K — dynamically fetched per video |
| 🎵 **MP3 extraction** | Extract high-quality 192 kbps audio (requires FFmpeg) |
| 📊 **Real-time progress** | Live progress bar with download speed and ETA |
| 🧵 **Threaded downloads** | Background threads keep the UI responsive during download |
| 📋 **Clipboard paste** | One-click paste from clipboard via the Clipboard API |
| 🕑 **Download history** | Recent downloads persisted in `localStorage` |
| 🔔 **Toast notifications** | Non-blocking alerts replace browser `alert()` dialogs |
| 🗑️ **Auto cleanup** | Temp files are deleted from the server after serving |
| 🌑 **Dark glassmorphism UI** | Fully responsive, premium dark-mode design |

---

## 🖼️ Screenshots

> _Run the app locally and visit `http://localhost:5000` to see it in action._

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, Flask 3.1, yt-dlp, threading
- **Frontend:** Vanilla JS (ES2020+), CSS Custom Properties, Google Fonts (Inter)
- **Media processing:** FFmpeg (optional, required for MP3)
- **Storage:** Temp filesystem (auto-cleaned), `localStorage` for history

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [FFmpeg](https://ffmpeg.org/download.html) on your system `PATH` *(optional — required only for MP3 extraction)*

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Moaz-2002/VideoEase.git
cd VideoEase

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open your browser at **http://localhost:5000**

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serve the main UI |
| `GET` | `/api/system-info` | Returns `ffmpeg_available` flag |
| `POST` | `/api/fetch-video-info` | Fetch video metadata & available formats |
| `POST` | `/api/download` | Start a background download, returns a token |
| `GET` | `/api/download-status/<token>` | Poll download progress, speed, ETA |
| `GET` | `/api/download-file/<token>` | Stream the finished file to the browser |
| `DELETE` | `/api/cleanup/<token>` | Manually delete a temp file |

---

## 🏗️ Project Structure

```
VideoEase/
├── app.py              # Flask routes & REST API
├── ytdlp_utils.py      # YTDLPHelper class (download engine)
├── requirements.txt
├── static/
│   ├── css/style.css   # Dark glassmorphism UI
│   └── js/main.js      # Frontend logic (toasts, history, polling)
├── templates/
│   └── index.html      # Jinja2 template
└── temp_files/         # Auto-created, gitignored
```

---

## ⚙️ How It Works

```
User pastes URL
      │
      ▼
POST /api/fetch-video-info
      │  yt-dlp extracts metadata (no download)
      ▼
User selects quality & clicks Download
      │
      ▼
POST /api/download  →  returns token
      │  spawns background thread
      ▼
GET /api/download-status/<token>  (polled every 1s)
      │  returns progress %, speed, ETA
      ▼
status == 'complete'
      │
      ▼
GET /api/download-file/<token>
      │  Flask streams file → browser saves it
      ▼
Temp file auto-deleted via call_on_close hook
```

---

## 🔧 Known Limitations

- Single video URLs only (no playlist support yet)
- MP3 requires FFmpeg installed on the server
- In-memory download state resets on server restart

---

## 🗺️ Roadmap

- [ ] Playlist / batch download support
- [ ] Celery + Redis task queue (replace raw threads)
- [ ] Dockerized deployment
- [ ] Progress via WebSockets instead of polling
- [ ] Rate limiting & request queuing

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.

> **Disclaimer:** This tool is for educational purposes. Only download content you own or have permission to download. Respect YouTube's Terms of Service and copyright laws.
