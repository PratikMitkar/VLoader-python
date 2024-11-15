import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QListWidget, 
                            QLabel, QProgressBar, QFileDialog, QMessageBox,
                            QSplitter, QToolButton, QListWidgetItem, QGroupBox, 
                            QDialog, QComboBox, QSplashScreen, QStyle)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QObject, QSettings, QTimer
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QPalette, QColor, QShortcut, QKeySequence, QAction, QMovie
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import yt_dlp
import tempfile
from PyQt6.QtGui import QDesktopServices
import time
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from browser_cookie3 import chrome, firefox

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        # Make window frameless and always on top
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Load theme setting
        self.settings = QSettings('VideoDownloader', 'Settings')
        self.current_theme = self.settings.value('theme', 'Light')
        
        # Create main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create central widget
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        
        # Left side (logo)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(0)
        left_widget.setLayout(left_layout)
        
        # Logo label
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background-color: transparent;")
        left_layout.addWidget(self.logo_label)
        
        # Right side (text and progress)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(20)
        right_widget.setLayout(right_layout)
        
        # App name with larger font
        app_name = QLabel("Video Downloader")
        app_name.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            font-family: 'Segoe UI Light', Arial, sans-serif;
        """)
        
        # Version info
        version_label = QLabel("Version 1.0")
        version_label.setStyleSheet("font-size: 14px;")
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("font-size: 12px;")
        
        # Thin progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Add widgets to right layout
        right_layout.addStretch()
        right_layout.addWidget(app_name)
        right_layout.addWidget(version_label)
        right_layout.addStretch()
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.progress_bar)
        
        # Add both sides to main layout
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 2)
        
        # Set fixed size and center
        self.setFixedSize(600, 300)
        central_widget.setGeometry(0, 0, self.width(), self.height())
        
        # Apply theme and center
        self.apply_theme(self.current_theme)
        self.center_on_screen()

    def apply_theme(self, theme_name):
        themes = {
            "Light": {
                "central_bg": "rgba(255, 255, 255, 200)",
                "right_bg": "rgba(245, 245, 245, 180)",
                "text_color": "#2C3E50",
                "secondary_text_color": "rgba(52, 73, 94, 180)",
                "progress_bg": "rgba(189, 195, 199, 100)",
                "progress_chunk": "#526D82",
                "logo_path": "icons/app-removebg.png"
            },
            "Dark": {
                "central_bg": "rgba(44, 62, 80, 200)",
                "right_bg": "rgba(52, 73, 94, 180)",
                "text_color": "#ECF0F1",
                "secondary_text_color": "rgba(236, 240, 241, 180)",
                "progress_bg": "rgba(52, 73, 94, 100)",
                "progress_chunk": "#526D82",
                "logo_path": "icons/app-removebg-white.png"
            }
        }
        
        theme = themes.get(theme_name, themes["Light"])
        
        # Update logo based on theme with increased size
        logo_pixmap = QPixmap(theme['logo_path'])
        if not logo_pixmap.isNull():
            # Increased size from 120x120 to 160x160
            scaled_logo = logo_pixmap.scaled(160, 160, 
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            # Fallback text with increased size
            self.logo_label.setText("VD")
            self.logo_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme['text_color']};
                    font-size: 96px;  # Increased from 72px
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: transparent;
                }}
            """)
        
        # Apply theme styles
        self.findChild(QWidget).setStyleSheet(f"""
            QWidget {{
                background-color: {theme['central_bg']};
                border-radius: 10px;
            }}
        """)
        
        # Style for right widget
        self.findChildren(QWidget)[2].setStyleSheet(f"""
            QWidget {{
                background-color: {theme['right_bg']};
            }}
        """)
        
        # Style for labels
        for label in self.findChildren(QLabel):
            if label.text() == "Video Downloader":
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {theme['text_color']};
                        font-size: 28px;
                        font-weight: bold;
                        font-family: 'Segoe UI Light', Arial, sans-serif;
                        background-color: transparent;
                        padding: 0px;
                    }}
                """)
            elif label.text() == "Version 1.0":
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {theme['secondary_text_color']};
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: transparent;
                        padding: 0px;
                    }}
                """)
            else:
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {theme['secondary_text_color']};
                        font-size: 12px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: transparent;
                        padding: 0px;
                    }}
                """)
        
        # Style for progress bar
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {theme['progress_bg']};
                height: 3px;
                text-align: center;
                margin: 0px 10px;
            }}
            QProgressBar::chunk {{
                background-color: {theme['progress_chunk']};
                border-radius: 1px;
            }}
        """)

    def update_progress(self, value, status):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

