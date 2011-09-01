#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import yaml
import threading
import oauth
import oauthtwitter

from aochat import Chat, ChatError, AOSP_CHANNEL_MESSAGE


class Worker(threading.Thread):
    """
    Thread worker.
    """
    
    sides = [
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
                chat.login(chat.characters[self.character].id)
                chat.start(self.callback)
            except ChatError:
                continue
            except SystemExit:
                break
    
    def callback(self, chat, packet):
        # Check packet
        if not (
            packet.type       == AOSP_CHANNEL_MESSAGE.type and  # Channel message
            packet.channel_id == 42949672960 and                # "All Towers" channel
            packet.category   == 506 and                        # Message category
            packet.instance   == 12753364                       # Message instance
        ):
            return
        
        # Sides:
        # 2005 0 neutral
        # 2005 1 clan
        # 2005 2 omni
        
        # The %s organization %s just entered a state of war! %s attacked the %s organization %s's tower in %s at location (%d,%d).
        # 0 - Attacker's org. side
        # 1 - Attacker's org. name
        # 2 - Attacker's name
        # 3 - Defender's org. side
        # 4 - Defender's org. name
        # 5 - Area name
        # 6 - X
        # 7 - Y
        
        # Org A (omni) ⚔ Org B (clan), Location (100,500), #RKx
        self.twitter.PostUpdate("%s (%s) \xe2\x9a\x94 %s (%s), %s (%d,%d), #%s" % (
            sides[packet.args[0][1]],
            packet.args[1],
            sides[packet.args[3][1]],
            packet.args[4],
            packet.args[5],
            packet.args[6],
            packet.args[7],
            self.tag
        ))


def main(argv = []):
    """
    Launcher.
    """
    
    # Read settings
    config = yaml.load(file("notumwars.conf", "rb"))
    
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
