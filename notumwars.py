#!/usr/bin/python
# -*- coding: utf-8 -*-


import datetime
import oauth
import oauthtwitter
import logging
import logging.handlers
import re
import sys
import time
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
    
    def __init__(self, username, password, host, port, character, dimension_name, twitter):
        threading.Thread.__init__(self)
        
        # Handlers
        self.name         = dimension_name
        self.log          = logging.getLogger("notumwars")
        self.twitter      = twitter
        self.twitter_user = twitter.GetUserInfo()
        
        # AO connection options
        self.username     = username
        self.password     = password
        self.host         = host
        self.port         = port
        self.character    = character
        
        # Active battles
        self.battles      = {}
    
    def run(self):
        while True:
            try:
                # Connect to dimension
                chat = Chat(self.username, self.password, self.host, self.port)
                
                # Select character by name
                for character in chat.characters:
                    if character.name == self.character:
                        break
                else:
                    self.log.critical("Unknown character '%s'" % self.character)
                    break
                
                # Login and listen chat
                chat.login(character.id)
                chat.start(self.callback)
            except ChatError, error:
                self.log.error(error)
                continue
            except SystemExit:
                break
            except Exception, error:
                self.log.exception(error)
                continue
    
    def callback(self, chat, packet):
        # Log incoming packets
        self.log.debug(repr(packet))
        
        # Check packet type
        if packet.type != AOSP_CHANNEL_MESSAGE.type:
            return
        
        # Remove old battles (older than 3 hours)
        for battle_key in self.battles.keys():
            if self.battles[battle_key]["updated"] < (time.time() - 3 * 60 * 60):
                del self.battles[battle_key]
        
        # "Battle end" flag
        battle_end = False
        
        # "All Towers" channel
        if packet.channel_id == 42949672960:
            # Organization vs. organization
            if packet.category == 506 and packet.instance == 12753364:
                # Xxx (omni) vs. Yyy (clan), Area (100,500), #RKx
                message = "%s (%s) vs. %s (%s), %s (%d,%d)" % (
                    packet.args[1],                                             # Attacker's organization name
                    self.SIDE[packet.args[0][1]],                               # Attacker's side
                    packet.args[4],                                             # Defender's organization name
                    self.SIDE[packet.args[3][1]],                               # Defender's side
                    packet.args[5],                                             # Area
                    packet.args[6],                                             # Area position X
                    packet.args[7],                                             # Area position Y
                )
                
                # Set battle key
                battle_key = (packet.args[4], packet.args[5],)
            # Player vs. organization
            else:
                match = re.search(r"^(\S+) just attacked the (\S+) organization (.+?)'s tower in (.+?) at location \((\d+), (\d+)\).\n", packet.message)
                
                if match:
                    # Aaa (player) vs. Yyy (clan), Area (100,500), #RKx
                    message = "%s (player) vs. %s (%s), %s (%s,%s)" % (
                        match.group(1),                                         # Attacker's name
                        match.group(3),                                         # Defender's organization name
                        match.group(2).lower(),                                 # Defender's side
                        match.group(4),                                         # Area
                        match.group(5),                                         # Area position X
                        match.group(6),                                         # Area position Y
                    )
                    
                    # Set battle key
                    battle_key = (match.group(3), match.group(4),)
                else:
                    return
        # "Tower Battle Outcome" channel
        elif packet.channel_id == 42949672962:
            match = re.search(r"^The (\S+) organization (.+?) attacked the (\S+) (.+?) at their base in (.+?)\.", packet.message)
            
            if match:
                # Xxx (omni) won! Yyy (clan) lost Area, #RKx
                message = "%s (%s) won! %s (%s) lost %s" % (
                    match.group(2),                                             # Winner's name
                    match.group(1).lower(),                                     # Winner's side
                    match.group(4),                                             # Loser's name
                    match.group(3).lower(),                                     # Loser's side
                    match.group(5),                                             # Area
                )
                
                # Set battle key and "end" flag
                battle_key = (match.group(4), match.group(5),)
                battle_end = True
            else:
                return
        # Other channel
        else:
            return
        
        # Get active battle or init new
        self.battles[battle_key] = self.battles.get(battle_key, { "updated": None, "id": None })
        self.battles[battle_key]["updated"] = time.time()
        
        # Post to Twitter
        attempts = 10
        
        while attempts:
            try:
                attempts -= 1
                
                if self.battles[battle_key]["id"]:
                    self.twitter.PostUpdate("@%s %s, #%s" % (self.twitter_user.screen_name, message, self.name,), self.battles[battle_key]["id"])
                else:
                    self.battles[battle_key]["id"] = self.twitter.PostUpdate("%s, #%s" % (message, self.name,)).id
            except Exception, error:
                self.log.exception(error)
                time.sleep(1)
                
                continue
            
            break
        else:
            self.log.critical("Can't post to Twitter!")
            return
        
        # Update battle
        if battle_end:
            del self.battles[battle_key]
        
        # Log message
        self.log.info(message)


def main(argv = []):
    """
    Launcher.
    """
    
    # Read settings
    config = yaml.load(file("/usr/local/etc/notumwars.conf", "rb"))
    
    # Init logger
    log_format = logging.Formatter("[%(asctime)s] %(threadName)s: %(message)s", "%Y-%m-%d %H:%M:%S %Z")
    
    log_handler = logging.FileHandler(config["general"]["log_filename"]) if config["general"]["log_filename"] else logging.StreamHandler(sys.stdout)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(log_format)
    
    log_smtp_handler = logging.handlers.SMTPHandler(
        mailhost    = (config["general"]["smtp_host"], config["general"]["smtp_port"],),
        credentials = (config["general"]["smtp_username"], config["general"]["smtp_password"],),
        fromaddr    = config["general"]["smtp_from"],
        toaddrs     = config["general"]["smtp_to"],
        subject     = "Occurrence of an error",
    )
    log_smtp_handler.setLevel(logging.CRITICAL)
    log_smtp_handler.setFormatter(log_format)
    
    log = logging.getLogger("notumwars")
    log.setLevel(logging.getLevelName(config["general"]["log_level"].upper()))
    log.addHandler(log_handler)
    log.addHandler(log_smtp_handler)
    
    # Init Twitter API
    access_token = oauth.oauth.OAuthToken(config["twitter"]["access_token_key"], config["twitter"]["access_token_secret"])
    twitter      = oauthtwitter.OAuthApi(config["twitter"]["consumer_key"], config["twitter"]["consumer_secret"], access_token)
    
    # Start workers
    workers = []
    
    for dimension in config["ao"]["dimensions"]:
        worker = Worker(
            username       = config["ao"]["username"],
            password       = config["ao"]["password"],
            host           = dimension["host"],
            port           = dimension["port"],
            character      = dimension["character"],
            dimension_name = dimension["name"],
            twitter        = twitter,
        )
        
        worker.start()
        workers.append(worker)
    
    for worker in workers:
        worker.join()
    
    return 0


if __name__ == "__main__":
    status = main(sys.argv[1:])
    sys.exit(status)
