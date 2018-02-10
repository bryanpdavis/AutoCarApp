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
from Message import Messenger

DEBUG_APP = True
HOST = '192.168.1.240'
PORT = 21567
PORT2 = 21568
BUFSIZ = 2048
ADDR = (HOST, PORT)
ADDR2 = (HOST, PORT2)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
size = [500, 800]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Joystick Tester")
REFRESH_RATE = 20
clock = pygame.time.Clock()



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

# =============================================================================
# Setup the Pygame
# =============================================================================


CAR_NOT_SET = '-1'
CAR_LAP = '1000'
CAR_SET = '255'

Car = game_state.Car()

# Start the Car Status as UNKNOWN until the Scoring Thread sees that the car is on the line i.e. READY
Car.Status = game_state.CarState.UNKNOWN

def Scoring_Thread(state, messenger):
    while True:
        data = messenger.receive("READYIndicator")
        if not data:
            sleep(1)
            continue

        if data == CAR_LAP:
            #Car is on the line, change
            state.Status = game_state.CarState.READY
            break

    while state.Status == game_state.CarState.READY:
        #Car Status is READY, loop until the main loop indicates the car is running.
        pass
    
    LapFound = False
    while state.Status == game_state.CarState.RUNNING:
        #Car Status is RUNNING, begin gathering scores from the line sensor and look for Laps
        score = messenger.receive("SensorScore")

        print("Sensor Score: " + str(score))
        
        #If we sense a Lap, we make sure that LapFound has been reset to false to ensure we aren't double counting laps
        if score == CAR_LAP and LapFound == False:
            state.Laps += 1
            LapFound = True

        elif int(score) > int(CAR_NOT_SET) and int(score) != int(CAR_LAP):
            #Car in RUNNING, toggle LapFound to allow for new laps to be counted.
            LapFound = False
            record_score(score)
        
        if state.Laps == len(game_state.CarState.NETWORK_RATES):
            state.Status = game_state.CarState.FINISHED
    
    calculate_total_score(state)

        #url = 'http://192.168.1.240:8080'
        #resp = requests.get(url=url, params=None)
        #data = json.loads(resp.text)
        #print("Sensor Value" + data['temperature']['value'])

# =============================================================================
# Scoring Functions for the Round
# =============================================================================
user_scores = []

def record_score(score):
    if score != '1000':
        user_scores.append(int(score))
        print("Score Received", score)

def calculate_total_score(state):
    print("Total Score: " + str(sum(user_scores) / float(len(user_scores))))
    state.Status = game_state.CarState.FINISHED

# =============================================================================
# Setup the Game Loop
# =============================================================================

def process_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True

def Controller(state, messenger):
    # Initialize the joysticks
    pygame.joystick.init()
    done = False
    FORWARD = 1
    BACKWARD = -1
    my_controller = xbox360_controller.Controller(0)
    stopped = True
    direction = FORWARD
    DELAY = 0.0;

    networklatency = 0
    network_can_go_up = True
    network_can_go_down = True
    current_steering = 0

    messenger.send("network=0")

    done = False

    while done==False:
        # Event processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # Drawing code
        screen.fill(BLACK)
        textPrint.reset()

        # Get count of joysticks
        joystick_count = pygame.joystick.get_count()

        textPrint.printText(screen, "Number of joysticks: {}".format(joystick_count) )
        textPrint.indent()

        # For each joystick:
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

        if state.Status == game_state.CarState.READY or state.Status == game_state.CarState.RUNNING:
            
            speed = my_controller.joystick.get_axis(1)
            
            if speed < -.01:
                state.Status = game_state.CarState.RUNNING
                spd = (speed * -100.0)
                cmd = ''
                if direction == FORWARD:
                    cmd = 'forward=' + str(int(spd))
                    print("Forward", "Speed set to", cmd)
                elif direction == BACKWARD:
                    cmd = 'backward=' + str(int(spd))
                    print("Backward", "Speed set to", cmd)
                messenger.send(cmd)
                stopped = False
            elif speed > -.01 and stopped == False:
                stopped = True
                messenger.send('stop')

            steering = my_controller.joystick.get_axis(0)

            if current_steering != steering:
                current_steering = steering
                if steering > 0.1:
                    cmd = 'offset=+' + str(int(steering * 70.0))
                    messenger.send(cmd)
                elif steering < 0.1:
                    cmd = 'offset=' + str(int(steering * 70.0))
                    messenger.send(cmd)
                else:
                    messenger.send('home')

            networkup = my_controller.joystick.get_button(11)
            networkdown = my_controller.joystick.get_button(10)
            
            if networkup == 0:
                network_can_go_up = True
            
            if networkdown == 0:
                network_can_go_down = True

            if networkup == 1 and network_can_go_up:
                network_can_go_up = False
                networklatency = networklatency + 10
                cmd = 'network=' + str(networklatency)
                #print("Network latency set to ", networklatency)
                messenger.send(cmd)
            elif networkdown == 1 and network_can_go_down:
                network_can_go_down = False
                if networklatency > 0:
                    networklatency = networklatency - 10
                    #print("Network latency set to ", networklatency)

                cmd = 'network=' + str(networklatency)
                messenger.send(cmd)

            forwardpaddle = my_controller.joystick.get_button(4)
            backwardpaddle = my_controller.joystick.get_button(5)

            if forwardpaddle == 1:
                direction = FORWARD
            elif backwardpaddle == 1:
                direction = BACKWARD

lineSensorMsgr = Messenger(ADDR2)
t = threading.Thread(target=Scoring_Thread, args=(Car, lineSensorMsgr))
t.daemon = True

carControllerMsgr = Messenger(ADDR)
t2 = threading.Thread(target=Controller, args=(Car, carControllerMsgr))
t2.daemon = True

def main():
    t.start()
    t2.start()
    while True:
            sleep(.001)
	
if __name__ == '__main__':
    try:
        main()
        
    except (KeyboardInterrupt, SystemExit):
        print('closing lineSensorMsgr')
        lineSensorMsgr.close()
        print('closing carControllerMsgr')
        carControllerMsgr.close()
        print('Sockets Closed')
        sys.exit(0)
        os._exit(0)
        