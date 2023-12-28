# Ambibulb

_A local, open source, room level ambilight algorithm using Home Assistant Websocket API_

## Installation

Tested with Home Assistant & Zigbee2MQTT & Phillips Hue Lightbulb, but you can make it work with any device that works with home assistant

1. Install Python 3.11
2. Clone this repo `git clone git@github.com:mbourand/ambibulb.git` or download it
3. Create a virtual environment with `python3.11 -m venv venv`
4. Go in the virtual environment with `source venv/bin/activate` on Linux or `./venv/Scripts/activate` on Windows
5. Install the requirements with `pip install -r requirements.txt`
6. Copy or rename .env.example to .env
7. Copy or rename command.template.example.json to command.template.json (the example template matches for a Phillips Hue lightbulb)
8. Replace `COMMAND_PATH` in the `.env` to `command.template.json`
9. Replace `device_id_here` in `command.template.json` with your device id in Home Assistant
10. Replace the `ACCESS_TOKEN` and `WEBSOCKET_URL` in the `.env` with the values that matches your setup (you can generate a long lasting token via the Home Assistant interface)
11. Run the program with `python ambibulb.py`
12. Edit any value in the `.env` that doesn't suit your needs, the correct configuration depends a lot on preferences, room, device, and so on
