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
from pygame.locals import *
from multiprocessing import *
from time import sleep
from Message import Messenger

DEBUG_APP = False
HOST = '192.168.1.6'
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
size = [1920, 1080]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Joystick Tester")
REFRESH_RATE = 20
clock = pygame.time.Clock()
pygame.joystick.init()
path = os.path.join("fonts")
my_controller = xbox360_controller.Controller(0)
TEXT_FONT = pygame.font.Font(path + "/prstart.ttf", 30, italic=True)
BASE_FONT = pygame.font.Font(None, 60, italic=True)
TITLE_FONT = pygame.font.Font(path + "/crackman.ttf", 100)

SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()

# =============================================================================
# Screen printing functions for the scoring
# =============================================================================
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = BASE_FONT

    def print(self, screen, textString):
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
class Lap(object):
    
    def __init__(self):
        self.Time = 0
        self.AccuracyScores = []

    def SetTime(self, value):
        self.Time = value
    
    def AppendAccuracy(self, value):
        self.AccuracyScores.append(int(value))
        self.Accuracy = round(sum(self.AccuracyScores) / float(len(self.AccuracyScores)), 2)

laps = []
lap_accuracy = []
temp_user_scores = []
final_user_scores = []
total_time_lapsed = ''
current_delay = 50

def record_score(score):
    if score != '1000':
        temp_user_scores.append(int(score))
        Car.AverageAccuracy = round(sum(temp_user_scores) / float(len(temp_user_scores)), 2)
        Car.Accuracy = score

def calculate_total_score(total_time):
    try:
        average_score = round(sum(temp_user_scores) / float(len(temp_user_scores)), 2)

        average_accuracy_percent = round(((float(average_score) * 14.2857) * -1) + 100, 2)
        total_score = 100000 - int(float(total_time.total_seconds()) / (average_accuracy_percent/100) * 100)

        #print("Average Score: " + average_score)
        final_user_scores.append([len(final_user_scores), str(average_accuracy_percent), total_time.total_seconds(), total_score])
        temp_user_scores.clear()
        print_scores()
    except Exception as e:
        print("Error occurred in calculate_total_score", e)

def print_scores():
    table = BeautifulTable()
    table.column_headers = ["index", "score", "time_lapsed", "total_score"]
    for item in final_user_scores:
        table.append_row(item)
    
    with open('scores', 'w') as w:
        w.write(str(json.dumps(final_user_scores)))

    print(table)

def update_lapsed_time(time):
    total_time_lapsed = time

def get_lapsed_time():
    return total_time_lapsed

def changeCarNetDelay(Delay):
    current_delay = Delay
    Car.NetDelay = Delay

CAR_LAP = '1000'

