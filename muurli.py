#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import logging
from icecream import ic
import openai, os, json
from dotenv import load_dotenv

load_dotenv()

def get_menu():
    url = "https://stadtmuur.ch/item/woche-aktuell/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    logging.info("Getting menu from %s", url)
    response = requests.get(url, headers=headers, verify=False)
    ic(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    menu=soup.select("article")
    return menu

def menu_to_json():
    menu = get_menu()
    text = menu[0].get_text("\n") if menu else "No menu found"

    client = openai.OpenAI()  # <-- Neue API-Initialisierung
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract the menu items and format them as JSON."},
            {"role": "user", "content": text}
        ]
    )

    json_output = response.choices[0].message.content
    return json.loads(json_output)



if __name__=="__main__":
    ic(menu_to_json())
