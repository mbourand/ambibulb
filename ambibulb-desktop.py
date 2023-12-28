import websockets
import time
from PIL import ImageGrab
import numpy as np
import asyncio
import json

def lerp(a, b, t):
	return a + (b - a) * min(max(t, 0), 1)

class Transition:
	def __init__(self, from_color, to_color, duration) -> None:
		self.time = time.time() + 0.5 # Estimated latency
		self.from_color = from_color
		self.to_color = to_color
		self.duration = duration

	def current_color(self, time):
		return [lerp(_from, to, (time - self.time) / self.duration) for _from, to in zip(self.from_color, self.to_color)]

def get_rgb():
	image_tmp = ImageGrab.grab()
	image_tmp = image_tmp.resize((image_tmp.size[0] // 8, image_tmp.size[1] // 8))

	image = np.array(image_tmp)
	dominant_color = np.mean(image, axis=(0, 1))
	return dominant_color

def rgb_to_hsv(r, g, b):
	r, g, b = r / 255.0, g / 255.0, b / 255.0
	mx = max(r, g, b)
	mn = min(r, g, b)
	df = mx - mn
	if mx == mn:
		h = 0
	elif mx == r:
		h = (60 * ((g - b) / df) + 360) % 360
	elif mx == g:
		h = (60 * ((b - r) / df) + 120) % 360
	elif mx == b:
		h = (60 * ((r - g) / df) + 240) % 360
	if mx == 0:
		s = 0
	else:
		s = (df / mx) * 100
	v = mx * 100
	return h, s, v

def hsv_to_rgb(h, s, v):
	h = h / 360.0
	s = s / 100.0
	v = v / 100.0
	if s == 0.0:
		v *= 255
		return v, v, v
	i = int(h * 6.)
	f = (h * 6.) - i
	p, q, t = int(255 * (v * (1. - s))), int(255 * (v * (1. - s * f))), int(255 * (v * (1. - s * (1. - f))))
	v *= 255
	i %= 6
	if i == 0:
		return v, t, p
	if i == 1:
		return q, v, p
	if i == 2:
		return p, v, t
	if i == 3:
		return p, q, v
	if i == 4:
		return t, p, v
	if i == 5:
		return v, p, q

def get_perceptual_lightness(r, g, b):
	vR, vG, vB = r / 255, g / 255, b / 255
	y = 0.9 * vR + 0.6 * vG + 0.03 * vB
	if (y <= (216 / 24389)):
		return y * (24389 / 27)
	else:
		return pow(y, 1 / 3) * 116 - 16

def get_brightness_ratio(r, g, b, desired_percieved_luminance, precision=0.01):
	percived_luminance = get_perceptual_lightness(r, g, b)
	if percived_luminance == 0:
		return 0

	start_sign = np.sign(desired_percieved_luminance - percived_luminance)
	if start_sign == 0:
		return 1

	ratio = 1
	while np.sign(desired_percieved_luminance - get_perceptual_lightness(r * ratio, g * ratio, b * ratio)) == start_sign:
		ratio += precision * start_sign

	return ratio

async def main():
	current_id = 1
	old_hsv = (0, 0, 0)
	current_transition = None

	async with websockets.connect('ws://homeassistant.local:8123/api/websocket') as websocket:
		auth_required_message = await websocket.recv()
		print(auth_required_message)
		await websocket.send('{"type": "auth", "access_token": "token"}')
		auth_response = json.loads(await websocket.recv())
		print(auth_response)
		if auth_response['type'] != 'auth_ok':
			raise Exception('Authentication failed')

		no_update_count = 0
		while True:
			r, g, b = get_rgb()
			h, s, v = rgb_to_hsv(r, g, b)
			old_h, old_s, _ = old_hsv
			if abs(old_h - h) < 20 and abs(old_s - s) < 20:
				time.sleep(0.2)
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
			v = 50
			r, g, b = hsv_to_rgb(h, s, v)
			h_value_change_per_second = 25 / 100 * 180
			s_value_change_per_second = 25 / 100 * 100
			brightness_change_per_second = 10 / 100 * 100

			current_bulb_h, current_bulb_s, current_bulb_v = current_transition.current_color(time.time()) if current_transition else (0, 0, 0)
			brightness = min((np.sqrt(original_v / 50) / 1.7) * get_brightness_ratio(r, g, b, 420, precision=0.02), 100)

			transition_time = round(max(min(abs(current_bulb_h - h), abs(current_bulb_h - (360 - h))) / h_value_change_per_second, abs(current_bulb_s - s) / s_value_change_per_second, abs(brightness - current_bulb_v) / brightness_change_per_second), 1)
			message = json.dumps({
				"id": current_id,
				"type": "call_service",
				"domain": "light",
				"service": "turn_on",
				"target": {
					"device_id": "id"
				},
				"service_data": {
					"brightness_pct": brightness,
					"rgb_color": [r, g, b],
					"transition": transition_time
				}
			})
			await websocket.send(message)
			response = json.loads(await websocket.recv())
			print(response)
			current_id += 1
			current_transition = Transition((current_bulb_h, current_bulb_s, current_bulb_v), (h, s, brightness), transition_time)
			old_hsv = (h, s, v)
			time.sleep(0.2)

if __name__ == '__main__':
	asyncio.run(main())