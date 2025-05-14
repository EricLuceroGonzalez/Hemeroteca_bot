# twitter-text.py
from datetime import date
from numpy import median
import tweepy
import os
import pathlib
import random
from dotenv import load_dotenv

xx = "\n++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ ++++++ "
load_dotenv()  # This line brings all environment variables from .env into os.environ

# credentials to access Twitter API
# create an OAuthHandler instance
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
check = api.verify_credentials()
image = "1899-Anuncio-en-el-diario-El-Tio-Sam-cuando-se-usaba-el-sistema-colombiano-de-nomenclatura-de-calles.png"
imageURL = "https://res.cloudinary.com/dcvnw6hvt/image/upload/v1599179407/Academo/Identidy/academoLogoC_oxeawu.png"
parentPath = str(pathlib.Path(__file__).parent.absolute())
imagePath = parentPath + "/images/"

media1 = api.media_upload(imagePath + image)
# client.create_tweet(text='I want to Post 3 Photos and description')#,media_ids=[media1])
client.create_tweet(
    text="This is a test! #DeveloperWorking", media_ids=[media1.media_id]
)
# client.create_tweet(text="This is a test! #DeveloperWorking")


# tweet the price of Bitcoin
def tweet_bitcoin_price():
    price = random.randint(28000, 35000)
    tweet = f"Hello {date.today} USD"
    client.create_tweet(text=tweet)
    # client.create_tweet(media_ids=[imagePath+image])
    print(tweet)
    return client


# main function
def main():
    print("here in main")

    # tweet_bitcoin_price()


# call main function
if __name__ == "__main__":
    main()
