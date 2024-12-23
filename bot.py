import os
import aiohttp
import pickle
import instaloader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import tempfile

# Load .env for secrets
load_dotenv()
botkey = os.getenv("BOT_KEY")
insta_username = os.getenv("INSTA_USERNAME")
insta_password = os.getenv("INSTA_PASSWORD")

# Initialize bot
intents = discord.Intents.default()
intents.messages = True  # Allows the bot to read messages
intents.message_content = True  # Allows the bot to read the content of the message
bot = commands.Bot(command_prefix="!", intents=intents)

# Function to set up headless Chrome using Selenium
def setup_chrome_driver():
    options = Options()
    options.add_argument("--headless")  # Run headlessly
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--no-sandbox")  # Run without sandboxing
    options.add_argument("--disable-dev-shm-usage")  # Use /tmp for shared memory
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Set path for chromedriver if necessary
    driver = webdriver.Chrome(options=options)
    return driver

# Function to login to Instagram using Selenium
def login_instagram(username, password):
    driver = setup_chrome_driver()

    try:
        # Open Instagram login page
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(2)  # Wait for the page to load

        # Locate the login elements
        username_input = driver.find_element_by_name("username")
        password_input = driver.find_element_by_name("password")
        
        # Enter username and password
        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.submit()

        time.sleep(5)  # Wait for login to complete

        # Save cookies after login
        cookies = driver.get_cookies()
        with open("instagram_cookies.pkl", "wb") as f:
            pickle.dump(cookies, f)

        print("Instagram login successful and cookies saved.")
        
    finally:
        driver.quit()

# Function to load cookies into Instaloader and download video
def download_video_with_instaloader(reel_url, cookies_file):
    L = instaloader.Instaloader()

    # Load cookies from file
    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)
    
    # Create a session using the cookies
    for cookie in cookies:
        L.context._session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    # Download the video reel
    print(f"Downloading Instagram reel from: {reel_url}")
    L.download_post(instaloader.Post.from_shortcode(L.context, reel_url.split('/')[-2]), target="reel_downloads")


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")
    print("Ping command received!")

# Command to fetch video from either Instagram or iFunny
@bot.command()
async def fetch_video(ctx, webpage_url: str):
    video_filename = None  # Initialize the variable here

    try:
        print(f"Fetching webpage: {webpage_url}")
        
        # Check if the URL is from Instagram
        if "instagram.com/reel" in webpage_url:
            username = insta_username
            password = insta_password
            # Step 1: Login and save cookies
            login_instagram(username, password)
            # Step 2: Download the video using Instaloader with saved cookies
            download_video_with_instaloader(webpage_url, "instagram_cookies.pkl")
            
            # Get the downloaded mp4 file from the 'reel_downloads' folder
            reel_folder = "reel_downloads"
            video_filename = None
            for file in os.listdir(reel_folder):
                if file.endswith(".mp4"):
                    video_filename = os.path.join(reel_folder, file)
                    break

            if video_filename:
                # Step 3: Send the video to the user
                await ctx.send(file=discord.File(video_filename))
                print(f"Instagram video sent successfully to {ctx.author}")

                # Step 4: Clear the folder after sending the video
                for file in os.listdir(reel_folder):
                    file_path = os.path.join(reel_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")

        # Check if the URL is from iFunny
        elif "ifunny.co" in webpage_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # Step 1: Download the HTML of the webpage asynchronously
            async with aiohttp.ClientSession() as session:
                async with session.get(webpage_url, headers=headers) as response:
                    response.raise_for_status()  # Raise error for bad responses (4xx or 5xx)
                    print(f"Webpage fetched successfully: {webpage_url}")

                    # Decode content as UTF-8 to avoid 'charmap' error
                    html = await response.text(encoding='utf-8')

            # Step 2: Parse the HTML to find the <video> tag
            soup = BeautifulSoup(html, 'html.parser')
            video_tag = soup.find('video')

            if not video_tag:
                await ctx.send("No video tag found on the page.")
                print(f"No video tag found on {webpage_url}")
                return

            print(f"Found <video> tag on {webpage_url}")

            # Try to get the video URL from 'data-src' or 'src' attribute
            video_url = video_tag.get('data-src') or video_tag.get('src')

            if not video_url:
                await ctx.send("No video source found on the page.")
                print(f"No video source found on {webpage_url}")
                return

            print(f"Video source URL found: {video_url}")

            # Handle relative URLs
            if not video_url.startswith("http"):
                from urllib.parse import urljoin
                video_url = urljoin(webpage_url, video_url)

            print(f"Resolved video URL: {video_url}")

            # Step 3: Download the video asynchronously
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, headers=headers) as video_response:
                    video_response.raise_for_status()  # Ensure the download was successful
                    print(f"Video downloaded successfully: {video_url}")

                    # Save video to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        video_filename = tmp_file.name
                        with open(video_filename, "wb") as file:
                            while True:
                                chunk = await video_response.content.read(8192)
                                if not chunk:
                                    break
                                file.write(chunk)

            # Step 4: Reply with the video attached
            await ctx.send(file=discord.File(video_filename))
            print(f"iFunny video sent successfully to {ctx.author}")

        else:
            await ctx.send("The provided URL is neither from Instagram nor iFunny.")
            return

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    finally:
        # Step 5: Clean up by deleting the video file if it exists
        if video_filename and os.path.exists(video_filename):
            os.remove(video_filename)
            print(f"Deleted temporary video file: {video_filename}")

# Run the bot
bot.run(botkey)
