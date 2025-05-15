import tweepy
import os
import json
import requests
import locale
from datetime import datetime
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# file_path = os.path.join(os.path.dirname(__file__), "data.json")
logging.basicConfig(
    filename=f"{os.path.dirname(__file__)}/hemeroteca_bot.log",
    encoding="utf-8",
    # filemode="w",
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
)
today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
logging.info(today)
# from apscheduler.schedulers.blocking import BlockingScheduler

# Cloudinary libraries for uploading/getting images
import cloudinary
import cloudinary.api

# Set locale to Spanish for date formatting
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    # Fallback: use the default locale or log a warning
    pass

# Load environment variables from .env file
load_dotenv()


# Get credentials with error handling
def get_credential(name):
    value = os.getenv(name)
    if not value:
        logging.error(f"Missing required environment variable: {name}")
        raise ValueError(f"Missing required environment variable: {name}")
    return value


# Twitter API credentials
client = tweepy.Client(
    bearer_token=get_credential("X_BEARER_TOKEN"),
    consumer_key=get_credential("X_API_KEY"),
    consumer_secret=get_credential("X_API_KEY_SECRET"),
    access_token=get_credential("X_ACCESS_TOKEN"),
    access_token_secret=get_credential("X_ACCESS_TOKEN_SECRET"),
)

auth = tweepy.OAuthHandler(
    get_credential("X_API_KEY"),
    get_credential("X_API_KEY_SECRET"),
    get_credential("X_ACCESS_TOKEN"),
    get_credential("X_ACCESS_TOKEN_SECRET"),
)

auth.set_access_token(
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_TOKEN_SECRET"),
)

api = tweepy.API(auth)


def ConnectToCloudinary():
    # Connect to Cloudinary
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )
    # Check if the connection is successful
    try:
        cloudinary.api.ping()
        logging.info("\nCloudinary connection successful!\n")
        # GetFolderFiles()
        return cloudinary
    except Exception as e:
        logging.info("Error connecting to Cloudinary")
        return None


def GetFolderFiles():
    folder_name = "Hemeroteca_bot"
    try:
        # Fetch all resources in the specified folder
        resources = cloudinary.api.resources(
            type="upload", prefix=folder_name, max_results=500
        )
        files = resources.get("resources", [])
        for file in files:
            # TODO: Check if file exist in data.json. if not, add it as a template element of the json.
            logging.debug(f"URL: {file}\n")
        return files
    except Exception as e:
        logging.debug(f"Error fetching files from folder '{folder_name}': {e}")
        return []


# Function to post tweets from JSON file
def post_scheduled_tweets():
    json_path = os.path.join(os.path.dirname(__file__), "data.json")
    # Load JSON file
    logging.debug(f"Loading JSON file from {json_path}...")
    with open(json_path, "r") as f:
        logging.debug("Loading JSON file...")
        tweets = json.load(f)

    # Get current date and time
    now = datetime.now()

    not_posted = 0
    posted = 0
    for tweet in tweets:
        # Parse the scheduled date and time
        scheduled_time = datetime.strptime(tweet["date"], "%Y-%m-%dT%H:%M:%S")

        # Check if the tweet is scheduled for the current date
        if scheduled_time.date() == now.date() and not tweet.get("isPublished", False):
            posted += 1
            # Download the image from Cloudinary
            image_url = tweet["image"]
            logging.info(f"Downloading image from Cloud")  # {image_url}
            image_response = requests.get(image_url)
            image_path = f"{os.path.dirname(__file__)}/temp_image.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(image_response.content)

            # Upload the image to Twitter
            media = api.media_upload(image_path)
            logging.info(f"Image uploaded: {media.media_id}")
            # Post the tweet with the image and text
            if tweet["published"] != "":
                published_date = datetime.strptime(tweet["published"], "%Y-%m-%d")
                formatted_date = published_date.strftime("%d de %B de %Y")
            if tweet["published"] == "":
                formatted_date = "Hace un tiempo."
            if tweet["text"] == "":
                tweet_text = f"Publicado el {formatted_date}"
            else:
                tweet_text = f"{tweet['text']}  📅 Publicado originalmente el {formatted_date}.  📚 Fuente: Biblioteca Nacional de Panamá."

            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            tweet["isPublished"] = True
            logging.info(f"Tweet posted: {tweet_text}")

            # Remove the temporary image file# logging.debug(f"Scheduled time: {scheduled_time}")
        # TODO: Eliminate the boolean to check and keep just the date
        if tweet["isPublished"] == False:
            not_posted += 1
        if tweet["isPublished"] == True:
            posted += 1
    logging.info(f"Not posted: {not_posted}, posted: {posted}")
    # Save the updated JSON file
    with open(json_path, "w") as f:
        json.dump(tweets, f, indent=4)
        logging.info("Updated JSON file saved.")


# Scheduler to run the function once every 24 hours
# scheduler = BlockingScheduler()
# scheduler.add_job(post_scheduled_tweets, "interval", seconds=10)
# scheduler.start()

# ConnectToCloudinary()
post_scheduled_tweets()
