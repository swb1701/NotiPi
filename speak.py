#
# Simple Command Line Speak Routine
# Scott Bennett, 5/17
#

import boto3
import sys
import os
import json
import time

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
    os.system("/usr/bin/mpg123 -q notify.mp3")

speak(str(sys.argv[1]))
