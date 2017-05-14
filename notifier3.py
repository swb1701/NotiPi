#
# Simple Alexa Spoken Notification Demo (Variant to Use HTTPS Request from Notify Server)
# Scott Bennett, 5/17
#

import boto3
import pygame as pg
import sys
import os
import json
import time
import urllib2

import secrets as s #import our keys and such

#set up an AWS session
uesess = boto3.Session(
        aws_access_key_id=s.AWS_ACCESS_KEY,
        aws_secret_access_key=s.AWS_SECRET_KEY,
        region_name=s.AWS_REGION
)

polly=uesess.client('polly') #for our speech synthesis

#speak some text (on Alexa)
def speak(text):
    resp=polly.synthesize_speech(OutputFormat='mp3',Text=text,VoiceId='Salli')
    mp3file=open('notify.mp3','w')
    mp3file.write(resp['AudioStream'].read())
    mp3file.close()
    play("notify.mp3")

def play(filename):
    clock=pg.time.Clock()
    pg.mixer.music.load(filename)
    pg.mixer.music.play()
    while pg.mixer.music.get_busy():
        clock.tick(30)

freq = 44100    # audio CD quality
bitsize = -16   # unsigned 16 bit
channels = 2    # 1 is mono, 2 is stereo
buffer = 2048   # number of samples (experiment to get right sound)
pg.mixer.init(freq, bitsize, channels, buffer)
# optional volume 0 to 1.0
pg.mixer.music.set_volume(1.0)
speak("Welcome to Noti Pi -- listening for commands")
#our main control loop
running=True
while running:
    #get messages containing JSON from the Notify server (see https://github.com/swb1701/Notify)
    resp=urllib2.urlopen(s.NOTIFY_URL)
    msg=resp.read()
    try:
        #parse the json of the message
        try:
            cmd=json.loads(msg) #illustrating use of json for more complex commands
            #get the command
            c=cmd['cmd']
            #handle the command
            if 'volume' in cmd:
                pg.mixer.music.set_volume(float(cmd['volume']))
            if 'alarm' in cmd:
                play('alarms/'+cmd['alarm'])
            if c=='speak':
                speak(cmd['text'])
            elif c=='update':
                speak("Updating software")
                time.sleep(5)
                running=False
        except:
            speak(msg) #if not in json, just speak it
    except:
        None
