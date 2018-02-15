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
    NETWORK_RATES = [50, 200, 500, 0]

class NETWORK_DIRECTION:
    UP = 1
    DOWN = -1

class Car(object):
    
    @property
    def Accuracy(self):
        return self._Accuracy

    @Accuracy.setter
    def Accuracy(self, value):
        print("Accuracy set to ", value)
        self._Accuracy = round(value, 2)

    @property
    def AverageAccuracy(self):
        return self._Accuracy

    @AverageAccuracy.setter
    def AverageAccuracy(self, value):
        self._Accuracy = round(value, 2)

    @property
    def NetDelay(self):
        return self._NetDelay

    @NetDelay.setter
    def NetDelay(self, value):
        self._NetDelay = value

    def __init__(self):
        self.Status = CarState.UNKNOWN
        self._NetDelay = 50
        self.Laps = 0
        self.Score = 0
        self._Accuracy = 0.0

    def Reset(self):
        self.Status = CarState.WAITING
        self._NetDelay = 50
        self.Laps = 0
        self._Accuracy = 0.0
        self.Score = 0
