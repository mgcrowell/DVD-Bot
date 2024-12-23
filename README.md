# DVD - Discord Video Download
A small Python-based bot to download iFunny videos and Instagram Reels in a Discord server.

Commands:
!fetch_video {video_url} – Downloads the video linked in the provided URL.
!ping - Sends back "Pong!"

Utilizes dotenv for proper secrets management.
BOT_KEY = You will obtain this from the Discord dev portal
INSTA_USERNAME = Insta Login
INSTA_PASSWORD = Insta Password

I use a seperate instagram account for this.

Reaplces deprecated modules in Python 3.13 (replacing audioop and cgi with community-supported versions) because the discord python library likes those to be around.

Note:
This bot is unsupported and not regularly maintained. Use it at your own risk.

For selenium to work you will need to install chrome seperately, it is configured for no gpu, no sandbox, and headless in the python code.
