#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib2 import urlopen,Request,build_opener,HTTPCookieProcessor,install_opener
from urllib import urlencode
from cookielib import LWPCookieJar
from HTMLParser import HTMLParser
from twython import Twython
from threading import Thread
from getpass import getpass

import os
import serial
import time
import uuid

TWITTER_CONSUMER_KEY = "XXXXXXXX"
TWITTER_CONSUMER_SECRET = "XXXXXXX"

SERIAL_PORT = "/dev/cu.usbmodem1421"
SERIAL_BAUD_RATE = 9600

TIME_INTERVAL = 60 #1 minute

class SerialMessageThread(Thread):

    isEnd = False

    def __init__(self, thisSerial, thisTwitter):
        super(SerialMessageThread, self).__init__()
        self.thisSerial = thisSerial
        self.thisTwitter = thisTwitter

    def run(self):
        while True:
            if SerialMessageThread.isEnd:
                break
            dt = self.thisSerial.readline()
            strMessage = "The current temperature is: %s°C. Message ID: %s. View code at: %s" % (dt.strip(), str(uuid.uuid4()).split('-')[0], "https://github.com/six519/TempTwitter")
            self.thisTwitter.update_status(status=strMessage)
            print "Message posted to twitter!!!"
            time.sleep(1)

class Twitter_Temperature(HTMLParser):

    def __init__(self, consumerKey, consumerSecret, twitterUsername, twitterPassword):
        HTMLParser.__init__(self)
        self.consumerKey = consumerKey
        self.consumerSecret = consumerSecret
        self.twitterUsername = twitterUsername
        self.twitterPassword = twitterPassword
        self.twitter = None
        self.jarName = 'cookie.jar'
        self.tokens = {}
        self.getPinCode = False
        self.pinCode = ""
        self.serial = None
    
    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            if self.cnt == 0:
                self.tokens['authenticity_token'] = attrs[2][1]
                self.cnt += 1

        if tag == 'code':
            self.getPinCode = True

    def handle_data(self, data):
        if self.getPinCode:
            self.getPinCode = False
            self.pinCode = data
    
    def resetData(self):
        try:
            os.remove(self.jarName)
        except OSError:
            pass
        self.tokens = {}
        self.cnt = 0
        
    def run(self):
        self.resetData()
        self.twitter = Twython(self.consumerKey, self.consumerSecret)
        auth_props = self.twitter.get_authentication_tokens()

        self.tokens['oauth_token'] = auth_props['oauth_token']

        cookie = self.jarName
        cookieJar = LWPCookieJar()
        opener = build_opener(HTTPCookieProcessor(cookieJar))
        install_opener(opener)
    
        f = urlopen(auth_props['auth_url'])
        cookieJar.save(cookie)
        self.feed(f.read().decode('utf-8','replace'))
        self.close()
        f.close()
    
        post = {"session[username_or_email]":self.twitterUsername,"session[password]":self.twitterPassword}
        post.update(self.tokens)
        data = urlencode(post)
    
        cookieJar.load(cookie)
        f = urlopen("https://twitter.com/oauth/authenticate",data)
        #print f.read()
        self.feed(f.read().decode('utf-8','replace'))
        self.close()
        f.close()

        self.twitter = Twython(self.consumerKey, self.consumerSecret, auth_props['oauth_token'], auth_props['oauth_token_secret'])

        authorized_tokens = self.twitter.get_authorized_tokens(self.pinCode)
        self.twitter = Twython(self.consumerKey, self.consumerSecret, authorized_tokens['oauth_token'], authorized_tokens['oauth_token_secret'])

        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE)
        smThread = SerialMessageThread(ser, self.twitter)
        smThread.start()
        self.resetData()

        while True:
            if SerialMessageThread.isEnd:
                break
            ser.write("GET_TEMPERATURE")
            time.sleep(TIME_INTERVAL)

if __name__ == "__main__":
    tuser = raw_input("Please enter your Twitter username: ").strip()
    tpass = getpass("Please enter your Twitter password: ").strip()
    
    tt = Twitter_Temperature(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, tuser, tpass)

    try:
        tt.run()
    except KeyboardInterrupt:
        SerialMessageThread.isEnd = True
        print "Application terminated..."