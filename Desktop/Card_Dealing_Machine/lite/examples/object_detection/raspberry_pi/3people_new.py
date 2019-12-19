#!/usr/bin/env python
import time
import RPi.GPIO as GPIO

##Declare the GPIO settings
GPIO.setmode(GPIO.BCM)

##set up GPIO pins

MONITOR_PIN = 18
GPIO.setup(MONITOR_PIN,GPIO.IN)

##################################
## top motor
GPIO.setup(4, GPIO.OUT)
# Connected to PWMA pin7

GPIO.setup(17, GPIO.OUT)
# Connected to AIN2 pin11

GPIO.setup(22, GPIO.OUT)
# Connected to AIN1 pin15

GPIO.setup(27, GPIO.OUT)
# Connected to STBY pin13

##################################

##################################
## down motor
GPIO.setup(5, GPIO.OUT)
# Connected to BIN1 pin29

GPIO.setup(6, GPIO.OUT)
# Connected to BIN2 pin31

GPIO.setup(13, GPIO.OUT)
# Connected to PWMB pin33

##################################
##################################
##Drive the top motor clockwise
##  no card  --> input_state = 1
## have card --> input_state = 0

def TurnOnTopMotor():
    GPIO.output(22, GPIO.HIGH) # AIN1
    GPIO.output(17, GPIO.LOW)  # AIN2
    GPIO.output(4, GPIO.HIGH)  # PWMA
    GPIO.output(27, GPIO.HIGH) # STBY

def TurnOffTopMotor():
    # top motor
    GPIO.output(22, GPIO.LOW)  # AIN1
    GPIO.output(17, GPIO.LOW)  # AIN2
    GPIO.output(4, GPIO.LOW)   # PWMA
    GPIO.output(27, GPIO.HIGH) # STBY

def TurnOnBotMotor():
    # down motor
    GPIO.output(5, GPIO.HIGH)  # BIN1
    GPIO.output(6, GPIO.LOW)   # BIN2
    GPIO.output(13, GPIO.HIGH) # PWMB
    GPIO.output(27, GPIO.HIGH) # STBY

def TurnOffBotMotor():
    # down motor
    GPIO.output(5, GPIO.LOW)   # BIN1
    GPIO.output(6, GPIO.LOW)   # BIN2
    GPIO.output(13, GPIO.LOW)  # PWMB
    GPIO.output(27, GPIO.HIGH) # STBY

top_motor = 1
down_motor = 0
card_R = 52

try:
    while True:
        input_state = GPIO.input(MONITOR_PIN)
        #print(input_state)
        if card_R > 0:
            if input_state == 1 and top_motor == 1 and down_motor == 0 :
                TurnOffBotMotor()
                TurnOffTopMotor()
                print "top motor"
                TurnOnTopMotor()
                while GPIO.input(MONITOR_PIN) == 1:
                    print "while"
                TurnOffTopMotor()
                print(input_state)
                card_R -= 1
                top_motor = 0
                down_motor = 1
            elif input_state == 0:
                #TurnOffTopMotor();
                TurnOnBotMotor();
                print "down motor"
                time.sleep(0.72)
                TurnOffBotMotor()
                top_motor = 1
                down_motor = 0
        else:
            break
###################################

except KeyboardInterrupt:
    print('shut down')
finally:
    GPIO.cleanup()

