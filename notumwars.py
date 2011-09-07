#!/usr/bin/python
# -*- coding: utf-8 -*-


import datetime
import oauth
import oauthtwitter
import re
import sys
import threading
import yaml

from aochat import Chat, ChatError, AOSP_CHANNEL_MESSAGE


class Worker(threading.Thread):
    """
    Thread worker.
    """
    
    SIDE = [
        "neutral",
        "clan",
        "omni",
    ]
    
    def __init__(self, username, password, host, port, character, tag, twitter):
        threading.Thread.__init__(self)
        
        self.username  = username
        self.password  = password
        self.host      = host
        self.port      = port
        self.character = character
        self.tag       = tag
        self.twitter   = twitter
    
    def run(self):
        while True:
            try:
                chat = Chat(self.username, self.password, self.host, self.port)
                
                for character in chat.characters:
                    if character.name == self.character:
                        break
                else:
                    self.log("Unknown character: %s" % self.character)
                    break
                
                chat.login(character.id)
                chat.start(self.callback)
            except SystemExit:
                break
            except Exception, error:
                self.log(error, sys.stderr)
                continue
    
    def callback(self, chat, packet):
        # Log incoming packets
        self.log(repr(packet))
        
        # Check packet type
        if packet.type != AOSP_CHANNEL_MESSAGE.type:
            return
        
        # "All Towers" channel
        if (
            packet.channel_id == 42949672960 and
            packet.category   == 506 and
            packet.instance   == 12753364
        ):
            # Xxx (omni) vs. Yyy (clan), Area (100,500), #RKx
            message = "%s (%s) vs. %s (%s), %s (%d,%d)" % (
                packet.args[1],                                                 # Attacker's organization/clan name
                self.SIDE[packet.args[0][1]],                                   # Attacker's side
                packet.args[4],                                                 # Defender's organization/clan name
                self.SIDE[packet.args[3][1]],                                   # Defender's side
                packet.args[5],                                                 # Area
                packet.args[6],                                                 # Area position X
                packet.args[7],                                                 # Area position Y
            )
        # "Tower Battle Outcome" channel
        elif packet.channel_id == 42949672962:
            match = re.search(r"^The (\S+) organization (.+?) attacked the (\S+) (.+?) at their base in (.+?)\.", packet.message)
            
            if match:
                # Xxx (omni) won! Yyy (clan) lost Area
                message = "%s (%s) won! %s (%s) lost %s" % (
                    match.group(2),                                             # Winner's name
                    match.group(1).lower(),                                     # Winner's side
                    match.group(4),                                             # Loser's name
                    match.group(3).lower(),                                     # Loser's side
                    match.group(5),                                             # Area
                )
            else:
                return
        # Other channel
        else:
            return
        
        # Post to Twitter
        try:
            self.twitter.PostUpdate(message + (", #%s" % self.tag))
        except Exception, error:
            self.log(error, sys.stderr)
        
        # Log message
        self.log(message)
    
    def log(self, message, fd = sys.stdout):
        print >> fd, "[%s] %s: %s" % (datetime.datetime.today().strftime("%F %T %s"), self.tag, message,)


def main(argv = []):
    """
    Launcher.
    """
    
    # Read settings
    config = yaml.load(file("/usr/local/etc/notumwars.conf", "rb"))
    
    # Init Twitter API
    access_token = oauth.oauth.OAuthToken(config["twitter"]["access_token_key"], config["twitter"]["access_token_secret"])
    twitter      = oauthtwitter.OAuthApi(config["twitter"]["consumer_key"], config["twitter"]["consumer_secret"], access_token)
    
    # Start workers
    workers = []
    
    for dimension in config["ao"]["dimensions"]:
        worker = Worker(
            username  = config["ao"]["username"],
            password  = config["ao"]["password"],
            host      = dimension["host"],
            port      = dimension["port"],
            character = dimension["character"],
            tag       = dimension["tag"],
            twitter   = twitter,
        )
        
        worker.start()
        workers.append(worker)
    
    for worker in workers:
        worker.join()
    
    return 0


if __name__ == "__main__":
    status = main(sys.argv[1:])
    sys.exit(status)
