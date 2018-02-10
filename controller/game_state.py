import os
import time

class CarState:
	UNKNOWN = -1
	READY = 0
	STOPPED = 1
	RUNNING = 2
	FINISHED = 10

	NETWORK_RATES = [50, 100, 200, 50]

class NETWORK_DIRECTION:
	UP = 1
	DOWN = -1

class Car:
	def __init__(self):
		self.Status = CarState.UNKNOWN
		self.NetDelay = CarState.NETWORK_RATES[0]
		self.Laps = 0

	def __ChangeNetwork(self, direction):
		current_network_index = NETWORK_RATES.index(self.NetDelay)
		requested_index = current_network_index + direction

		try:
			self.NetDelay = NETWORK_RATES[requested_index]
		except:
			self.NetDelay = NETWORK_RATES[current_network_index]
