# AutoCarApp
Introduction:
	This is based on the Sunfounder Raspberry Pi smart video car client but updating to support the xbox360controller and hopefully a steering wheel via pygame for cross-platform support. Currently supports a Logitec G29 Steering Wheel

	Also need to install the xbox360 controller driver if using the xbox 360 remote. Testing was done on the Logitech F310.
	https://www.microsoft.com/accessories/en-gb/d/xbox-360-controller-for-windows

	Open Terminal Window to Connect to Car or use Putty on Windows:
		![Alt text](http://iptvwams-cdn.att.net/AutoCarApp/CarInstall.jpg?raw=true "Title")

	In GitBash (https://gitforwindows.org/) for Python3 (tested on 3.6.3):
		Start a new gitbash terminal and install the following dependencies:
		pip install pygame
		pip install beautifultable
		pip install requests

		Computer:~ name$ git clone https://github.com/bryanpdavis/AutoCarApp.git
		cd /AutoCar/controller/
		sudo python3 client_AppSteeringWheel.py
	
	1.) Put the car on the line which activates the gas pedal and steering wheel. 
	2.) Car runs through 4 rounds at [50,100,200,50] ms connection delay.
	3.) Car will stop at the end of the round to show the score. (Score screen is stilling being worked on.)
	4.) Press x on the game pad, to end the score screen and restart the test screen.
	5.) Rinse and repeat

	Car:
		It is based on the Sunfounder Raspberry Pi Smart Video Car Kit, being modified to support commands to move
		the servos based on the movement of the left stick and trigger of an xbox360 controller using the xbox360controller
		driver.

	Controller:
		It is based on Python3 and pygame and using the xbox360Controller driver to control the car over IP.
