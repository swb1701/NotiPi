#
# Simple Alexa Spoken Notification Demo (Variant Using Pygame for Continuous Audio and Volume Control)
# PyGame Version
# Scott Bennett, 5/17
#

import boto3
import pygame as pg
import sys
import os
import json
import time
import datetime

import secrets as s #import our keys and such

#set up an AWS session
uesess = boto3.Session(
        aws_access_key_id=s.AWS_ACCESS_KEY,
        aws_secret_access_key=s.AWS_SECRET_KEY,
        region_name=s.AWS_REGION
)

polly=uesess.client('polly') #for our speech synthesis
sqs=uesess.client('sqs') #for receiving commands

#speak some text (on Alexa)
def speak(text,voice='Salli'):
    resp=polly.synthesize_speech(OutputFormat='mp3',TextType='ssml',Text='<prosody volume="x-loud">'+text+'</prosody>',VoiceId=voice)
    mp3file=open('notify.mp3','w')
    mp3file.write(resp['AudioStream'].read())
    mp3file.close()
    play("notify.mp3")

def play(filename):
    if in_between(datetime.datetime.now().time(),quietstart,quietstop):
        return
    clock=pg.time.Clock()
    pg.mixer.music.load(filename)
    pg.mixer.music.play()
    while pg.mixer.music.get_busy():
        clock.tick(30)
        
def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end        

quietstart = datetime.time(0,15)
quietstop = datetime.time(6)
freq = 44100    # audio CD quality
bitsize = -16   # unsigned 16 bit
channels = 2    # 1 is mono, 2 is stereo
buffer = 2048   # number of samples (experiment to get right sound)
pg.mixer.init(freq, bitsize, channels, buffer)
# optional volume 0 to 1.0
pg.mixer.music.set_volume(1.0)
speak("Welcome to Noti Pi -- listening for commands")
#set the queue we get commands from
queue=s.SQS_QUEUE
#our main control loop
running=True
while running:
    #get messages containing JSON from SQS (20 second long poll)
    resp=sqs.receive_message(QueueUrl=queue,WaitTimeSeconds=20)
    print(resp)
    if 'Messages' in resp:
        for msg in resp['Messages']:
            try:
                #parse the json of the message
                try:
                    cmd=json.loads(msg['Body']) #illustrating use of json for more complex commands
                    #get the command
                    c=cmd['cmd']
                    #handle the command
                    if 'volume' in cmd:
                        pg.mixer.music.set_volume(float(cmd['volume']))
                    if 'alarm' in cmd:
                        play('alarms/'+cmd['alarm'])
                    if c=='speak':
                        if 'voice' in cmd:
                                speak(cmd['text'],cmd['voice'])
                        else:
                                speak(cmd['text'])
                    elif c=='update':
                        speak("Updating software")
                        time.sleep(5)
                        running=False
                except:
                    speak(msg['Body']) #if not in json, just speak it
            except:
                None
            finally:
                #delete the message from the queue
                sqs.delete_message(QueueUrl=queue,ReceiptHandle=msg['ReceiptHandle'])
                