def AccuracyMonitor(car, messenger):
    lap = Lap()
    try:
        ready = False
        print("Starting Accuracy Monitor", "CarStatus", car.Status)
        
        while car.Status == CarState.WAITING:
            print("Car is currently waiting for the ready indicator")
            data = messenger.receive("READYIndicator")
            msgs = data.split(";")
            for score in msgs:
                if not score:
                    sleep(1)
                    continue

                #First lap detected. Car is on the line. Set the car state to ready.
                if score == CAR_LAP:
                    #Car is on the line, change
                    print("Line detected... setting status to READY")
                    car.Status = CarState.READY
                    break
        
        while car.Status == CarState.READY:
            if ready == False:
                print("Car is ready")
                ready = True
            #Car Status is READY, loop until the main loop indicates the car is running.
            pass

        LapFound = False
        start_time = ''
        round_start_time = ''
        while car.Status == CarState.RUNNING:
            if not start_time:
                start_time = datetime.now()
                round_start_time = datetime.now()
            #Car Status is RUNNING, begin gathering scores from the line sensor and look for Laps
            time_lapsed = datetime.now() - start_time
            print_rounds(time_lapsed, car.NetDelay)

            data = messenger.receive("SensorScore")
            msgs = data.split(";")
            for score in msgs:
                if not score:
                    break
                
                print("Sensor Score: " + str(score))
                
                #If we sense a Lap, we make sure that LapFound has been reset to false to ensure we aren't double counting laps
                if score == CAR_LAP and LapFound == False:
                    round_time = datetime.now() - round_start_time
                    lap.SetTime(round_time)
                    
                    car.Laps += 1
                    LapFound = True
                    laps.append(lap)
                    lap = Lap()

                    if car.Laps == len(CarState.NETWORK_RATES):
                        car.Status = CarState.FINISHED
                        sleep(1)
                        break
                    else:
                        round_start_time = datetime.now()
                        changeCarNetDelay(CarState.NETWORK_RATES[car.Laps])

                elif int(score) != int(CAR_LAP) and int(score) <= 7:
                    #Car in RUNNING, toggle LapFound to allow for new laps to be counted.
                    LapFound = False
                    lap.AppendAccuracy(score)
                    record_score(score)

        time_lapsed = datetime.now() - start_time
        print("Total Time Lapsed:", time_lapsed)
        calculate_total_score(time_lapsed)
        start_time = ''
        round_start_time = ''
        round_times = []
        final_user_score_showing = False
        final_rankings_showing = False
        while True:
            print("Entering Showing Score test loop")
            joystick = pygame.joystick.Joystick(0)
            next_screen_time = datetime.now() + timedelta(seconds=5)
            while car.Status == CarState.SHOWING_SCORE:
                if datetime.now() < next_screen_time and final_user_score_showing == False:
                    print_rounds(time_lapsed, None)
                    final_user_score_showing = True
                elif datetime.now() > next_screen_time and final_user_score_showing == True and final_rankings_showing == False:
                    final_rankings_showing = True
                    show_user_ranking()

                if "G29" in joystick.get_name():
                    home = my_controller.joystick.get_button(0)
                elif "G25" in joystick.get_name():
                        home = my_controller.joystick.get_button(0)
                elif "F310" in joystick.get_name():
                    home = my_controller.joystick.get_button(2)
                if home == 1:
                    print("x button pressed, starting the round/threads.")
                    car.Status = CarState.KILLING_CONTROLLER
                    return
    except Exception as e:
        print("Exception occurred", e)

try:
    with open("scores") as f:
        final_user_scores = eval(f.read())
except:
    pass

def show_user_ranking():
    try:
        screen.fill(WHITE)
        i = 0

        rank_title_text = TEXT_FONT.render("RANK", 1, (0,0,0))
        rank_title_text_rect = rank_title_text.get_rect(center=(SCREEN_WIDTH/2, 160))
        rank_title_text_rect.left = 400
        screen.blit(rank_title_text, rank_title_text_rect)

        score_title_text = TEXT_FONT.render("ACCURACY", 1, (0,0,0))
        score_title_text_rect = score_title_text.get_rect(center=(SCREEN_WIDTH/2, 160))
        score_title_text_rect.left = 580
        screen.blit(score_title_text, score_title_text_rect)

        time_title_text = TEXT_FONT.render("TIME", 1, (0,0,0))
        time_title_text_rect = time_title_text.get_rect(center=(SCREEN_WIDTH/2, 160))
        time_title_text_rect.left = 900
        screen.blit(time_title_text, time_title_text_rect)

        time_lapsed_title_text = TEXT_FONT.render("SCORE", 1, (0,0,0))
        time_lapsed_title_text_rect = time_lapsed_title_text.get_rect(center=(SCREEN_WIDTH/2, 160))
        time_lapsed_title_text_rect.left = 1200
        screen.blit(time_lapsed_title_text, time_lapsed_title_text_rect)
        rankings = sorted(final_user_scores, key=lambda tup: tup[3], reverse=True)

        for item in rankings:
            distance = 40*i

            rank_text = TEXT_FONT.render("" + str(i+1) + "", 1, (0,0,0))
            rank_text_rect = rank_text.get_rect(center=(SCREEN_WIDTH/2, 200+distance))
            rank_text_rect.left = 400
            screen.blit(rank_text, rank_text_rect)
        
            accuracy_text = TEXT_FONT.render("{0}%".format(item[1]), 1, (0,0,0))
            accuracy_text_rect = accuracy_text.get_rect(center=(SCREEN_WIDTH/2, 200+distance))
            accuracy_text_rect.left = 580
            screen.blit(accuracy_text, accuracy_text_rect)

            time_text = TEXT_FONT.render("{0}".format(item[2]), 1, (0,0,0))
            time_text_rect = time_text.get_rect(center=(SCREEN_WIDTH/2, 200+distance))
            time_text_rect.left = 900
            screen.blit(time_text, time_text_rect)

            time_lapsed_text = TEXT_FONT.render("{0}".format(item[3]), 1, (0,0,0))
            time_lapsed_text_rect = time_lapsed_text.get_rect(center=(SCREEN_WIDTH/2, 200+distance))
            time_lapsed_text_rect.left = 1200
            screen.blit(time_lapsed_text, time_lapsed_text_rect)

            i += 1
    except Exception as e:
        print("Error on show_user_ranking:", e)

    pygame.display.flip()
    clock.tick(REFRESH_RATE)
    
