import xbox360_controller
import time
import string
from pygame_functions import *

def show_initials_prompt():
    selector = makeTextBox(10,80,300,2, "Enter text here", 3, 24)
    showTextBox(selector)
    entry = textBoxInput(selector)
    while len(entry) < 3:
        waitPress()
        
    while True:
        waitPress()
        if(keyPressed("return")):
            return entry