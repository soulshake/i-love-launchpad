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
    def __init__(self, p):
        self.p = p
        self.state = self.make_blank_state()

    def make_blank_state(self):
        ret = {}
        for button in self.buttons():
            ret[button] = (0,0,0)
        return ret

    def clear(self, first_button=11, end=99):
        for note in range(first_button, end):
            self.p.send(mido.Message("note_off", note=note))

    def buttons(self):
        ret = []
        for first_button in [11, 21, 31, 41, 51, 61, 71, 81]:
            for x in range(first_button, first_button+8):
                ret.append(x)
        return ret

    def display_button(self, button, hue):
        R = hue[0]
        G = hue[1]
        B = hue[2]
        msg = mido.Message("sysex", data=[0, 32, 41, 2, 16, 11, button, R, G, B])
        logging.info(msg)
        self.p.send(msg)

    def display_row(self, hues, first_button, offset=0, step=1):
        for i in range(len(hues)):

            LED = first_button + offset + (i*step)
            if LED not in self.buttons():
                continue
            self.display_button(LED, hues[i])

    def receive_button_push(self):
        while True:
            event = self.p.receive()
            if event.type in ["polytouch"]:
                continue
            if event.type in ["control_change"]:
                logging.info("alerting on control_change event")
                return handle_control_change(event)
            if event.type == "sysex":
                logging.info("skipping sysex message: {}".format(event.dict()))
                continue
            if event.velocity == 0:
                continue

            return event.note

    def blink(self, color="YELLOW", count=3):
        color = colors.COLORS[color]
        for c in range(0, count):
            for status in "note_on", "note_off":
                for note in range(0, 10):
                    self.p.send(mido.Message(status, note=note, velocity=color))
                time.sleep(0.3)




def setup():
    portnames = mido.get_ioport_names()
    p = mido.open_ioport(portnames[1])

    # enter programmer mode
    p.send(mido.Message("sysex", data=[0, 32, 41, 2, 16, 44, 3]))
    return p


def handle_control_change(event):
    if event.control == 94:
        main()
    return 999


def play(g, hues, first_button=11, end=19):
    our_range = [x for x in range(first_button, end)]
    parallel_range = [x+10 for x in range(first_button, end)]
    print(parallel_range)

    random_order = hues.copy()
    random.shuffle(random_order)
    fill = [(0, 0, 0)] * first_button
    random_order = fill + random_order
    new_order = random_order

    #g.display_row(hues, first_button, offset=40)
    #g.display_row(hues, first_button, offset=30)
    #g.display_row(hues, first_button, offset=20)
    g.display_row(random_order, first_button, offset=10)
    g.display_row(random_order, first_button)
    #g.display_row(hues, first_button, offset=-10)
    #g.display_row(hues, first_button, offset=-20)
    #g.display_row(hues, first_button, offset=-30)

    guess_count = 0
    while fill + hues != new_order:
        guesses = []
        while len(guesses) < 2:
            guess = g.receive_button_push()
            if guess in parallel_range:
                guess -= 10  # fix this hardcoded offset
            if guess not in our_range:
                g.blink(color="RED", count=1)
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
        g.display_row(new_order, first_button)
        g.display_row(new_order, first_button, offset=10)

    logging.info("yay! you won in {} guesses".format(guess_count))
    g.blink(color="GREEN")

def fill_scale(begin=(
                random.randint(0, 64),
                random.randint(0, 64),
                random.randint(0, 64)),
            end=(
                random.choice([63,0]),
                random.choice([63,0]),
                random.choice([63,0])),
            size=8):

    ret = [begin]

    new_hues = []
    for i in range(0, size):
        new_hue = {}
        for x in [0, 1, 2]:
            interval = (end[x] - begin[x]) / size
            new_hue[x] = int(begin[x] + (i * interval))
        new_hues.append(new_hue)

    return new_hues

def interpolate_component(c1, c2, num_steps = 8):
    diff = c2 - c1
    interval = diff / (num_steps-1)
    result = [ int(c1 + interval*i) for i in range(num_steps) ]
    return result

def interpolate_colors(c1, c2, num_steps = 8):
    r = interpolate_component(c1[0], c2[0], num_steps)
    g = interpolate_component(c1[1], c2[1], num_steps)
    b = interpolate_component(c1[2], c2[2], num_steps)
    return list(zip(r,g,b))


def main():
    p = setup()
    g = Grid(p)
    g.clear()

    lower_left = (63, 0, 0)
    lower_right = (0, 0, 63)
    lower_row = interpolate_colors(lower_left, lower_right)
    g.display_row(lower_row, 11)

    upper_left = (63, 63, 0)
    upper_right = (0, 63, 0)
    upper_row = interpolate_colors(upper_left, upper_right)
    g.display_row(upper_row, 81)

    #for col in range(11, 19):
    for col in range(8):
        column = interpolate_colors(lower_row[col], upper_row[col])
        g.display_row(column, col+11, step=10)

    """
    left_col = interpolate_colors(lower_left, upper_left)
    g.display_row(left_col, 12, step=10)

    right_col = interpolate_colors(lower_right, upper_right)
    g.display_row(right_col, 19, step=10)
    """

    #hues = fill_scale(size=8, begin=(63, 0, 0), end=(0, 63, 0))
    #play(g, hues, first_button=41, end=49)


    print("bloop")
    time.sleep(1)

main()