def print_rounds(time_lapsed, delay):
    screen.fill(WHITE)
    
    total_time_title = BASE_FONT.render("Time Lapsed", 1, (0,0,0))
    total_time_title_rect = total_time_title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    total_time_title_rect.top = 10
    total_time_title_rect.left = 10
    screen.blit(total_time_title, total_time_title_rect)

    time_lapsed_text = TEXT_FONT.render("{0}".format(time_lapsed), 1, (0,0,0))
    time_lapsed_rect = time_lapsed_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    time_lapsed_rect.top = 65
    time_lapsed_rect.left = 50
    screen.blit(time_lapsed_text, time_lapsed_rect)

    
    average_accuracy_title = BASE_FONT.render("Avg Accuracy", 1, (0,0,0))
    average_accuracy_title_rect = average_accuracy_title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    average_accuracy_title_rect.top = 100
    average_accuracy_title_rect.left = 10
    screen.blit(average_accuracy_title, average_accuracy_title_rect)

    try:
        percentage_avg_accuracy = round(((Car.AverageAccuracy * 14.2857) * -1) + 100, 2)
        average_accuracy_text = TEXT_FONT.render("{0}%".format(percentage_avg_accuracy), 1, (0,0,0))
        average_accuracy_rect = average_accuracy_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        average_accuracy_rect.top = 155
        average_accuracy_rect.left = 50
        screen.blit(average_accuracy_text, average_accuracy_rect)
    except:
        pass
    
    if delay != None:
        #Top right data
        latency_title = BASE_FONT.render("Latency", 1, (0,0,0))
        latency_title_rect = total_time_title.get_rect()
        latency_title_rect.top = 10
        latency_title_rect.right = SCREEN_WIDTH+10
        screen.blit(latency_title, latency_title_rect)

        latency_text = TEXT_FONT.render("{0}ms".format(delay), 1, (0,0,0))
        latency_text_rect = time_lapsed_text.get_rect()
        latency_text_rect.top = 65
        latency_text_rect.left = SCREEN_WIDTH-200
        screen.blit(latency_text, latency_text_rect)

        accuracy_title = BASE_FONT.render("Accuracy", 1, (0,0,0))
        accuracy_title_rect = accuracy_title.get_rect()
        accuracy_title_rect.top = 100
        accuracy_title_rect.right = latency_title_rect.right-70
        screen.blit(accuracy_title, accuracy_title_rect)

        try:
            current_accuracy = Car.Accuracy
            percentage_accuracy = round(((int(current_accuracy) * 14.2857) * -1) + 100, 2)
            accuracy_text = TEXT_FONT.render("{0}%".format(percentage_accuracy), 1, (0,0,0))
            accuracy_text_rect = accuracy_text.get_rect()
            accuracy_text_rect.top = 155
            accuracy_text_rect.left = SCREEN_WIDTH-200
            screen.blit(accuracy_text, accuracy_text_rect)
        except:
            pass

    laps_title = BASE_FONT.render("Laps", 1, (0,0,0))
    laps_title_rect = laps_title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    laps_title_rect.top = 400
    laps_title_rect.left = 400
    screen.blit(laps_title, laps_title_rect)
    i = 0
    pygame.display.flip()
    clock.tick(REFRESH_RATE)

    for lap in laps:
        distance = 40*i
        scoretext = TEXT_FONT.render("" + str(i+1) + "    {0}    {1}".format(lap.Time, lap.Accuracy), 1, (0,0,0))
        text_rect = scoretext.get_rect(center=(SCREEN_WIDTH/2, 500+distance))
        text_rect.left = 400
        screen.blit(scoretext, text_rect)
        i += 1

