#
# Simple Alexa Spoken Notification Demo (Variant to Use HTTPS Request from Notify Server Instead of Direct SQS Access)
# Added BTLE Device Scanning
# Scott Bennett, 5/17
#

import boto3
import pygame as pg
import sys
import os
import json
import time
import urllib
import urllib2
import datetime
import struct
import pexpect
import threading
from ctypes import (CDLL, get_errno)
from ctypes.util import find_library
from socket import (
    socket,
    AF_BLUETOOTH,
    SOCK_RAW,
    BTPROTO_HCI,
    SOL_HCI,
    HCI_FILTER,
)

import secrets as s #import our keys and such

def setup_bluetooth():
    #since the code I found doesn't guarantee a previous scan was shut down, use this hack to ensure it is
    p=pexpect.spawn('/usr/bin/bluetoothctl')
    p.sendline('scan on')
    time.sleep(5) #this delay is essential
    p.sendline('scan off')
    p.sendline('quit')
    p.close()
    btlib = find_library("bluetooth")
    bluez = CDLL(btlib, use_errno=True)
    dev_id = bluez.hci_get_route(None)
    sock.bind((dev_id,))
    err = bluez.hci_le_set_scan_parameters(sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000);
    if err < 0:
        raise Exception("Set scan parameters failed")
        # occurs when scanning is still enabled from previous call
    # allows LE advertising events
    hci_filter = struct.pack(
        "<IQH",
        0x00000010,
        0x4000000000000000,
        0
    )
    sock.setsockopt(SOL_HCI, HCI_FILTER, hci_filter)
    err = bluez.hci_le_set_scan_enable(
        sock.fileno(),
        1,  # 1 - turn on;  0 - turn off
        0, # 0-filtering disabled, 1-filter out duplicates
        1000  # timeout
    )

def signal_watchdog():
    os.system("touch /tmp/notifier-alive")

signal_watchdog()    
devmap={}
sock = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)
setup_bluetooth()
millis = lambda: int(round(time.time()*1000))
lock=threading.Lock()

def btle_listen():
    while True:
        data = sock.recv(1024)
        # print bluetooth address from LE Advert. packet
        addr = ':'.join("{0:02x}".format(ord(x)) for x in data[12:6:-1])
        rssi = (ord(data[-1]))
        with lock:
            try:
                dev=devmap[addr]
                dev['time']=millis()
                dev['rssi']=rssi
            except:
                dev={'time':millis(),'rssi':rssi,'addr':addr}
                devmap[addr]=dev
            #now=millis()
            #print("---------------------------")
            #for key in devmap:
            #    print(key+" "+str(devmap[key]['rssi'])+" "+str(now-devmap[key]['time']))

def btle_since(timestamp):
    result=[]
    with lock:
        for key in devmap:
            if (devmap[key]['time']>timestamp):
                result.append(devmap[key])
    return(result)

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
t=threading.Thread(target=btle_listen) #start btle listen
t.daemon=True
t.start()
poll=0
#our main control loop
running=True
errcnt=0
while running:
    try:
        errcnt=0
        #get messages containing JSON from the Notify server (see https://github.com/swb1701/Notify)
        btle_result=btle_since(poll)
        print(btle_result)
        poll=millis()
        data=urllib.urlencode({'token':s.NOTIFY_TOKEN,'key':s.NOTIFY_KEY,'btle':json.dumps(btle_result)})
        req=urllib2.Request(url=s.NOTIFY_BASE_URL,data=data)
        resp=urllib2.urlopen(req, timeout=60)
        msg=resp.read()
        signal_watchdog()    
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
                print("Updating software")
                time.sleep(5)
                running=False
        except:
            speak(msg) #if not in json, just speak it
    except Exception,e:
        print str(e)
        errcnt=errcnt+1
        if (errcnt>12):
            print("Consecutive error count exceeded, forcing client reload/restart")
            running=False
        time.sleep(10)
