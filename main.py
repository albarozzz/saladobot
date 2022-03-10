#!/usr/bin/env python3
import tweepy
import datetime
import time
import requests
from io import BytesIO
from settings import *

auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, key, secret
)

api = tweepy.API(auth)

# fake user agent to spoof and download images.
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 " \
             "Safari/537.36 "

with open("parte.txt", "r") as f:
    parte = f.read()

while True:
    now = datetime.datetime.utcnow()
    if now.hour == 22:
        word = requests.get(
            "https://es.metapedia.org/m/api.php",
            params={"format": "json",
                    "action": "query",
                    "generator": "random",
                    "grnnamespace": "0",
                    "prop": "revisions",
                    "rvprop": "content",
                    "grnlimit": "25"}
        )
        if word.status_code == 200:
            status = api.update_status(status=f"Bienvenido a la parte {parte} de CITA Y OPINA")
            last_status = status.id_str
            for i in range(0, 10):
                pages = word.json()["query"]["pages"]
                title = pages[list(pages)[i]]["title"]
                images = requests.get("https://customsearch.googleapis.com/customsearch/v1",
                                      params={"q": title,
                                              "cx": cx,
                                              "searchType": "image",
                                              "key": google_api},
                                      headers={"Accept": "application/json"}
                                      )
                z = 0
                image = None
                while True:
                    image_og = images.json()["items"][z]
                    try:
                        image = BytesIO(requests.get(image_og["link"],
                                                     headers={"Referer": "google.com",
                                                              "User-Agent": user_agent}).content)
                        image.seek(0)
                        image = api.media_upload(file=image, filename="dummy")
                    except Exception as err:
                        if z == 8:
                            print(err, type(err))
                            print(f"Error downloading image! {image_og['link']} trying thumbnail...")
                            image = BytesIO(requests.get(image_og["image"]["thumbnailLink"],
                                                         headers={"Referer": "google.com",
                                                                  "User-Agent": user_agent}).content)
                            image.seek(0)
                            image = api.media_upload(file=image, filename="dummy")
                            break
                        else:
                            continue

                status = api.update_status(status=title,
                                           media_ids=[image.media_id_string] if image else None,
                                           in_reply_to_status_id=last_status
                                           )
                last_status = status.id_str
                time.sleep(15)  # cooldown
            parte = str(int(parte) + 1)
            with open("parte.txt", "w") as f:
                f.seek(0)
                f.truncate()
                f.write(parte)
            time.sleep(3700)
    time.sleep(15)
