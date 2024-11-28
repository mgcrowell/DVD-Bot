import os
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env for secrets
load_dotenv()
botkey = os.getenv("BOT_KEY")

# Initialize bot
intents = discord.Intents.default()
intents.messages = True  # Allows the bot to read messages
intents.message_content = True  # Allows the bot to read the content of the message
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")
    print("Ping command received!")

@bot.command()
async def fetch_video(ctx, webpage_url: str):
    video_filename = None  # Initialize the variable here

    try:
        print(f"Fetching webpage: {webpage_url}")

        # Step 1: Download the HTML of the webpage asynchronously
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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
                video_filename = "temp_video.mp4"
                with open(video_filename, "wb") as file:
                    while True:
                        chunk = await video_response.content.read(8192)
                        if not chunk:
                            break
                        file.write(chunk)

        # Step 4: Reply with the video attached
        await ctx.send(file=discord.File(video_filename))
        print(f"Video sent successfully to {ctx.author}")

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
