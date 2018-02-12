import os
import time
from Message import Messenger

class CarState:
	UNKNOWN = -1
	WAITING = 0
	READY = 1
	STOPPED = 2
	RUNNING = 3
	SHOWING_SCORE = 4
	RESTART = 5
	KILLING_CONTROLLER = 9
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
		self.Score = 0
		self.Accuracy = 0
	def Reset(self):
		self.Status = CarState.WAITING
		self.Laps = 0
		self.Accuracy = 0
		self.Score = 0