class ThumbnailWorker(QThread):
    thumbnail_ready = pyqtSignal(QPixmap)
    title_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                # Get title
                title = info.get('title', 'Unknown Title')
                self.title_ready.emit(title)
                
                # Get thumbnail
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    response = requests.get(thumbnail_url)
                    img = QImage()
                    img.loadFromData(response.content)
                    pixmap = QPixmap.fromImage(img)
                    scaled_pixmap = pixmap.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
                    self.thumbnail_ready.emit(scaled_pixmap)
                else:
                    self.show_placeholder()
        except Exception as e:
            self.error.emit(str(e))
            self.show_placeholder()

    def show_placeholder(self):
        pixmap = QPixmap(320, 180)
        pixmap.fill(Qt.GlobalColor.gray)
        self.thumbnail_ready.emit(pixmap)

class VideoExtractor:
    @staticmethod
    def extract_video_urls(page_url):
        try:
            # Check if it's an Instagram URL
            if 'instagram.com' in page_url:
                return VideoExtractor.extract_instagram_video(page_url)
            
            # Configure session with retries and headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate'
            })
            
            # Add retry strategy
            retries = Retry(
                total=5,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504]
            )
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))

            # Fetch page content
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            video_urls = set()
            
            # Enhanced patterns for video URL detection
            patterns = [
                # Standard video files
                r'https?://[^\s<>"\']+?\.(?:mp4|webm|ogg|m3u8)(?:[^\s<>"\']*)?',
                
                # Video platforms
                r'https?://(?:www\.)?youtube\.com/watch\?v=[^\s<>"\']+',
                r'https?://(?:www\.)?youtu\.be/[^\s<>"\']+',
                r'https?://(?:www\.)?vimeo\.com/[^\s<>"\']+',
                r'https?://(?:www\.)?dailymotion\.com/video/[^\s<>"\']+',
                
                # Video IDs and embeds
                r'https?://[^\s<>"\']+?/(?:videos?|media|embed)/[a-zA-Z0-9-_]+',
                
                # CDN patterns
                r'https?://[^\s<>"\']+?\.cdn\.net/[^\s<>"\']+?\.(?:mp4|webm|ogg|m3u8)',
                
                # Storage patterns
                r'https?://[^\s<>"\']+?/storage\d+/[^\s<>"\']+?\.(?:mp4|webm|ogg|m3u8)',
                
                # Additional patterns from JS code
                r'https?://[^\s<>"\']+?/download/[^\s<>"\']+?\.(?:mp4|webm|ogg)',
                r'https?://[^\s<>"\']+?/files?/[^\s<>"\']+?\.(?:mp4|webm|ogg)'
            ]
            
            # Find video elements in HTML
            for video in soup.find_all(['video', 'source']):
                src = video.get('src')
                if src:
                    video_urls.add(urljoin(page_url, src))
                
                # Check data-src attribute
                data_src = video.get('data-src')
                if data_src:
                    video_urls.add(urljoin(page_url, data_src))
            
            # Find iframes that might contain videos
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '')
                if any(platform in src.lower() for platform in ['youtube', 'vimeo', 'dailymotion']):
                    video_urls.add(urljoin(page_url, src))
            
            # Search for video URLs in the page source
            for pattern in patterns:
                urls = re.findall(pattern, response.text, re.IGNORECASE)
                for url in urls:
                    # Clean up the URL
                    cleaned_url = url.strip("'\"\\;,")
                    if cleaned_url:
                        video_urls.add(urljoin(page_url, cleaned_url))
            
            # Additional check for JSON data that might contain video URLs
            json_pattern = r'["\'](https?://[^\s<>"\']+?\.(?:mp4|webm|ogg|m3u8)[^\s<>"\']*)["\']'
            json_urls = re.findall(json_pattern, response.text)
            video_urls.update(json_urls)
            
            return list(video_urls)
            
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, requests.exceptions.ConnectionError):
                error_msg = "Connection was interrupted. Please check your internet connection and try again."
            elif isinstance(e, requests.exceptions.Timeout):
                error_msg = "The connection timed out. Please try again or check your internet connection."
            elif isinstance(e, requests.exceptions.TooManyRedirects):
                error_msg = "Too many redirects. The website might be blocking automated access."
            elif isinstance(e, requests.exceptions.RequestException):
                error_msg = "Failed to connect to the website. Please check the URL and try again."
            
            raise Exception(f"Error extracting videos: {error_msg}")

    @staticmethod
    def extract_instagram_video(url):
        try:
            # Get cookies from browser with better error handling
            cookies = {}
            try:
                try:
                    chrome_cookies = chrome()
                    cookies = {cookie.name: cookie.value for cookie in chrome_cookies if '.instagram.com' in cookie.domain}
                except Exception as chrome_error:
                    print(f"Chrome cookies error: {str(chrome_error)}")
                    try:
                        firefox_cookies = firefox()
                        cookies = {cookie.name: cookie.value for cookie in firefox_cookies if '.instagram.com' in cookie.domain}
                    except Exception as firefox_error:
                        print(f"Firefox cookies error: {str(firefox_error)}")
                        # Continue without cookies
                        pass
            except Exception as e:
                print(f"Cookie extraction error: {str(e)}")
                # Continue without cookies
                pass

            # Configure yt-dlp options for Instagram
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'format': 'best',
            }

            # Only add cookie options if we successfully got cookies
            if cookies:
                # Create a temporary cookie file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    for name, value in cookies.items():
                        f.write(f'.instagram.com\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n')
                    ydl_opts['cookiefile'] = f.name

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    if 'Login required' in str(e):
                        # If login required, try alternative method
                        return VideoExtractor.extract_instagram_video_alternative(url, cookies)
                    raise e

                # Get video URL
                if info.get('url'):
                    return [info['url']]
                elif info.get('entries'):
                    return [entry['url'] for entry in info['entries'] if entry.get('url')]
                else:
                    raise Exception("No video URL found in the Instagram post")

        except Exception as e:
            if 'Login required' in str(e):
                raise Exception("This Instagram content requires login. Please log in to Instagram in your browser first.")
            raise Exception(f"Failed to extract Instagram video: {str(e)}")

    @staticmethod
    def extract_instagram_video_alternative(url, cookies):
        try:
            # Headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Origin': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/',
            }

            # Create session with cookies
            session = requests.Session()
            for name, value in cookies.items():
                session.cookies.set(name, value, domain='.instagram.com')

            # Get the Instagram post page
            response = session.get(url, headers=headers)
            response.raise_for_status()

            # Look for video URLs in the page source
            video_urls = []
            
            # Pattern for video URLs in Instagram's HTML
            patterns = [
                r'"video_url":"([^"]+)"',
                r'"video_versions":\[{"type":\d+,"width":\d+,"height":\d+,"url":"([^"]+)"',
                r'property="og:video" content="([^"]+)"'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    video_urls.extend(matches)

            # Clean up URLs (remove escapes)
            video_urls = [url.replace('\\u0026', '&') for url in video_urls]

            if not video_urls:
                raise Exception("No video URLs found in the Instagram post")

            return list(set(video_urls))

        except Exception as e:
            raise Exception(f"Failed to extract Instagram video using alternative method: {str(e)}")

class ScanWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            # Check if direct video URL
            if any(ext in self.url.lower() for ext in ['.mp4', '.webm', '.ogg']) or \
               any(site in self.url.lower() for site in ['youtube.com', 'youtu.be', 'vimeo.com']):
                videos = [self.url]
            else:
                videos = VideoExtractor.extract_video_urls(self.url)
            self.finished.emit(videos)
        except Exception as e:
            self.error.emit(str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, output_path):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.last_progress = 0
        
        # Enhanced session configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Configure more robust retry strategy
        retries = Retry(
            total=10,
            backoff_factor=1,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            raise_on_status=False
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Calculate download progress
            if 'total_bytes' in d:
                # Direct byte calculation
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.progress.emit(progress)
            elif 'total_bytes_estimate' in d:
                # Use estimated total bytes
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                self.progress.emit(progress)
            elif '_percent_str' in d:
                # Parse percentage string directly
                try:
                    percent_str = d['_percent_str'].strip().replace('%', '')
                    progress = float(percent_str)
                    self.progress.emit(progress)
                except:
                    pass
            elif 'downloaded_bytes' in d:
                # If we only have downloaded bytes, emit -1 to show indeterminate progress
                self.progress.emit(-1)

        elif d['status'] == 'finished':
            self.progress.emit(100)

    def run(self):
        try:
            print(f"Starting download for URL: {self.url}")
            
            # Enhanced yt-dlp options
            ydl_opts = {
                'format': 'best',
                'outtmpl': str(Path(self.output_path) / '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'socket_timeout': 120,
                'retries': 30,
                'fragment_retries': 30,
                'retry_sleep': lambda n: min(10 + n, 60),
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'no_color': True,
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                # Add these options for better progress reporting
                'progress_with_newline': True,
                'force_progress': True,
            }

            # Try multiple download methods
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])
            except Exception as e:
                print(f"yt-dlp download failed: {str(e)}")
                print("Attempting direct download...")
                self.download_direct(self.url)
                
            self.finished.emit()
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)

    def download_direct(self, url):
        try:
            # Enhanced direct download with chunked transfer
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(self.output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            self.progress.emit(progress)
                            
        except Exception as e:
            raise Exception(f"Direct download failed: {str(e)}")

    @staticmethod
    def sanitize_filename(url):
        """Sanitize filename from URL"""
        # Extract filename from URL
        filename = url.split('/')[-1].split('?')[0]
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limit length
        return filename[:50]

class VideoListItemWidget(QWidget):
    thumbnail_loaded = pyqtSignal(bool)
    
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.has_thumbnail = False
        
        # Remove the forced white text style
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)  # 16:9 aspect ratio
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)
        
        # Create right container widget
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Title label without forced color
        self.title_label = QLabel("Loading title...")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self.title_label.setWordWrap(True)
        
        # URL Label without forced color
        self.url_label = QLabel(url)
        self.url_label.setWordWrap(True)
        self.url_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                background-color: transparent;
            }
        """)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #526D82;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                min-width: 28px;
            }
            QPushButton:hover {
                background-color: #27374D;
            }
            QPushButton:pressed {
                background-color: #526D82;
            }
        """
        
        # Copy Button with emoji
        self.copy_button = QPushButton("📋")
        self.copy_button.setToolTip("Copy URL")
        self.copy_button.setStyleSheet(button_style)
        
        # Download Button with emoji
        self.download_button = QPushButton("⬇️")
        self.download_button.setToolTip("Download Video")
        self.download_button.setStyleSheet(button_style)
        
        # Add buttons to container
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.download_button)
        button_layout.addStretch()
        
        # Connect button signals
        self.copy_button.clicked.connect(self.copy_url)
        
        # Add widgets to right layout
        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.url_label)
        right_layout.addWidget(button_container)
        right_layout.addStretch()
        
        # Add main components to layout
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(right_container, stretch=1)
        
        # Start fetching thumbnail and title
        self.fetch_thumbnail_and_title()
    
    def fetch_thumbnail_and_title(self):
        self.thumbnail_worker = ThumbnailWorker(self.url)
        self.thumbnail_worker.thumbnail_ready.connect(self.set_thumbnail)
        self.thumbnail_worker.title_ready.connect(self.set_title)
        self.thumbnail_worker.error.connect(self.handle_error)
        self.thumbnail_worker.start()
    
    def set_thumbnail(self, pixmap):
        if not pixmap.isNull():
            self.has_thumbnail = True
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_loaded.emit(True)
        else:
            # Emit False for invalid thumbnails
            self.thumbnail_loaded.emit(False)
            self.handle_error("Failed to load thumbnail")
    
    def set_title(self, title):
        self.title_label.setText(title)
    
    def handle_error(self, error):
        self.title_label.setText("Untitled Video")
        self.has_thumbnail = False
        self.thumbnail_loaded.emit(False)
        # Show placeholder thumbnail
        pixmap = QPixmap(self.thumbnail_label.size())
        pixmap.fill(Qt.GlobalColor.gray)
        self.thumbnail_label.setPixmap(pixmap)
    
    def copy_url(self):
        QApplication.clipboard().setText(self.url)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        # Load settings
        self.settings = QSettings('VideoDownloader', 'Settings')
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Output Path Group
        path_group = QGroupBox("Default Output Path")
        path_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setText(self.settings.value('default_output_path', ''))
        self.path_input.setPlaceholderText("Select default output directory")
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        
        # Theme Group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        current_theme = self.settings.value('theme', 'Light')
        self.theme_combo.setCurrentText(current_theme)
        
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # Add all to main layout
        layout.addWidget(path_group)
        layout.addWidget(theme_group)
        layout.addLayout(button_layout)
        
        # Apply current theme
        self.apply_theme(current_theme)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Default Output Directory")
        if directory:
            self.path_input.setText(directory)

    def save_settings(self):
        # Save settings
        self.settings.setValue('default_output_path', self.path_input.text())
        self.settings.setValue('theme', self.theme_combo.currentText())
        self.accept()

    def apply_theme(self, theme_name):
        themes = {
            "Light": """
            /* ... other light theme styles ... */
            
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #f5f5f5;
            }
            VideoListItemWidget QLabel {
                color: #333333;
            }
            VideoListItemWidget .title_label {
                color: #333333;
            }
            VideoListItemWidget .url_label {
                color: #333333;
            }
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
            }
            QProgressBar::chunk {
                background-color: #27374D;
            }
            #progress_label {
                color: #333333;
                font-weight: bold;
            }
        """,
            "Dark": """
            /* ... other dark theme styles ... */
            
            QListWidget {
                background-color: #2d2d2d;
                border: 2px solid #333333;
                border-radius: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #404040;
            }
            VideoListItemWidget QLabel {
                color: #ffffff;
            }
            VideoListItemWidget .title_label {
                color: #ffffff;
            }
            VideoListItemWidget .url_label {
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #27374D;
            }
            #progress_label {
                color: #ffffff;
                font-weight: bold;
            }
        """
        }
        
        if theme_name in themes:
            self.setStyleSheet(themes[theme_name])

class VideoDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("VLoader - Video Downloader")
        
        # Set application icon using PNG file
        app_icon = QIcon("icons/app-removebg.png")
        self.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)  # Set application-wide icon
        
        self.setMinimumSize(1200, 800)
        
        # Set custom font
        app_font = QFont("Segoe UI", 10)
        QApplication.setFont(app_font)
        
        # Update the color palette to use consistent blue theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 245, 255))           # Light blue background
        palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 60, 90))          # Dark blue text
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))             # White
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 250, 255))    # Very light blue
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))      # White
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 60, 90))         # Dark blue
        palette.setColor(QPalette.ColorRole.Text, QColor(30, 60, 90))                # Dark blue
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 245, 255))           # Light blue
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 60, 90))          # Dark blue
        palette.setColor(QPalette.ColorRole.BrightText, QColor(0, 100, 200))         # Bright blue
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))          # Selection blue
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))  # White
        QApplication.setPalette(palette)
        
        # Update the stylesheet with consistent blue theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dcdde1;
                border-radius: 10px;
                margin-top: 1em;
                padding: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #2f3640;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #dcdde1;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #526D82;
            }
            QPushButton {
                background-color: #526D82;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27374D;
            }
            QPushButton:pressed {
                background-color: #526D82;
            }
            QPushButton#scanButton, 
            QPushButton#browseButton, 
            QPushButton#downloadButton {
                background-color: #27374D;
            }
            QPushButton#scanButton:hover, 
            QPushButton#browseButton:hover, 
            QPushButton#downloadButton:hover {
                background-color: #526D82;
            }
            QProgressBar {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                background-color: white;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #526D82;
                border-radius: 6px;
            }
            QListWidget {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f2f6;
            }
            QListWidget::item:selected {
                background-color: #f1f2f6;
                color: #2f3640;
            }
            QToolButton {
                background-color: #27374D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #526D82;
            }
            QToolButton:pressed {
                background-color: #27374D;
            }
        """)
        
        # Create the main central widget and splitter
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create the main horizontal layout
        main_layout = QHBoxLayout(main_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side container
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create all your groups
        # URL Input Group
        url_group = QGroupBox("URL Input")
        url_layout = QHBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL or webpage URL")
        self.url_input.setMinimumHeight(40)
        
        # Scan button with emoji
        self.scan_button = QPushButton("🔍 Scan for Videos")
        self.scan_button.setObjectName("scanButton")
        self.scan_button.setMinimumHeight(40)
        self.scan_button.clicked.connect(self.scan_videos)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.scan_button)
        url_group.setLayout(url_layout)
        
        # Found Videos Group
        videos_group = QGroupBox("Found Videos")
        videos_layout = QVBoxLayout()
        self.video_list = QListWidget()
        videos_layout.addWidget(self.video_list)
        videos_group.setLayout(videos_layout)
        
        # Download Options Group
        download_group = QGroupBox("Download Options")
        download_layout = QVBoxLayout()
        
        # Output path layout
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Output directory")
        self.path_input.setMinimumHeight(40)
        
        # Browse button with emoji
        self.browse_button = QPushButton("📁 Browse")
        self.browse_button.setObjectName("browseButton")
        self.browse_button.setMinimumHeight(40)
        self.browse_button.clicked.connect(self.browse_output)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        
        # Download button with emoji
        self.download_button = QPushButton("⬇️ Download Selected")
        self.download_button.setObjectName("downloadButton")
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        
        # Modify progress bar settings
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setFormat("%p%")  # Show percentage
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                text-align: center;    /* Center text horizontally */
                qproperty-alignment: AlignCenter;  /* Center text both horizontally and vertically */
            }
            QProgressBar::chunk {
                background-color: #27374D;
            }
        """)
        
        # Add percentage label
        self.progress_label = QLabel("0.00%")
        self.progress_label.setObjectName("progress_label")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #526D82;
                font-size: 13px;
                font-weight: bold;
                min-width: 70px;
            }
        """)
        
        # Create horizontal layout for progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar, stretch=1)
        progress_layout.addWidget(self.progress_label)
        
        # Add to download layout
        download_layout.addLayout(path_layout)
        download_layout.addWidget(self.download_button)
        download_layout.addLayout(progress_layout)
        download_group.setLayout(download_layout)
        
        # Add all groups to left layout
        left_layout.addWidget(url_group)
        left_layout.addWidget(videos_group)
        left_layout.addWidget(download_group)
        
        # Right side: web view container with title bar
        web_container = QWidget()
        web_container.setObjectName("webContainer")  # Add object name for styling
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        web_layout.setSpacing(0)
        
        # Enhanced title bar with gradient
        title_bar = QWidget()
        title_bar.setFixedHeight(48)  # Slightly taller for better proportions
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27374D,
                    stop:1 #526D82
                );
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(8)

        # Button container with improved styling
        button_container = QWidget()
        button_container.setFixedHeight(28)  # Match button height
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(8)  # Increased spacing between buttons

        # Enhanced button styling with modern look and better spacing
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: white;
                border: none;
                border-radius: 6px;
                width: 34px;
                height: 34px;
                margin: 7px 3px;
                font-family: 'Segoe UI', Arial;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
                transform: translateY(1px);
            }
            
            /* Specific styling for close button */
            QPushButton#closeButton {
                margin-right: 8px;
            }
            QPushButton#closeButton:hover {
                background-color: #E81123;
            }
            
            /* Specific styling for maximize/restore button */
            QPushButton#maximizeButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
            }
            
            /* Specific styling for minimize button */
            QPushButton#minimizeButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
            }
        """

        # Create buttons with consistent styling and clear icons
        buttons = [
            ("🔄", "Refresh Video", lambda: self.web_view.reload()),
            ("🌐", "Open in Browser", self.open_in_browser),
            ("⛶", "Toggle Fullscreen", self.toggle_fullscreen)
        ]

        for icon, tooltip, callback in buttons:
            btn = QPushButton(icon)
            btn.setFixedSize(28, 28)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 15px;
                    margin: 4px;
                    padding: 0;
                    font-family: 'Segoe UI', Arial;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
            btn.clicked.connect(callback)
            button_container_layout.addWidget(btn)

        # Update video icon with better visibility
        video_icon = QPushButton("🎥")
        video_icon.setFixedSize(28, 28)
        video_icon.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 18px;
                padding: 0;
                margin-left: 12px;
            }
        """)

        # Add spacing between button groups
        button_container_layout.addStretch(1)

        # Update title container layout
        title_container = QWidget()
        title_container_layout = QHBoxLayout(title_container)
        title_container_layout.setContentsMargins(10, 0, 10, 0)
        title_container_layout.setSpacing(12)  # Increased spacing

        # Title label with improved styling
        self.title_label = QLabel("Video Preview")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 0 12px;
                letter-spacing: 0.3px;
            }
        """)

        # Add widgets to title container with proper spacing
        title_container_layout.addWidget(video_icon)
        title_container_layout.addWidget(self.title_label, stretch=1)
        title_container_layout.addWidget(button_container)

        # Update title bar layout
        title_layout.addWidget(title_container, stretch=1)

        # Create and configure the web view with dark mode
        web_profile = QWebEngineProfile("video_profile", self)
        web_profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.web_view = QWebEngineView()
        custom_page = CustomWebPage(web_profile)
        self.web_view.setPage(custom_page)
        
        self.web_view.setStyleSheet("""
            QWebEngineView {
                background: #2D3436;
                background-color: #2D3436;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Force dark mode for web content
        settings = custom_page.settings()
        # Remove the invalid WebRenderFPS attribute
        # settings.setAttribute(QWebEngineSettings.WebAttribute.WebRenderFPS, True)
        
        # Connect load finished signal
        self.web_view.loadFinished.connect(self.handle_load_finished)
        
        # Add a subtle loading overlay
        self.loading_overlay = QLabel()
        self.loading_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(45, 52, 54, 0.95);
                color: white;
                font-size: 16px;
                font-weight: 500;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.loading_overlay.hide()
        
        # Add widgets to web container
        web_layout.addWidget(title_bar)
        web_layout.addWidget(self.web_view)
        web_layout.addWidget(self.loading_overlay)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(web_container)
        
        # Set initial sizes for splitter
        splitter.setSizes([600, 600])
        
        # Connect video list item click to open web view
        self.video_list.itemClicked.connect(self.open_in_web_view)

        # Add keyboard shortcuts
        self.setup_shortcuts()
        
        # Add drag and drop support
        self.setup_drag_drop()

        # Load settings
        self.settings = QSettings('VideoDownloader', 'Settings')
        self.load_settings()
        
        # Add settings button to toolbar or menu
        self.create_menu()

    def open_in_browser(self):
        current_url = self.web_view.url().toString()
        if current_url:
            QDesktopServices.openUrl(QUrl(current_url))

    def handle_load_finished(self, success):
        if not success:
            self.loading_overlay.setText("Failed to load content")
            self.loading_overlay.show()
            self.web_view.hide()
        else:
            self.loading_overlay.hide()
            self.web_view.show()
            # Update title if available
            title = self.web_view.title()
            if title:
                self.title_label.setText(title)

    def open_in_web_view(self, item):
        widget = self.video_list.itemWidget(item)
        url = widget.url
        
        # Show loading state
        self.loading_overlay.setText("Loading...")
        self.loading_overlay.show()
        self.web_view.hide()
        
        # Check if it's a YouTube URL and modify accordingly
        if 'youtube.com' in url or 'youtu.be' in url:
            video_id = self.extract_youtube_id(url)
            if video_id:
                # Use embed URL for YouTube videos
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                self.web_view.setUrl(QUrl(embed_url))
            else:
                self.web_view.setUrl(QUrl(url))
        else:
            # For other URLs, load directly
            self.web_view.setUrl(QUrl(url))
        
        self.title_label.setText("Loading...")

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.path_input.setText(directory)

    def scan_videos(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
        
        self.scan_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.video_list.clear()
        
        self.scan_worker = ScanWorker(url)
        self.scan_worker.finished.connect(self.scan_complete)
        self.scan_worker.error.connect(self.show_error)
        self.scan_worker.start()

    def scan_complete(self, videos):
        self.video_list.clear()
        self.pending_thumbnails = len(videos)
        
        for url in videos:
            item = QListWidgetItem(self.video_list)
            widget = VideoListItemWidget(url)
            # Connect thumbnail_loaded signal to handle_thumbnail_loaded
            widget.thumbnail_loaded.connect(lambda success, item=item: 
                self.handle_thumbnail_loaded(success, item))
            widget.download_button.clicked.connect(lambda checked, u=url: self.download_video(u))
            item.setSizeHint(widget.sizeHint())
            self.video_list.addItem(item)
            self.video_list.setItemWidget(item, widget)
        
        self.scan_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
    
    def download_video(self, url):
        output_path = self.path_input.text()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please select an output directory")
            return
        
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.download_worker = DownloadWorker(url, output_path)
        self.download_worker.progress.connect(self.update_progress)
        self.download_worker.finished.connect(self.download_complete)
        self.download_worker.error.connect(self.show_error)
        self.download_worker.start()

    def start_download(self):
        selected_items = self.video_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a video to download")
            return
        
        output_path = self.path_input.text()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please select an output directory")
            return
        
        # Get URL from the widget
        widget = self.video_list.itemWidget(selected_items[0])
        url = widget.url
        
        # Reset progress indicators
        self.progress_bar.setValue(0)
        self.progress_label.setText("0.00%")
        self.download_button.setEnabled(False)
        
        # Create and start download worker
        self.download_worker = DownloadWorker(url, output_path)
        self.download_worker.progress.connect(self.update_progress)
        self.download_worker.finished.connect(self.download_complete)
        self.download_worker.error.connect(self.show_error)
        self.download_worker.start()

    def update_progress(self, progress):
        """Update progress bar and label with precise percentage"""
        try:
            if progress < 0:
                # Show indeterminate progress
                self.progress_bar.setRange(0, 0)
                self.progress_label.setText("Downloading...")
            else:
                # Ensure progress bar has proper range
                if self.progress_bar.maximum() == 0:
                    self.progress_bar.setRange(0, 100)
                
                # Ensure progress is between 0 and 100
                progress = max(0, min(100, progress))
                
                # Update progress bar
                self.progress_bar.setValue(int(progress))
                
                # Update label with 2 decimal precision
                self.progress_label.setText(f"{progress:.2f}%")
            
            # Force immediate update
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error updating progress: {str(e)}")

    def download_complete(self):
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)  # Set to 100 instead of 1000
        self.progress_label.setText("100.00%")
        QMessageBox.information(self, "Success", "Download completed!")

    def show_error(self, error_message):
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("0.00%")
        QMessageBox.critical(self, "Error", error_message)

    def update_preview(self):
        selected_items = self.video_list.selectedItems()
        if selected_items:
            widget = self.video_list.itemWidget(selected_items[0])
            url = widget.url
            self.title_label.setText("Loading preview...")
            
            # Load URL directly in web view
            self.web_view.setUrl(QUrl(url))
            
            # Get title using yt-dlp
            self.thumbnail_worker = ThumbnailWorker(url)
            self.thumbnail_worker.title_ready.connect(self.set_title)
            self.thumbnail_worker.error.connect(self.show_preview_error)
            self.thumbnail_worker.start()
    
    def extract_youtube_id(self, url):
        # Extract YouTube video ID from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube.com/embed/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def set_title(self, title):
        self.title_label.setText(title)

    def show_preview_error(self, error):
        self.title_label.setText("Title not available")

    def toggle_fullscreen(self):
        if self.web_view.isFullScreen():
            self.web_view.showNormal()
        else:
            self.web_view.showFullScreen()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Ctrl+V to paste URL
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self.paste_url)
        
        # Ctrl+D to start download
        download_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        download_shortcut.activated.connect(self.start_download)
        
        # Escape to exit fullscreen
        escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        escape_shortcut.activated.connect(lambda: self.web_view.showNormal())

    def setup_drag_drop(self):
        """Setup drag and drop support"""
        self.setAcceptDrops(True)
        self.url_input.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            self.url_input.setText(url)
            self.scan_videos()
        elif event.mimeData().hasText():
            self.url_input.setText(event.mimeData().text())
            self.scan_videos()

    def paste_url(self):
        """Handle URL pasting"""
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())
        self.scan_videos()

    def handle_thumbnail_loaded(self, success, item):
        if not success:
            # Remove items without thumbnails
            row = self.video_list.row(item)
            self.video_list.takeItem(row)
        
        self.pending_thumbnails -= 1
        if self.pending_thumbnails == 0:
            # All thumbnails processed
            if self.video_list.count() == 0:
                QMessageBox.information(self, "No Videos", "No videos with valid thumbnails found.")

    def create_menu(self):
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Settings action
        settings_action = QAction(QIcon.fromTheme('settings'), 'Settings', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        # Exit action
        exit_action = QAction(QIcon.fromTheme('exit'), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()

    def load_settings(self):
        # Load and apply settings
        default_path = self.settings.value('default_output_path', '')
        if default_path:
            self.path_input.setText(default_path)
        
        theme = self.settings.value('theme', 'Light')
        self.apply_theme(theme)

    def apply_theme(self, theme_name):
        themes = {
            "Light": """
                QMainWindow, QDialog {
                    background-color: #ffffff;
                    color: #333333;
                }
                QGroupBox {
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    margin-top: 1em;
                    padding: 15px;
                    background-color: #ffffff;
                    color: #333333;
                }
                QLineEdit, QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 2px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 8px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border-color: #27374D;
                }
                QPushButton {
                    background-color: #27374D;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #27374D;
                }
                QPushButton:pressed {
                    background-color: #526D82;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    color: #333333;
                }
                QListWidget::item {
                    color: #333333;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:selected {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QProgressBar {
                    border: 2px solid #e0e0e0;
                    border-radius: 4px;
                    background-color: #ffffff;
                    color: #333333;
                }
                QProgressBar::chunk {
                    background-color: #27374D;
                }
                QMenuBar {
                    background-color: #ffffff;
                    color: #333333;
                }
                QMenuBar::item:selected {
                    background-color: #27374D;
                    color: white;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                }
                QMenu::item:selected {
                    background-color: #27374D;
                    color: white;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    color: #333333;
                }
                QListWidget::item {
                    color: #333333;
                }
                QListWidget QLabel {
                    color: #333333;
                }
                VideoListItemWidget {
                    background-color: transparent;
                }
                VideoListItemWidget QLabel {
                    color: #333333;
                }
                #progress_label {
                    color: #333333;
                    font-weight: bold;
                }
            """,
            "Dark": """
                QMainWindow, QDialog, QWidget {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QGroupBox {
                    border: 2px solid #333333;
                    border-radius: 10px;
                    margin-top: 1em;
                    padding: 15px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLineEdit, QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 2px solid #333333;
                    border-radius: 4px;
                    padding: 8px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border-color: #27374D;
                }
                QPushButton {
                    background-color: #27374D;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #27374D;
                }
                QPushButton:pressed {
                    background-color: #526D82;
                }
                QListWidget {
                    background-color: #2d2d2d;
                    border: 2px solid #333333;
                    border-radius: 8px;
                    color: white !important;
                }
                QListWidget::item {
                    background-color: #2d2d2d;
                    color: white !important;
                    border-bottom: 1px solid #333333;
                }
                QListWidget::item:selected {
                    background-color: #404040;
                    color: white !important;
                }
                QLabel {
                    color: white !important;
                    background-color: transparent;
                }
                QProgressBar {
                    border: 2px solid #333333;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #27374D;
                }
                QMenuBar {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #27374D;
                    color: white;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #333333;
                }
                QMenu::item:selected {
                    background-color: #27374D;
                    color: white;
                }
                QScrollBar:vertical {
                    background-color: #2d2d2d;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #404040;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #27374D;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background-color: #2d2d2d;
                }
                QWebEngineView {
                    background-color: #2d2d2d;
                }
                QToolTip {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #333333;
                    padding: 5px;
                }
                QListWidget {
                    background-color: #2d2d2d;
                    border: 2px solid #333333;
                    border-radius: 8px;
                    color: white !important;
                    padding: 5px;
                }
                QListWidget::item {
                    background-color: #2d2d2d;
                    color: white !important;
                    border-bottom: 1px solid #333333;
                    padding: 5px;
                }
                QListWidget::item:selected {
                    background-color: #404040;
                    color: white !important;
                }
                QListWidget QLabel {
                    color: white !important;
                    background-color: transparent;
                }
                VideoListItemWidget {
                    background-color: transparent;
                }
                VideoListItemWidget QLabel {
                    color: white !important;
                    background-color: transparent;
                }
                #progress_label {
                    color: #ffffff;
                    font-weight: bold;
                }
            """
        }
        
        if theme_name in themes:
            self.setStyleSheet(themes[theme_name])

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile):
        super().__init__(profile)
        
        # Enable all required settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        
        # Set default encoding
        settings.setDefaultTextEncoding("UTF-8")
        
        # Force dark mode for web content
        self.runJavaScript("""
            document.documentElement.style.backgroundColor = '#2d2d2d';
            document.documentElement.style.color = '#ffffff';
        """)
        
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        # Allow all navigation requests
        return True
    
    def certificateError(self, error):
        # Ignore certificate errors
        return True
        
    def javaScriptConsoleMessage(self, level, message, line, source):
        # Log JavaScript console messages for debugging
        print(f"JS Console ({level}): {message} [line {line}] {source}")

class VideoDownloader(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(float)
    error_signal = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': self.url.split('/get_file/')[0],
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
            }

            session = requests.Session()
            
            # Get file size
            response = session.head(self.url, headers=headers, allow_redirects=True)
            total_size = int(response.headers.get('content-length', 0))

            # Download with proper headers and streaming
            response = session.get(self.url, headers=headers, stream=True)
            response.raise_for_status()

            downloaded_size = 0
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded_size += len(chunk)
                        f.write(chunk)
                        if total_size:
                            progress = (downloaded_size / total_size) * 100
                            self.progress.emit(progress)

            self.finished.emit()

        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished.emit()

def main():
    app = QApplication(sys.argv)
    
    # Create and show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Process events to ensure splash is displayed
    app.processEvents()
    
    # Create main window
    window = VideoDownloaderApp()
    
    # Simulate loading steps
    for i in range(0, 101, 20):
        time.sleep(0.1)  # Simulate work being done
        splash.update_progress(i, f"Loading... {i}%")
        app.processEvents()
    
    # Show main window and close splash
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 