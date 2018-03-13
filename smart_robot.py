# -*- coding: utf-8 -*-
"""
A temple for a smart robot

"""
import threading as Thrd
import RPi.GPIO as gpio
import time
from PIL import Image
import sys
import thread
import requests
import os  # file io
import picamera
from time import sleep
import base64
import io

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(20, gpio.OUT) #set pin 20 to output

pre_angle = 0
new_angle= 30            #turn 30 degree each time when pi does not detect a human body.



def Servo_Init(GPIO_Pins):
    gpio.setwarnings(False)
    # initialize BCM pin
    gpio.setmode(gpio.BCM)
    # set the pwm period

    # set mode of servo control pins
    gpio.setup(GPIO_Pins, gpio.OUT)
    return gpio.PWM(GPIO_Pins, 50)


def Servo_Begin(s):
    s.start(0)


def angleToDutyCycle(angle):
    time = float((2 * angle * 100) / 180) + 50
    return time / 20


def Servo_control(pre_angle, servo_num, angle, rotate_speed):

    DutyCycle = angleToDutyCycle(angle)
    Pre_DutyCycle = angleToDutyCycle(pre_angle)
    i = DutyCycle - Pre_DutyCycle
    if i > 0:
        while i > 0:
            servo_num.ChangeDutyCycle(DutyCycle - i)
            i -= 0.1
            time.sleep(rotate_speed)
    elif i < 0:
        while i < 0:
            servo_num.ChangeDutyCycle(DutyCycle - i)
            i += 0.1
            time.sleep(rotate_speed)

def Servo_Update(loop_times, Servo_Pin, angle ,speed):
    global pre_angle
    for t in range (loop_times):
        Servo_control(pre_angle, Servo_Pin, angle, speed)
        pre_angle = angle


def http_post(url, stream):
    global new_angle
    print("In http_post")
    img = stream.read()          #read directly from the stream.
    img = base64.b64encode(img)

    r = requests.post("{}:5000/get_state".format(url), data={   # post the request.
        'current': img
    })

    json_response = r.json()
    print(json_response)
    on_seat = json_response["on_seat"]    #key_val for if human is on-seat
    stop = json_response["stop"]          #key_val for if timer is stopped by the website.
    if on_seat is not True:
        #update value of new_angle here
        if new_angle >= 150:              #if on_seat is FALSE, then turn the camera 30 degree each time to seek the user.
            new_angle = 60
            time.sleep(0.5)


    return on_seat, stop


def Servo_Thread():
    global pre_angle
    global  new_angle
    # initialize GPIO pins
    Pin_list = 19
    Servo_pin = Servo_Init(Pin_list)
    Servo_Begin(Servo_pin)
    pre_angle = 0
    while True:
        Servo_control(pre_angle,Servo_pin,new_angle,0.04)
        pre_angle=new_angle




if __name__=="__main__":

        thread.start_new_thread(Servo_Thread,())

        # initialize camera
        reminder = 3 # second.
        camera = picamera.PiCamera()
        camera.resolution = (640, 480)
        camera.rotation = 180
        camera.start_preview()
        sleep(2)  #load the camera
        stream = io.BytesIO()              #enable stream.

        while True:
            camera.capture(stream, 'png')  #caputer in stream.
            stream.seek(0)
            on_seat, stop = http_post("http://192.168.43.244", stream)  #ip may change.
            stream.seek(0)

            
            print(stop,reminder)  # print each post.

            if reminder > 0:
                if stop:
                    reminder = 3 #reset
                elif not on_seat:
                    reminder = 3
                else:
                    reminder -= 1
            else:
                #make noise- beep three times when the timer count down to zero.                
                for j in range (3):
                    gpio.output(20, gpio.HIGH)
                    sleep(1)
                    gpio.output(20, gpio.LOW)
                    sleep(1)
                reminder = 3  #reset
                pass

            sleep(1)

        #camera.stop_preview()





    #except Exception as e:
        #print("wrong path")
        #pass
