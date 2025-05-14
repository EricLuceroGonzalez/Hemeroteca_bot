import tweepy
import os
import json
import requests
import locale
from datetime import datetime
from dotenv import load_dotenv

# from apscheduler.schedulers.blocking import BlockingScheduler

# Cloudinary libraries for uploading/getting images
import cloudinary
import cloudinary.api

# Set locale to Spanish for date formatting
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

# Load environment variables from .env file
load_dotenv()

# Twitter API credentials
client = tweepy.Client(
    os.environ["X-BEARER_TOKEN"],
    os.environ["X-API_KEY"],
    os.environ["X-API_KEY_SECRET"],
    os.environ["X-ACCESS_TOKEN"],
    os.environ["X-ACCESS_TOKEN_SECRET"],
)

auth = tweepy.OAuthHandler(
    os.environ["X-API_KEY"],
    os.environ["X-API_KEY_SECRET"],
)

auth.set_access_token(
    os.environ["X-ACCESS_TOKEN"],
    os.environ["X-ACCESS_TOKEN_SECRET"],
)

api = tweepy.API(auth)


def ConnectToCloudinary():
    # Connect to Cloudinary
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    # Check if the connection is successful
    try:
        cloudinary.api.ping()
        print("\nCloudinary connection successful!\n")
        GetFolderFiles()
        return cloudinary
    except Exception as e:
        print("Error connecting to Cloudinary:", e)
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
            print(f"URL: {file['url']}\n")
        return files
    except Exception as e:
        print(f"Error fetching files from folder '{folder_name}': {e}")
        return []


# Function to post tweets from JSON file
def post_scheduled_tweets():
    json_path = os.path.join(os.path.dirname(__file__), "data.json")
    # Load JSON file
    print(f"Loading JSON file from {json_path}...")
    with open(json_path, "r") as f:
        print("\n\n\n Loading JSON file...")
        tweets = json.load(f)

    # Get current date and time
    now = datetime.now()
    print("Current date and time:", now)

    for tweet in tweets:
        # Parse the scheduled date and time
        scheduled_time = datetime.strptime(tweet["date"], "%Y-%m-%dT%H:%M:%S")
        # print(f"Scheduled time: {scheduled_time}")

        # Check if the tweet is scheduled for the current date
        if scheduled_time.date() == now.date() and not tweet.get("isPublished", False):
            # Download the image from Cloudinary
            image_url = tweet["image"]
            print(f"Downloading image from {image_url}")
            image_response = requests.get(image_url)
            image_path = "temp_image.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(image_response.content)

            # Upload the image to Twitter
            media = api.media_upload(image_path)
            print(f"Image uploaded: {media.media_id}")
            # Post the tweet with the image and text
            if tweet["published"] != "":
                published_date = datetime.strptime(tweet["published"], "%Y-%m-%d")
                formatted_date = published_date.strftime("%d de %B de %Y")
            if tweet["published"] == "":
                formatted_date = "Hace un tiempo."
            if tweet["text"] == "":
                tweet_text = f"Publicado el {formatted_date}"
            else:
                tweet_text = f"{tweet['text']} Publicado originalmente el {formatted_date}. Fuente: Biblioteca Nacional de Panamá."

            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            tweet["isPublished"] = True
            print(f"Tweet posted: {tweet['text']}")
    # Save the updated JSON file
    with open(json_path, "w") as f:
        json.dump(tweets, f, indent=4)
        print("Updated JSON file saved.")


# Scheduler to run the function once every 24 hours
# scheduler = BlockingScheduler()
# scheduler.add_job(post_scheduled_tweets, "interval", seconds=10)
# scheduler.start()

ConnectToCloudinary()
post_scheduled_tweets()
