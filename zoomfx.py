#!/usr/bin/python3
#
# Process to detect GPIO pin changes and interact with Zoom Multistomp MS-50G
#

import mido
from time import sleep
import RPi.GPIO as GPIO
from time import sleep
import os

Inport = None
Outport = None
GPIOPWRDN = 17
GPIOPREV = 23
GPIONEXT = 24
DEVICE_ID = 0x58 # 0x58=MS-50G , 0x61=MS-70CDR, 0x5F=MS-60B

def setupGPIO():
    global GPIOPREV
    global GPIONEXT

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIOPWRDN, GPIO.IN)
    GPIO.setup(GPIOPREV, GPIO.IN)
    GPIO.setup(GPIONEXT, GPIO.IN)


def connectToZoom():
    midiname = "ZOOM MS Series"
    global Inport
    global Outport

    for port in mido.get_input_names():
        print("Checking:", port)
        if port[:len(midiname)]==midiname:
            Inport = mido.open_input(port)
            print("Using Input:", port)
            break

    for port in mido.get_output_names():
        print("Checking:",port)
        if port[:len(midiname)]==midiname:
            Outport = mido.open_output(port)
            print("Using Output:", port)
            break

    if Inport == None or Outport == None:
        print("Unable to find Pedal")


def zoomParameterEditEnable():
    global Inport
    global Outport
    global DEVICE_ID

    #Identity Request
    msg = mido.Message("sysex", data = [0x7e,0x00,0x06,0x01])
    Outport.send(msg); sleep(0); msg = Inport.receive()
    print("msg:",msg.hex())

    # Parameter Edit Enable
    msg = mido.Message("sysex", data = [0x52,0x00,DEVICE_ID,0x50])
    Outport.send(msg); sleep(0);
    print("sent edit enable")


def getCurrentPatch():
    global Inport
    global Outport
    global DEVICE_ID

    currentPatch = 0
    zoomParameterEditEnable()
    # Request Current Program
    msg = mido.Message("sysex", data = [0x52,0x00,DEVICE_ID,0x33])
    Outport.send(msg)
    while True:
        msg = Inport.receive()
        print("msg:",msg.hex())
        if msg.bytes()[0] == 192:
            currentPatch = msg.bytes()[1]
            print("Current Patch is:",currentPatch)
            break;
    zoomParameterEditDisable()

    return currentPatch


def zoomParameterEditDisable():
    global Outport
    global DEVICE_ID

    # Parameter Edit Disable
    msg = mido.Message("sysex", data = [0x52,0x00,DEVICE_ID,0x51])
    Outport.send(msg); sleep(0);
    print("sent edit disable")


def changePatch(dir):
    global Outport

    # Get the current patch
    currentPatch = getCurrentPatch()

    # Adjust patch and wrap around min/max
    currentPatch=currentPatch+dir
    if currentPatch >49 :
        currentPatch=0
    if currentPatch<0:
        currentPatch=49
    print("Changing to Patch:",currentPatch)

    zoomParameterEditEnable()
  
    print("Changing patch")
    msg = mido.Message.from_bytes([0xc0, currentPatch])
    Outport.send(msg);

    zoomParameterEditDisable()


def main():
    global GPIOPWRDN
    global GPIOPREV
    global GPIONEXT

    # Setp up Zoom and get Current Patch
    connectToZoom()

    # Setup buttons and loop for presses
    setupGPIO()
    try:
        while True:
            if GPIO.input(GPIOPWRDN):
                print("Power Down Button Pressed")
                os.system("shutdown -h now")
            if GPIO.input(GPIOPREV):
                print("Previous Button Pressed")
                changePatch(-1)
                sleep(0.5)
            if GPIO.input(GPIONEXT):
                print("Next Button Pressed")
                changePatch(1)
                sleep(0.5)

            sleep(0.1)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
