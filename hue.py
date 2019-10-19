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

    def clear(self, first_button=1, end=99):
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
        logging.debug(msg)
        self.p.send(msg)

    def display_row(self, hues, first_button, offset=0, step=1, sleep=0):
        assert isinstance(hues, dict)

        for k in hues:
            LED = k
            self.display_button(LED, hues[k])
            time.sleep(sleep)
            if LED not in self.buttons():
                #from IPython import embed; embed()
                print(LED)
                raise ValueError("{} not in self.buttons()".format(LED))


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
        for c in range(count):
            for status in "note_on", "note_off":
                for note in range(10):
                    self.p.send(mido.Message(status, note=note, velocity=color))
                time.sleep(0.3)

    def fill_scale(self, first_button = 11,
                begin=(
                    random.randint(0, 64),
                    random.randint(0, 64),
                    random.randint(0, 64)),
                end=(
                    random.choice([63,0]),
                    random.choice([63,0]),
                    random.choice([63,0])),
                size=8):

        new_hues = {}
        for button in self.buttons():
            new_hues[button] = {0: 0, 1: 0, 2: 0}

        for i in range(first_button, first_button+size):
            new_hue = {}
            for x in [0, 1, 2]:
                interval = (end[x] - begin[x]) / size
                new_hue[x] = int(begin[x] + ((i-first_button) * interval))
            #new_hues.append(new_hue)
            if i not in new_hues:
                logging.warn("tried to assign to nonexistent button")
            new_hues[i] = new_hue

        return new_hues

    def pulse_buttons(self, buttons):
        # last param is the color
        for button in buttons:
            msg = mido.Message("sysex", data=[0, 32, 41, 2, 16, 40, button, 0])
            logging.debug(msg)
            self.p.send(msg)


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


def are_equal(scrambled_hues, correct_hues):
    for k in scrambled_hues:
        if scrambled_hues[k] != correct_hues[k]:
            logging.debug("{} != {}".format(scrambled_hues[k], correct_hues[k]))
            return False
        logging.debug("{} == {}".format(scrambled_hues[k], correct_hues[k]))
    return True

def play(g, hues, to_scramble=list(range(11, 19))):
    correct_hues = hues
    scrambled_hues = hues.copy()

    g.display_row(correct_hues, 11)
    time.sleep(.5)

    our_range = to_scramble
    scrambled_hues = {k:v for k,v in hues.items() if k in our_range}
    scrambled_keys = [x for x in scrambled_hues.keys()]
    random.shuffle(scrambled_keys)

    for k in to_scramble:
        if k not in g.buttons():
            continue
        scrambled_hues[k] = correct_hues[scrambled_keys.pop()]
    assert scrambled_keys == []

    g.display_row(scrambled_hues, 11, sleep=.1)

    guess_count = 0

    while not are_equal(scrambled_hues, correct_hues):
        guesses = []
        while len(guesses) < 2:
            guess = g.receive_button_push()
            if guess == 999:
                g.pulse_buttons(scrambled_hues)
                time.sleep(.3)
                g.display_row(scrambled_hues, 11)
            if guess not in our_range:
                g.blink(color="RED", count=1)
                logging.info("discarding invalid guess: {} (not in {})".format(guess, our_range))
                if guesses != []:
                    g.display_button(guesses[0], scrambled_hues[guesses[0]])
                    guesses = []
                continue
            guesses.append(guess)
            g.pulse_buttons([guesses[0]])
        g.display_button(guesses[0], scrambled_hues[guesses[0]])

        g1, g2 = guesses[0], guesses[1]
        value1 = scrambled_hues[g1]
        value2 = scrambled_hues[g2]

        scrambled_hues[g1] = value2
        scrambled_hues[g2] = value1
        g.display_row(scrambled_hues, 11)

        guess_count += 1

        print("{} vs {}".format(scrambled_hues[g1], scrambled_hues[g2]))
        print("{} vs {}".format(correct_hues[g1], correct_hues[g2]))
        print("----")
        # pulse event received?
        #g.pulse_buttons(scrambled_hues)
        g.display_row(scrambled_hues, 11, sleep=.1)




    """
    while fill + hues != new_order:

        value1 = new_order[g1]
        value2 = new_order[g2]
        index1 = new_order.index(value1)
        index2 = new_order.index(value2)

        new_order[index1] = value2
        new_order[index2] = value1
        g.display_row(new_order, first_button)
        g.display_row(new_order, first_button, offset=10)

    """
    logging.info("yay! you won in {} guesses".format(guess_count))
    g.blink(color="GREEN")


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
    #hues = g.fill_scale(size=8, first_button=81, begin=(63, 0, 0), end=(0, 63, 0))
    hues = {}

    # Fill lower row
    lower_left = (63, 0, 0)
    lower_right = (0, 0, 63)
    lower_row = interpolate_colors(lower_left, lower_right)
    for x in range(8):
        hues[x+11] = lower_row[x]
    g.display_row(hues, 11)

    # Fill upper row
    upper_left = (0, 63, 0)
    upper_right = (0, 63, 63)
    upper_row = interpolate_colors(upper_left, upper_right)
    for x in range(8):
        hues[x+81] = upper_row[x]
    g.display_row(hues, 81)

    time.sleep(.5)

    # fill all columns
    for col in range(8):
        a = col + 11
        b = col + 81 #a + 70
        colors = interpolate_colors(hues[a], hues[b])
        for x in range(8):
            button = a + (x*10)
            try:
                hues[button] = colors[x]
            except:
                print(button, col, x)
    g.display_row(hues, 81)
    #to_scramble=[12,22,32,42,52,62,72,82]
    #to_scramble.extend([17,27,37,47,57,67,77,87])
    #to_scramble.extend([18,28,38,48,58,68,78,88])
    to_scramble = []
    to_scramble=[41,32,23,14,15,26,37,48]
    to_scramble.extend([51,62,73,84,85,76,67,58])
    to_scramble = [
        22,23,24,25,26,27,
        32,33,34,35,36,37,
        42,43,44,45,46,47,
        52,53,54,55,56,57,
        62,63,64,65,66,67,
        72,73,74,75,76,77
    ]

    play(g, hues, to_scramble)


    print("bloop")
    time.sleep(1)

main()
