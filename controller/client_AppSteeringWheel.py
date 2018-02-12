#!/usr/bin/python
import os, sys
import time
import threading
import json, requests
import xbox360_controller
import pygame
import json
from Car import *
from datetime import datetime, timedelta
from beautifultable import BeautifulTable
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

# =============================================================================
# Setup Pygame
# =============================================================================

pygame.init()
size = [500, 800]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Joystick Tester")
REFRESH_RATE = 20
clock = pygame.time.Clock()
pygame.joystick.init()
my_controller = xbox360_controller.Controller(0)
BASE_FONT = pygame.font.Font(None, 20)

# =============================================================================
# Screen printing functions for the scoring
# =============================================================================
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = BASE_FONT

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
# Scoring and Printing for the Rounds and Rounds Data
# =============================================================================

temp_user_scores = []
final_user_scores = []

def record_score(score):
    if score != '1000':
        temp_user_scores.append(int(score))

def calculate_total_score(total_time):
    average_score = str(sum(temp_user_scores) / float(len(temp_user_scores)))
    print("Total Score: " + average_score)
    final_user_scores.append([len(final_user_scores), average_score, total_time.microseconds / 1000])
    temp_user_scores.clear()
    print_scores()


def print_scores():
    table = BeautifulTable()
    table.column_headers = ["index", "score", "time_lapsed"]
    for item in final_user_scores:
        table.append_row(item)
    
    with open('scores', 'w') as w:
        w.write(str(json.dumps(final_user_scores)))

    print(table)

    
# =============================================================================
# Controller Loop
# =============================================================================

def Controller(car, messenger):
    # Initialize the joysticks
    
    done = False
    FORWARD = 1
    BACKWARD = -1
    
    stopped = True
    direction = FORWARD
    DELAY = 0.0;

    networklatency = 0
    network_can_go_up = True
    network_can_go_down = True
    current_steering = 0
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

        if car.Status == CarState.READY or car.Status == CarState.RUNNING:
            
            speed = my_controller.joystick.get_axis(1)
            
            if networklatency != car.NetDelay:
                networklatency = car.NetDelay
                cmd = 'network=' + str(CarState.NETWORK_RATES[car.Laps])
                print("Sending command:" + cmd)
                messenger.send(cmd)

            if speed < -.01:
                start_time = datetime.now()

                car.Status = CarState.RUNNING
                spd = (speed * -100.0)
                cmd = ''
                if direction == FORWARD:
                    cmd = 'forward=' + str(int(spd))
                    #print("Forward", "Speed set to", cmd)
                elif direction == BACKWARD:
                    cmd = 'backward=' + str(int(spd))
                    #print("Backward", "Speed set to", cmd)
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
        elif car.Status == CarState.FINISHED:
            print("Car FINISHED, Stopping car")
            messenger.send('stop')
            print("Setting car.Status=CarState.SHOWING_SCORE")
            car.Status = CarState.SHOWING_SCORE
            print("Car Status:", car.Status)
        elif car.Status == CarState.SHOWING_SCORE:
            disclaimertext = "This is my disclaimer..."
            screen.fill(WHITE)
            disclaimertext = BASE_FONT.render("Some disclaimer...", 1, (0,0,0))
            screen.blit(disclaimertext, (5, 480))

            scoretext = BASE_FONT.render("Score {0}".format(car.Accuracy), 1, (0,0,0))
            screen.blit(scoretext, (5, 10))

            pygame.display.flip()
            clock.tick(REFRESH_RATE)
        elif car.Status == CarState.KILLING_CONTROLLER:
            print("Killing controller")
            break

        pygame.display.flip()
        clock.tick(REFRESH_RATE)
    car.Status = CarState.RESTART
    print("Exiting controller")
        

CAR_LAP = '1000'

def AccuracyMonitor(car, messenger):
    print("Starting Accuracy Monitor")
    while car.Status == CarState.WAITING:
        data = messenger.receive("READYIndicator")
        msgs = data.split(";")
        for score in msgs:
            if not score:
                sleep(1)
                continue

            #First lap detected. Car is on the line. Set the car state to ready.
            if score == CAR_LAP:
                #Car is on the line, change
                car.Status = CarState.READY
                break

    while car.Status == CarState.READY:
        #Car Status is READY, loop until the main loop indicates the car is running.
        pass
    
    LapFound = False
    start_time = ''
    while car.Status == CarState.RUNNING:
        if not start_time:
            start_time = datetime.now()
        #Car Status is RUNNING, begin gathering scores from the line sensor and look for Laps
        data = messenger.receive("SensorScore")
        msgs = data.split(";")
        for score in msgs:
            print("Sensor Score: " + str(score))
            
            #If we sense a Lap, we make sure that LapFound has been reset to false to ensure we aren't double counting laps
            if score == CAR_LAP and LapFound == False:
                car.Laps += 1
                LapFound = True

                if car.Laps == len(CarState.NETWORK_RATES):
                    car.Status = CarState.FINISHED
                    sleep(1)
                    break
                else:
                    print("Car Laps:", car.Laps, " Length of Network Rates:", len(CarState.NETWORK_RATES))
                    car.NetDelay = CarState.NETWORK_RATES[car.Laps]

            elif int(score) != int(CAR_LAP) and int(score) <= 7:
                #Car in RUNNING, toggle LapFound to allow for new laps to be counted.
                LapFound = False
                record_score(score)

    time_lapsed = datetime.now() - start_time
    print("Total Time Lapsed:", time_lapsed)
    calculate_total_score(time_lapsed)
    start_time = ''

    while True:
        print("Entering Showing Score test loop")
        while car.Status == CarState.SHOWING_SCORE:
            home = my_controller.joystick.get_button(0)
            if home == 1:
                print("x button pressed, starting the round/threads.")
                car.Status = CarState.KILLING_CONTROLLER
                return

try:
    with open("scores") as f:
        final_user_scores = eval(f.read())
except:
    pass

# Start the Car Status as UNKNOWN to make the main() function start the threads
car = Car()
car.Status = CarState.UNKNOWN
lineSensorMsgr = Messenger(ADDR2)
carControllerMsgr = Messenger(ADDR)

t: threading.Thread
t2: threading.Thread

def main():
    try:
        while True:
            if car.Status == CarState.RESTART:
                car.Reset()
                print("Game Finished")
                car.Status = CarState.WAITING
                print("Starting Game Threads")
                t = threading.Thread(target=AccuracyMonitor, args=(car, lineSensorMsgr))
                #t.daemon = True
                t2 = threading.Thread(target=Controller, args=(car, carControllerMsgr))
                #t2.daemon = True
                t.start()
                t2.start()

            if car.Status == CarState.UNKNOWN:
                car.Status = CarState.WAITING
                print("Starting Game Threads")
                t = threading.Thread(target=AccuracyMonitor, args=(car, lineSensorMsgr))
                #t.daemon = True
                t2 = threading.Thread(target=Controller, args=(car, carControllerMsgr))
                #t2.daemon = True
                t.start()
                t2.start()

            sleep(.001)
    except (KeyboardInterrupt, SystemExit):
        t.join()
        t2.join()
        print('closing lineSensorMsgr')
        lineSensorMsgr.close()
        print('closing carControllerMsgr')
        carControllerMsgr.close()
        print('Sockets Closed')
        sys.exit(0)
        os._exit(0)
	
if __name__ == '__main__':
    main()
    
        