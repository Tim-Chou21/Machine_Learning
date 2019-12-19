# python3
#
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#!/usr/bin/env python

"""Example using TF Lite to detect objects with the Raspberry Pi camera."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import RPi.GPIO as GPIO
import argparse
import io
import re
import time
#import py_qmc5883l

from annotation import Annotator

import numpy as np
import picamera

from PIL import Image
from tflite_runtime.interpreter import Interpreter

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

top_motor = 1
down_motor = 0
card_R = 52
location = 0

#######################################
#sensor = py_qmc5883l.QMC5883L()
#position = [[0 for i in range(2)] for j in range(4)]
position = [[0,0], [0,0], [0,0], [0,0]]
direction = []
direction_count = 0
lastDirection = -3
#######################################
#######################################
##Declare the GPIO settings
GPIO.setmode(GPIO.BCM)

##set up GPIO pins

MONITOR_PIN = 18
GPIO.setup(MONITOR_PIN,GPIO.IN)
input_state = 1
##################################
## top motor
GPIO.setup(4, GPIO.OUT)
# Connected to PWMA pin7

GPIO.setup(17, GPIO.OUT)
# Connected to AIN1 pin11

GPIO.setup(22, GPIO.OUT)
# Connected to AIN2 pin12

GPIO.setup(27, GPIO.OUT)
# Connected to STBY pin13

##################################

##################################
## down motor
GPIO.setup(5, GPIO.OUT)
# Connected to BIN1 pin7

GPIO.setup(6, GPIO.OUT)
# Connected to BIN2 pin11

GPIO.setup(13, GPIO.OUT)
# Connected to PWMB pin12

####################################
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

'''
def getHeading():
    global location;
    m = sensor.get_magnet()
    if location==0:
        position[location][0] = m[0]
        position[location][1] = m[1]
    else:
        if (abs(m[0]-position[location-1][0]) > 1500 and abs(m[1]-position[location-1][1])) > 1500:
            position[location][0] = m[0]
            position[location][1] = m[1]
        else:
            location = location - 1
    
    
    print(position)
    #print(index)

def dealing(index):
    global card_R, location, input_state;
    TurnOnBotMotor()
    TurnOffTopMotor()
    m = sensor.get_magnet()
    if  (abs(m[0] - position[index][0])) < 1200 and (abs(m[1] - position[index][1])) < 1200:
        TurnOffBotMotor()
        time.sleep(2)
        TurnOnTopMotor()
        if input_state==0:
            TurnOffTopMotor()
            #time.sleep(0.1)
#time.sleep(0.116)
#       TurnOffTopMotor()
        card_R = card_R - 1
        location = location + 1
        if location > 3:
            location = 0
        time.sleep(0.3)
'''

def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels


def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor


def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  global location,lastDirection
  
  set_input_tensor(interpreter, image)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i]
      }
      
      if result['class_id'] == 76 and result['bounding_box'][1] > 0.2 and result['bounding_box'][1] < 0.6:
          results.append(result)
          if direction_count - lastDirection >= 2 :
              direction.append(direction_count*0.052125)
              print(direction_count)
              lastDirection = direction_count
              if location < 4:
              #getHeading()
                  location = location + 1
  time.sleep(1)
  return results


def annotate_objects(annotator, results, labels):
  """Draws the bounding box and label for each object in the results."""
  for obj in results:
    # Convert the bounding box figures from relative coordinates
    # to absolute coordinates based on the original resolution
    ymin, xmin, ymax, xmax = obj['bounding_box']
    xmin = int(xmin * CAMERA_WIDTH)
    xmax = int(xmax * CAMERA_WIDTH)
    ymin = int(ymin * CAMERA_HEIGHT)
    ymax = int(ymax * CAMERA_HEIGHT)

    # Overlay the box, label, and score on the camera preview
    annotator.bounding_box([xmin, ymin, xmax, ymax])
    annotator.text([xmin, ymin],
                   '%s\n%.2f' % (labels[obj['class_id']], obj['score']))


def main():
  global location, card_R, input_state, direction_count
  clock = 0;
  TurnOffTopMotor()
  TurnOffBotMotor()
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model', help='File path of .tflite file.', required=True)
  parser.add_argument(
      '--labels', help='File path of labels file.', required=True)
  parser.add_argument(
      '--threshold',
      help='Score threshold for detected objects.',
      required=False,
      type=float,
      default=0.4)
  args = parser.parse_args()

  labels = load_labels(args.labels)
  interpreter = Interpreter(args.model)
  interpreter.allocate_tensors()
  _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
  with picamera.PiCamera(
      resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30) as camera:
    camera.start_preview()
    try:
      stream = io.BytesIO()
      annotator = Annotator(camera)
      for _ in camera.capture_continuous(
          stream, format='jpeg', use_video_port=True):
        if clock % 2 == 0:
            TurnOnBotMotor()
            time.sleep(0.052125)
            TurnOffBotMotor()
            direction_count += 1
        stream.seek(0)
        image = Image.open(stream).convert('RGB').resize(
            (input_width, input_height), Image.ANTIALIAS)
        start_time = time.monotonic()
        results = detect_objects(interpreter, image, args.threshold)

        elapsed_ms = (time.monotonic() - start_time) * 1000
        annotator.clear()
        annotate_objects(annotator, results, labels)
        annotator.text([5, 0], '%.1fms' % (elapsed_ms))
        annotator.update()
        stream.seek(0)
        stream.truncate()
        clock = clock + 1
        if location > 3:
            location = 3
            tmp = direction[0]
            direction[0] = direction[1] - direction[0]
            direction[1] = direction[2] - direction[1]
            direction[2] = direction[3] - direction[2]
            direction[3] = tmp + 0.834 - direction[3]
            print(tmp , direction[0], direction[1], direction[2], direction[3])
            while True:
                #input_state = GPIO.input(MONITOR_PIN)
                if card_R > 0 :
                    TurnOnBotMotor()
                    #m =sensor.get_magnet()
                    time.sleep(direction[location])
                    if card_R==52 :
                        time.sleep(tmp)
                        #if  (m[0] - position[location][0]) < 600 and (m[1] - position[location][1]) < 600:
                    TurnOffBotMotor()
                    time.sleep(0.5)
                    TurnOnTopMotor()
                    while GPIO.input(MONITOR_PIN) == 1 :
                        print(tmp , direction[0], direction[1], direction[2], direction[3])
                    TurnOffTopMotor()
                    time.sleep(0.5)
                    card_R -= 1
                    location += 1
                    if location > 3:
                        location = 0
                else: break
    finally:
      camera.stop_preview()
      GPIO.cleanup()


if __name__ == '__main__':
  main()
