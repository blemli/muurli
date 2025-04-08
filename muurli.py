#!/usr/bin/env python

from bs4 import BeautifulSoup
from icecream import ic
import openai, json, blemli, subprocess,logging,requests,sys,os
from dotenv import load_dotenv
from PIL import Image
import click


load_dotenv()

MENUE_FILE=os.path.dirname(__file__)+"/menues.json"
IMAGE_FOLDER=os.path.dirname(__file__)+"/images"

def get_menu():
    url = "http://stadtmuur.ch/item/woche-aktuell/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    logging.info(f"Getting menu from {url}")
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    menu=soup.select("article")
    return menu

def menu_to_json(html_menu):
    logging.info("parse menu to json with gpt")
    text = html_menu[0].get_text("\n") if html_menu else None
    with open("extraction_prompt.txt", "r") as f:
        prompt = f.read()
    client = openai.OpenAI()
    response = client.chat.completions.create(
    model="gpt-4-turbo",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": (prompt)},
        {"role": "user", "content": text}
    ]
    )
    json_output = response.choices[0].message.content
    ic(json_output)
    return json.loads(json_output)

def update_menues():
    with open(MENUE_FILE, "r") as f:
        menues = json.load(f)
    today=blemli.from_date()
    if today not in menues.keys():
        logging.warning("Today not in menues")
        html_menu = get_menu()
        this_week=menu_to_json(html_menu=html_menu)
        ic(this_week)
        menues.update(this_week)
        with open("menues.json", "w") as f:
            json.dump(menues, f, indent=4)
    return menues

def generate_menu_picture(dish,suffix,date):
    image_name = f"{IMAGE_FOLDER}/{date}{suffix}.png"
    try:
        with open(image_name, "rb") as f:
            logging.info(f"Image already exists: {image_name}")
            return
    except FileNotFoundError:
        logging.info(f"Image does not exist: {image_name}")
        logging.info("Generating image")
    client = openai.OpenAI()
    prompt = f"Erstelle ein Bild von einem weissen Teller auf einem Holztisch, gefüllt bis zum Rand mit folgendem Gericht: {dish}. Keine zusätzlichen Speisen hinzufügen! Einfach, rustikal und authentisch"
    logging.info("generating image with dalle")
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
    )
    image_url = response.data[0].url    
    with open(image_name, "wb") as f:
        f.write(requests.get(image_url).content)
    logging.info(f"Image saved to {image_name}")

@click.command()
@click.argument('date', default=blemli.from_date() )
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--vegetarian', is_flag=True, help='Show only vegetarian options')
def muurli(date,vegetarian,verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    menues=update_menues()
    current_menu=menues[date]
    suffix=""
    if current_menu == {}:
        logging.error(f"No menu found for {date}")
        sys.exit(1)
    if vegetarian:
        dish=current_menu["vegetarian"]
        suffix="_v"
    else:
        dish=current_menu["main_course"]
    print(dish)
    generate_menu_picture(dish,suffix,date)
    Image.open(f"{IMAGE_FOLDER}/{date}{suffix}.png").show()



if __name__=="__main__":
    muurli()
