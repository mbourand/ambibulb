import websockets
import time
from PIL import ImageGrab
import numpy as np
import asyncio
import json
from Transition import *
from colors import *
from globals import *

def create_command(template, **kwargs):
	for key, value in kwargs.items():
		template = template.replace("{{" + key + "}}", str(value))
	return template

def compute_ambilight_color():
	image_tmp = ImageGrab.grab()
	image_tmp = image_tmp.resize((image_tmp.size[0] // 8, image_tmp.size[1] // 8))

	image = np.array(image_tmp)
	dominant_color = np.mean(image, axis=(0, 1))
	return dominant_color

def get_brightness_ratio(r, g, b, desired_percieved_luminance, precision=0.01):
	percived_luminance = get_percieved_brightness(r, g, b)
	if percived_luminance == 0:
		return 0

	start_sign = np.sign(desired_percieved_luminance - percived_luminance)
	if start_sign == 0:
		return 1

	ratio = 1
	while np.sign(desired_percieved_luminance - get_percieved_brightness(r * ratio, g * ratio, b * ratio)) == start_sign:
		ratio += precision * start_sign

	return ratio

async def main():
	current_id = 1
	old_hsv = (0, 0, 0)
	current_transition = None

	async with websockets.connect(WEBSOCKET_URL) as websocket:
		auth_required_message = await websocket.recv()
		print(auth_required_message)
		await websocket.send('{"type": "auth", "access_token": "' + ACCESS_TOKEN + '"}')
		auth_response = json.loads(await websocket.recv())
		print(auth_response)
		if auth_response['type'] != 'auth_ok':
			raise Exception('Authentication failed')

		no_update_count = 0
		while True:
			r, g, b = compute_ambilight_color()
			h, s, v = rgb_to_hsv(r, g, b)
			old_h, old_s, _ = old_hsv
			if abs(old_h - h) < MINIMUM_HUE_CHANGE_TO_TRIGGER_TRANSITION and abs(old_s - s) < MINIMUM_SATURATION_CHANGE_TO_TRIGGER_TRANSITION:
				time.sleep(WAIT_SECONDS_AFTER_COMMAND)
				no_update_count += 1
				if no_update_count > 10:
					# Keep connection alive by pinging
					await websocket.send('{"id": 0, "type": "ping"}')
					response = json.loads(await websocket.recv())
					print(response)
					no_update_count = 0
				continue
			no_update_count = 0
			original_v = v
			v = FORCED_VALUE_CHANNEL
			r, g, b = hsv_to_rgb(h, s, v)

			current_bulb_h, current_bulb_s, current_bulb_v = current_transition.current_color(time.time()) if current_transition else (0, 0, 0)

			scene_brightness_variation_factor = np.sqrt(original_v * BRIGHTNESS_VARIATION_SQRT_FACTOR) * BRIGHTNESS_VARIATION_FACTOR
			brightness = min(scene_brightness_variation_factor * get_brightness_ratio(r, g, b, BASE_BRIGHTNESS, precision=0.02), 100)

			hue_transition_time = min(abs(current_bulb_h - h), abs(current_bulb_h - (360 - h))) / HUE_TRANSITION_SPEED_PERCENT_PER_SECOND
			saturation_transition_time = abs(current_bulb_s - s) / SATURATION_TRANSITION_SPEED_PERCENT_PER_SECOND
			brightness_transition_time = abs(brightness - current_bulb_v) / BRIGHTNESS_TRANSITION_SPEED_PERCENT_PER_SECOND
			transition_time = round(max(hue_transition_time, saturation_transition_time, brightness_transition_time), 1)

			message = create_command(COMMAND_TEMPLATE, REQUEST_ID=current_id, BRIGHTNESS=brightness, RED=r, GREEN=g, BLUE=b, TRANSITION_SECONDS=transition_time)
			await websocket.send(message)
			response = json.loads(await websocket.recv())
			print(response)
			current_id += 1
			current_transition = Transition((current_bulb_h, current_bulb_s, current_bulb_v), (h, s, brightness), transition_time)
			old_hsv = (h, s, v)
			time.sleep(WAIT_SECONDS_AFTER_COMMAND)

if __name__ == '__main__':
	asyncio.run(main())