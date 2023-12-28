import time
from globals import *

class Transition:
	def __init__(self, from_color, to_color, duration) -> None:
		self.time = time.time() + DEVICE_ESTIMATED_LATENCY_SECONDS
		self.from_color = from_color
		self.to_color = to_color
		self.duration = duration

	def lerp(self, a, b, t):
		return a + (b - a) * min(max(t, 0), 1)

	def current_color(self, time):
		return [self.lerp(from_value, to_value, (time - self.time) / self.duration) for from_value, to_value in zip(self.from_color, self.to_color)]