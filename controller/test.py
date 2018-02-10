#!/usr/bin/python
import os, sys
import time
import threading
import json, requests
import xbox360_controller
import pygame
import game_state
from socket import *
from threading import *
from time import sleep

DEBUG_APP = True
HOST = '192.168.1.240'
PORT = 21567
PORT2 = 21568
BUFSIZ = 1024
ADDR = (HOST, PORT)
ADDR2 = (HOST, PORT2)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


# =============================================================================
# Text printing functions for the scoring
# =============================================================================
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def printText(self, screen, textString):
        textBitmap = self.font.render(textString, True, WHITE)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 18

    def indent(self):
        self.x += 20

    def unindent(self):
        self.x -= 20

# Get ready to print
textPrint = TextPrint()

Car = game_state.Car()

# Start the Car Status as UNKNOWN until the Scoring Thread sees that the car is on the line i.e. READY
Car.Status = game_state.CarState.UNKNOWN

def Controller():
	pygame.joystick.init()
	done = False
	FORWARD = 1
	BACKWARD = -1
	my_controller = xbox360_controller.Controller(0)
	while True:
		#Drawing code
		textPrint.reset()
		screen.fill(BLACK);

		if DEBUG_APP == True:
			# Get count of joysticks
			joystick_count = pygame.joystick.get_count()

			textPrint.printText(screen, "Number of joysticks: {}".format(joystick_count) )
			textPrint.indent()

			#For each joystick:
			for i in range(joystick_count):
				joystick = pygame.joystick.Joystick(i)
				joystick.init()

				textPrint.printText(screen, "Joystick {}".format(i) )
				textPrint.indent()

			# Get the name from the OS for the controller/joystick
				name = joystick.get_name()
				textPrint.printText(screen, "Joystick name: {}".format(name) )

			# Usually axis run in pairs, up/down for one, and left/right for the other.
				axes = joystick.get_numaxes()
				textPrint.printText(screen, "Number of axes: {}".format(axes) )
				textPrint.indent()

				for i in range( axes ):
					axis = joystick.get_axis( i )
					textPrint.printText(screen, "Axis {} value: {:>6.3f}".format(i, axis) )
				textPrint.unindent()

				buttons = joystick.get_numbuttons()
				textPrint.printText(screen, "Number of buttons: {}".format(buttons) )
				textPrint.indent()

				for i in range( buttons ):
					button = joystick.get_button( i )
					textPrint.printText(screen, "Button {:>2} value: {}".format(i,button) )
				textPrint.unindent()

			# Hat switch. All or nothing for direction, not like joysticks.
			# Value comes back in a tuple.
				hats = joystick.get_numhats()
				textPrint.printText(screen, "Number of hats: {}".format(hats) )
				textPrint.indent()

				for i in range( hats ):
					hat = joystick.get_hat( i )
					textPrint.printText(screen, "Hat {} value: {}".format(i, str(hat)) )
				textPrint.unindent()

				textPrint.unindent()

		# Go ahead and update the screen with what we've drawn.
		pygame.display.flip()
		clock.tick(REFRESH_RATE)

def Scoring_Thread(game_state):
	while True:
		sleep(.001)

t = threading.Thread(target=Scoring_Thread, args=(Car,))
t.daemon = True

t2 = threading.Thread(target=Controller, args=())
t2.daemon = True

def main():
    t.start()
    t2.start()
	
if __name__ == '__main__':
    try:
        main()
        while True:
            sleep(.001)
    except (KeyboardInterrupt, SystemExit):
        print('Sockets Closed')
        sys.exit(0)
        os._exit(0)