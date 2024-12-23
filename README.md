# discord-ifunny-downloader
A small Python-based bot to download iFunny videos in a Discord server.

Commands:
!fetch_video {video_url} – Downloads the video linked in the provided URL.
!ping - Sends back "Pong!"

Utilizes dotenv for proper secrets management.
Handles deprecated modules in Python 3.13 (replacing audioop and cgi with community-supported versions).
Note:
This bot is unsupported and not regularly maintained. Use it at your own risk.

For selenium to work you will need to install chrome seperately.
# Install dependencies for Chrome
sudo apt-get update
sudo apt-get install -y wget curl unzip

# Download the Google Chrome headless version
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install the downloaded .deb package
sudo dpkg -i google-chrome-stable_current_amd64.deb

# If any dependencies are missing, fix them
sudo apt-get install -f
