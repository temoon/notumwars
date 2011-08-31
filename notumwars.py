#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys

from aochat import Chat, ChatError, AOSP_CHARACTER_NAME, AOSP_CHANNEL_MESSAGE
from aochat.dimensions import DIMENSIONS
from aochat.data import load_texts


CHARACTERS = {}
CHANNEL_ALL_TOWERS = 42949672960L


def callback(chat, packet):
    """
    AOChat callback.
    """
    
    # Cache character name
    if packet.type == AOSP_CHARACTER_NAME.type:
        CHARACTERS[packet.character_id] = packet.character_name
    
    if packet.type == AOSP_CHANNEL_MESSAGE.type and packet.category and packet.instance:
        print packet.mask % tuple(packet.args)


def main(argv = []):
    """
    Launcher.
    """
    
    username = ""
    password = ""
    
    dimension = DIMENSIONS[2]
    
    load_texts("/var/lib/aochat/texts.dat")
    
    while True:
        try:
            chat = Chat(username, password, dimension.host, dimension.port)
            character = chat.characters[1]
            chat.login(character.id)
            chat.start(callback)
        except ChatError, error:
            print error
    
    return 0


if __name__ == "__main__":
    status = main(sys.argv[1:])
    sys.exit(status)