def show_title_screen(car):
    screen.fill(WHITE)
    carImg = pygame.image.load('images/att_2016_logo_with_type.png')
    screen.blit(carImg, (50,50))
    title_text = TITLE_FONT.render("Latency Racer", 1, (0,0,0))
    text_rect = title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    text_rect.top = 200
    text_rect.left = 850
    screen.blit(title_text, text_rect)
    color = (0,159,219)
    pygame.draw.rect(screen,color,(0, 500, 1920, 200))

    home_screen_text = "Place the car on the start line to continue..."
    home_screen_text2 = ''
    if car.Status == CarState.READY:
        home_screen_text = "Steering and pedals are activated."
        home_screen_text2 = "Press the gas pedal to begin racing!"

    instruction_text = TEXT_FONT.render(home_screen_text, 1, (0,0,0))
    instruction_text_rect = instruction_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    instruction_text_rect.top = 580
    screen.blit(instruction_text, instruction_text_rect)

    instruction_text2 = TEXT_FONT.render(home_screen_text2, 1, (0,0,0))
    instruction_text_rect2 = instruction_text2.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    instruction_text_rect2.top = 620
    screen.blit(instruction_text2, instruction_text_rect2)

def main():
    car = Car()
    car.Status = CarState.UNKNOWN
    lineSensorMsgr = Messenger(ADDR2)
    carControllerMsgr = Messenger(ADDR)

    FORWARD = 1
    BACKWARD = -1

    stopped = True
    direction = FORWARD
    DELAY = 0.0;

    done = False
    networklatency = 0
    network_can_go_up = True
    network_can_go_down = True
    current_steering = 0

    first_run = True
    try:
        while True:
            if car.Status == CarState.RESTART:
                #Reset some of the round values
                laps = []
                laps.clear()
                car.Reset()
                first_run = True
                print("Game Finished")
                car.Status = CarState.WAITING
                print("Starting Game Threads")
                t = threading.Thread(target=AccuracyMonitor, args=(car, lineSensorMsgr))
                t.start()

            if car.Status == CarState.UNKNOWN:
                car.Status = CarState.WAITING
                print("Starting Game Threads")
                t = threading.Thread(target=AccuracyMonitor, args=(car, lineSensorMsgr))
                t.start()

            while done==False:
                pygame.event.pump()
                
                for e in pygame.event.get():
                    if (e.type is KEYDOWN and e.key == K_f):
                        if screen.get_flags() & FULLSCREEN:
                            pygame.display.set_mode(size)
                        else:
                            pygame.display.set_mode(size, FULLSCREEN)

                    if e.type == pygame.QUIT:
                        t.join()
                        print('closing lineSensorMsgr')
                        lineSensorMsgr.close()
                        print('Sockets Closed')
                        sys.exit(0)
                        os._exit(0)

                if DEBUG_APP:
                    # Drawing code
                    screen.fill(BLACK)
                    textPrint.reset()

                    # Get count of joysticks
                    joystick_count = pygame.joystick.get_count()

                    textPrint.print(screen, "Number of joysticks: {}".format(joystick_count) )
                    textPrint.indent()

                    # For each joystick:
                    for i in range(joystick_count):
                        joystick = pygame.joystick.Joystick(i)
                        joystick.init()

                        textPrint.print(screen, "Joystick {}".format(i) )
                        textPrint.indent()

                        # Get the name from the OS for the controller/joystick
                        name = joystick.get_name()
                        textPrint.print(screen, "Joystick name: {}".format(name) )

                        # Usually axis run in pairs, up/down for one, and left/right for the other.
                        axes = joystick.get_numaxes()
                        textPrint.print(screen, "Number of axes: {}".format(axes) )
                        textPrint.indent()

                        for i in range( axes ):
                            axis = joystick.get_axis( i )
                            textPrint.print(screen, "Axis {} value: {:>6.3f}".format(i, axis) )
                        textPrint.unindent()

                        buttons = joystick.get_numbuttons()
                        textPrint.print(screen, "Number of buttons: {}".format(buttons) )
                        textPrint.indent()

                        for i in range( buttons ):
                            button = joystick.get_button( i )
                            textPrint.print(screen, "Button {:>2} value: {}".format(i,button) )
                        textPrint.unindent()

                        # Hat switch. All or nothing for direction, not like joysticks.
                        # Value comes back in a tuple.
                        hats = joystick.get_numhats()
                        textPrint.print(screen, "Number of hats: {}".format(hats) )
                        textPrint.indent()

                        for i in range( hats ):
                            hat = joystick.get_hat( i )
                            textPrint.print(screen, "Hat {} value: {}".format(i, str(hat)) )
                        textPrint.unindent()

                        textPrint.unindent()
                if car.Status == CarState.WAITING:
                    #show_user_ranking()
                    show_title_screen(car)
                elif car.Status == CarState.READY or car.Status == CarState.RUNNING:
                    if car.Status == CarState.READY and DEBUG_APP == False:
                        show_title_screen(car)
                        if first_run:
                            first_run = False
                            file = os.path.join("music", "1.mp3")
                            pygame.mixer.init()
                            pygame.mixer.music.load(file)
                            pygame.mixer.music.play()

                    name = my_controller.joystick.get_name()
                    speed = my_controller.joystick.get_axis(2)
                    steering = my_controller.joystick.get_axis(0)
                    networkup = my_controller.joystick.get_button(6)
                    networkdown = my_controller.joystick.get_button(7)
                    forwardpaddle = my_controller.joystick.get_button(4)
                    backwardpaddle = my_controller.joystick.get_button(5)

                    if "G29" in name:
                        speed = my_controller.joystick.get_axis(2)
                        steering = my_controller.joystick.get_axis(0)
                        networkup = my_controller.joystick.get_button(19)
                        networkdown = my_controller.joystick.get_button(20)
                        forwardpaddle = my_controller.joystick.get_button(4)
                        backwardpaddle = my_controller.joystick.get_button(5)
                    elif "G25" in name:
                        speed = my_controller.joystick.get_axis(2)
                        steering = my_controller.joystick.get_axis(0)
                        networkup = my_controller.joystick.get_button(6)
                        networkdown = my_controller.joystick.get_button(7)
                        forwardpaddle = my_controller.joystick.get_button(4)
                        backwardpaddle = my_controller.joystick.get_button(5)

                    if networklatency != car.NetDelay:
                        networklatency = car.NetDelay
                        cmd = 'network=' + str(CarState.NETWORK_RATES[car.Laps])
                        print("Sending command:" + cmd)
                        carControllerMsgr.send(cmd)

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
                        carControllerMsgr.send(cmd)
                        stopped = False
                    elif speed > -.01 and stopped == False:
                        stopped = True
                        carControllerMsgr.send('stop')

                    if current_steering != steering:
                        current_steering = steering
                        if steering > 0.1:
                            cmd = 'offset=+' + str(int(steering * 70.0))
                            print("Offset", " steering to", cmd)
                            carControllerMsgr.send(cmd)
                        elif steering < 0.1:
                            cmd = 'offset=' + str(int(steering * 70.0))
                            print("Offset", " steering to", cmd)
                            carControllerMsgr.send(cmd)
                        else:
                            carControllerMsgr.send('home')
                    
                    if networkup == 0:
                        network_can_go_up = True
                    
                    if networkdown == 0:
                        network_can_go_down = True

                    if networkup == 1 and network_can_go_up:
                        network_can_go_up = False
                        networklatency = networklatency + 10
                        cmd = 'network=' + str(networklatency)
                        carControllerMsgr.send(cmd)
                    elif networkdown == 1 and network_can_go_down:
                        network_can_go_down = False
                        if networklatency > 0:
                            networklatency = networklatency - 10

                        cmd = 'network=' + str(networklatency)
                        carControllerMsgr.send(cmd)

                    if forwardpaddle == 1:
                        direction = FORWARD
                    elif backwardpaddle == 1:
                        direction = BACKWARD

                elif car.Status == CarState.FINISHED:
                    print("Car FINISHED, Stopping car")
                    carControllerMsgr.send('stop')
                    cmd = 'offset=0'
                    carControllerMsgr.send(cmd)
                    print("Setting car.Status=CarState.SHOWING_SCORE")
                    car.Status = CarState.SHOWING_SCORE
                    print("Car Status:", car.Status)
                elif car.Status == CarState.SHOWING_SCORE:
                    pass
                elif car.Status == CarState.KILLING_CONTROLLER:
                    print("Killing controller")
                    break
                
                # Go ahead and update the screen with what we've drawn.
                pygame.display.flip()
                clock.tick(REFRESH_RATE)

            car.Status = CarState.RESTART
            print("Exiting controller")

    except (KeyboardInterrupt, SystemExit):
        t.join()
        print('closing lineSensorMsgr')
        lineSensorMsgr.close()
        print('closing carControllerMsgr')
        carControllerMsgr.close()
        print('Sockets Closed')
        sys.exit(0)
        os._exit(0)
    
if __name__ == '__main__':
    main()