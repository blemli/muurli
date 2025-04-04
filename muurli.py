#!/usr/bin/env python

from bs4 import BeautifulSoup
from icecream import ic
import openai, json, blemli, subprocess,logging,requests,sys
from dotenv import load_dotenv

load_dotenv()

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
    with open("menues.json", "r") as f:
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

def generate_menu_picture(menu,date):
    image_name = f"./images/{date}.png"
    try:
        with open(image_name, "rb") as f:
            logging.info(f"Image already exists: {image_name}")
            return
    except FileNotFoundError:
        logging.info(f"Image does not exist: {image_name}")
        logging.info("Generating image")
    client = openai.OpenAI()
    prompt = f"Erstelle ein Bild von einem weissen Teller auf einem Holztisch, gefüllt bis zum Rand mit folgendem Gericht: {menu['main_course']}. Keine zusätzlichen Speisen hinzufügen! Einfach, rustikal und authentisch!"    
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
    )
    image_url = response.data[0].url    
    with open(image_name, "wb") as f:
        f.write(requests.get(image_url).content)
    logging.info(f"Image saved to {image_name}")

if __name__=="__main__":
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = blemli.from_date()
    menues=update_menues()
    current_menu=menues[date]
    print(current_menu["main_course"])
    generate_menu_picture(current_menu,date)
    subprocess.run(["qlmanage","-p", f"./images/{date}.png"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)