# murli
**In den Topf schauen**

[Inky Impression 7.3" (7 colour ePaper/E Ink HAT)](https://www.pi-shop.ch/an-extra-large-7-3-800-x-480-pixel-7-colour-e-ink-display-for-raspberry-pi)

## Usage

1. clone and enter

   ```bash
   git clone https://github.com/blemli/muurli && cd muurli
   ```

2. add openai key to .env

   ```bash
   echo 'OPENAI_API_KEY="xxxxxx"' > .env
   ```

   > [!TIP]
   >
   > be lazy and get it from 1pw
   >
   > ```bash
   > echo "OPENAI_API_KEY=$(op item get lnxaa66mnx435aii6k62zcz6ee --reveal --field Anmeldedaten)" > .env
   > ```

3. create venv

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. install dependencies

   ```bash
   pip install -r requirements.txt
   ```

5. run

   ```bash
   ./muurli.py --help
   ```



//todo: make installable with pipx

## use as a service

```bash
sudo mkdir /opt/muurli
chown /opt/muurli
sudo chown -R pi  /opt/muurli
sudo apt install -y git vim
git clone https://github.com/blemli/muurli  /opt/muurli/
cd /opt/git
python3 -m venv .venv
source .venv/bin/activate
sudo apt update
sudo apt install python3-dev
pip install -r requirements.txt
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
echo "dtoverlay=spi0-0cs" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```





> [!TIP]	
>
> use the image.py --file xy.png to show custom images on the screen

