from globals import *

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

def get_percieved_brightness(r, g, b):
	normalized_r, normalized_g, normalized_b = r / 255, g / 255, b / 255

	y = RED_PERCIEVED_BRIGHTNESS_FACTOR * normalized_r + \
		GREEN_PERCIEVED_BRIGHTNESS_FACTOR * normalized_g + \
		BLUE_PERCIEVED_BRIGHTNESS_FACTOR * normalized_b

	if (y <= (216 / 24389)):
		return y * (24389 / 27)
	else:
		return pow(y, 1 / 3) * 116 - 16