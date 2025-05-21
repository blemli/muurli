#!/usr/bin/env python

from bs4 import BeautifulSoup
from icecream import ic
import openai, json, blemli, subprocess, logging, requests, sys, os, click
from dotenv import load_dotenv
from PIL import Image
from rich.console import Console
from rich.table import Table


load_dotenv()

MENUE_FILE=os.path.dirname(__file__)+"/menues.json"
IMAGE_FOLDER=os.path.dirname(__file__)+"/images"
EXTRACTION_PROMPT=os.path.dirname(__file__)+"/extraction_prompt.txt"
URL="https://stadtmuur.ch/item/woche-aktuell/"

def get_menu():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    logging.info(f"Getting menu from {URL}")
    # Properly handle SSL verification
    try:
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        menu = soup.select("article")
        return menu
    except requests.exceptions.SSLError:
        logging.warning("SSL verification failed. Falling back to unverified request.")
        # Import warnings to suppress InsecureRequestWarning
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(URL, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        menu = soup.select("article")
        return menu

def menu_to_json(html_menu):
    logging.info("parse menu to json with gpt")
    text = html_menu[0].get_text("\n") if html_menu else None
    with open(EXTRACTION_PROMPT, "r") as f:
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
    return json.loads(json_output)

def update_menues(force=False, date=None):
    if not os.path.exists(MENUE_FILE):
        logging.warning(f"{MENUE_FILE} does not exist, creating new file")
        with open(MENUE_FILE, "w+") as f:
            json.dump({}, f, indent=4)
    with open(MENUE_FILE, "r+") as f:
        menues = json.load(f)
    
    today = blemli.from_date() if date is None else date
    
    if today not in menues or force:
        if force:
            logging.info(f"Force flag set, regenerating menu for {today}")
        else:
            logging.info(f"Fetching menu for {today}")
            
        html_menu = get_menu()
        try:
            this_week = menu_to_json(html_menu=html_menu)

            menues.update(this_week)
            with open(MENUE_FILE, "w+") as f:
                json.dump(menues, f, indent=4)
        except Exception as e:
            logging.error(f"Error processing menu data: {e}")
            if today not in menues.keys():
                # Only raise if we don't have any data for this date
                raise
    
    return menues

def generate_menu_picture(dish,suffix,date,force=False):
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    image_name = f"{IMAGE_FOLDER}/{date}{suffix}.png"
    if not force:
        try:
            with open(image_name, "rb") as f:
                logging.info(f"Image already exists: {image_name}")
                return
        except FileNotFoundError:
            logging.info(f"Image does not exist: {image_name}")
            logging.info("Generating image")
    else:
        logging.info(f"Force flag set, regenerating image: {image_name}")
    client = openai.OpenAI()
    prompt = f"Erstelle ein Bild von einem weissen Teller auf einem Holztisch, gefüllt bis zum Rand mit folgendem Gericht: {dish}. Keine zusätzlichen Speisen hinzufügen! Einfach, rustikal und authentisch"
    logging.info("generating image with dalle")
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
    )
    
    # Check if the response contains a URL or base64 data
    if hasattr(response.data[0], 'url') and response.data[0].url:
        image_url = response.data[0].url
        try:
            image_response = requests.get(image_url)
            image_response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            with open(image_name, "wb") as f:
                f.write(image_response.content)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading image from {image_url}: {e}")
            raise ValueError(f"Failed to download image: {e}")
    elif hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
        # Handle base64 encoded image data
        import base64
        try:
            image_data = base64.b64decode(response.data[0].b64_json)
            with open(image_name, "wb") as f:
                f.write(image_data)
        except Exception as e:
            logging.error(f"Error decoding base64 image data: {e}")
            raise ValueError(f"Failed to decode base64 image data: {e}")
    else:
        logging.error("No image URL or base64 data found in the response")
        logging.debug(f"Response: {response}")
        raise ValueError("Failed to get image from OpenAI API")
    logging.info(f"Image saved to {image_name}")


def list_menues():
    with open(MENUE_FILE, "r") as f:
        menues = json.load(f)
    table = Table()
    table.add_column("Date", style="bold")
    table.add_column("Meat")
    table.add_column("Vegetarian")
    for date, menu in menues.items():
        if not menu:
            continue
        table.add_row(
            date,
            menu.get("meat", "-"),
            menu.get("vegetarian", "-")
        )
    Console().print(table)

@click.command()
@click.argument('date', default=blemli.from_date() )
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--vegetarian','--vegi', is_flag=True, help='Show only vegetarian options')
@click.option('--no-image', is_flag=True, help='Do not generate image')
@click.option('-l','--list','list_menues_flag', is_flag=True, help='List all available menues')
@click.option('-f', '--force', is_flag=True, help='Ignore caches and regenerate/redownload both image and menu')
@click.option('--web', is_flag=True, help='Show the web version of menu')
def muurli(date,vegetarian,verbose,no_image,list_menues_flag,force,web):
    # Set up logging first
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
        
    if web:
        logging.info(f"Opening web version of menu: {URL}")
        subprocess.run(["open", URL])
        sys.exit(0)
    if list_menues_flag:
        list_menues()
        sys.exit(0)
    menues=update_menues(force=force, date=date)
    
    # Check if the requested date exists in the menu data
    if date not in menues:
        logging.error(f"No menu found for {date}")
        sys.exit(1)
        
    current_menu=menues[date]
    suffix=""
    if current_menu == {}:
        logging.error(f"Menu for {date} is empty")
        sys.exit(1)
    if vegetarian:
        dish=current_menu["vegetarian"]
        suffix="_v"
    else:
        # Handle both "main_course" and "meat" keys for backward compatibility
        if "main_course" in current_menu:
            dish=current_menu["main_course"]
        elif "meat" in current_menu:
            dish=current_menu["meat"]
        else:
            logging.error(f"No main course or meat dish found in menu for {date}")
            sys.exit(1)
    print(dish)
    if not no_image:
        generate_menu_picture(dish,suffix,date,force=force)
        Image.open(f"{IMAGE_FOLDER}/{date}{suffix}.png").show()


if __name__=="__main__":
    muurli()
