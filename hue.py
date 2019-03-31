#!/usr/bin/env python
import random
import mido
import colors
import time
import logging
import os

log_format = "[%(levelname)s] %(filename)s:%(lineno)d %(funcName)s() -> %(message)s"
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format=log_format)

# /etc/X11/rgb.txt

class Grid(object):
    def __init__(self):
        pass

    def clear(self, first_button=11, end=99):
        for note in range(first_button, end):
            p.send(mido.Message("note_off", note=note))

    def buttons(self):
        first_button = 11
        ret = []
        for first_button in [11, 21, 31, 41, 51, 61, 71, 81]:
            for x in range(first_button, first_button+8):
                ret.append(x)
        return ret


def setup():
    portnames = mido.get_ioport_names()
    p = mido.open_ioport(portnames[1])

    # enter programmer mode
    p.send(mido.Message("sysex", data=[0, 32, 41, 2, 16, 44, 3]))
    return p


def blink(color="YELLOW", count=3):
    color = colors.COLORS[color]
    for c in range(0, count):
        for status in "note_on", "note_off":
            for note in range(0, 10):
                p.send(mido.Message(status, note=note, velocity=color))
            time.sleep(0.3)

def display_row(hues, first_button, offset=0):
    i = -1
    for hue in hues:
        if hue == (0, 0, 0):
            continue
        i += 1
        if not hues:
            logging.warn("out of hues")
            return

        LED = first_button + offset + i
        if LED not in Grid().buttons():
            i += 1
            continue
        R = hue[0]
        G = hue[1]
        B = hue[2]
        msg = mido.Message("sysex", data=[0, 32, 41, 2, 16, 11, LED, R, G, B])
        logging.debug(msg)
        p.send(msg)

def receive_button_push():
    while True:
        event = p.receive()
        if event.type in ["polytouch"]:
            continue
        if event.type in ["control_change"]:
            logging.info("alerting on control_change event")
            return 999
        if event.type == "sysex":
            logging.info("skipping sysex message: {}".format(event.dict()))
            continue
        if event.velocity == 0:
            continue

        return event.note

def play(hues, first_button=11, end=19):
    our_range = [x for x in range(first_button, end)]
    random_order = hues.copy()
    random.shuffle(random_order)
    fill = [(0, 0, 0)] * first_button
    random_order = fill + random_order
    new_order = random_order

    display_row(hues, first_button, offset=20)
    display_row(random_order, first_button)

    guess_count = 0
    while fill + hues != new_order:
        guesses = []
        while len(guesses) < 2:
            guess = receive_button_push()
            if guess not in our_range:
                blink(color="RED", count=1)
                logging.info("discarding invalid guess: {} (not in {})".format(guess, our_range))
                guesses = []
                continue
            guesses.append(guess)

        guess_count += 1

        g1, g2 = guesses[0], guesses[1]
        value1 = new_order[g1]
        value2 = new_order[g2]
        index1 = new_order.index(value1)
        index2 = new_order.index(value2)

        new_order[index1] = value2
        new_order[index2] = value1
        display_row(new_order, first_button)

    logging.info("yay! you won in {} guesses".format(guess_count))
    blink(color="GREEN")

def fill_scale(begin=(random.randint(0, 64), random.randint(0, 64), random.randint(0, 64)), end=(63, 0, 0), size=8):
    ret = [begin]

    new_hues = []
    for i in range(0, size):
        new_hue = {}
        for x in [0, 1, 2]:
            interval = (end[x] - begin[x]) / size
            new_hue[x] = int(begin[x] + (i * interval))
        new_hues.append(new_hue)

    return new_hues


p = setup()
g = Grid()
g.clear()

hues = fill_scale(size=8)
play(hues)
