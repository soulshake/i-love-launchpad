#!/usr/bin/env python
import random
import mido
import colors
import time



mido.get_ioport_names()

portnames = mido.get_ioport_names()
p = mido.open_ioport(portnames[1])

# enter programmer mode
p.send(mido.Message("sysex", data=[0, 32, 41, 2, 16, 44, 3]))
"""
LED=0
for R in [10, 20, 30, 40, 50, 60]:
    for G in [10, 20, 30, 40, 50, 60]:
        for B in [60, 20, 30, 40, 50, 60]:
            LED += 1
            print("{}: {} {} {}".format(LED, R, G, B))
            p.send(mido.Message("sysex", data=[0, 32, 41, 2, 16, 11, LED, R, G, B]))
            (240, 0,32,41,2,16,40
            if LED > 126:
                break
        if LED > 126:
            break
    if LED > 126:
        break
exit()
"""

def blink(color="YELLOW", count=3):
    color = colors.COLORS[color]
    for c in range(0, count):
        for status in "note_on", "note_off":
            for note in range(0, 10):
                p.send(mido.Message(status, note=note, velocity=color))
            time.sleep(0.3)

def clear(begin, end):
    for note in range(begin, end):
        p.send(mido.Message("note_off", note=note))

def display_row(order, offset=0):
    i = 0
    for item in order:
        i += 1
        if not item:
            continue
        p.send(mido.Message("note_on", note = i + offset, velocity = order[i-1]))


def receive_button_push():
    while True:
        event = p.receive()
        if event.type in ["polytouch"]:
            continue
        if event.type in ["control_change"]:
            print("alerting on control_change event")
            return 999
        if event.type == "sysex":
            print("skipping sysex message: {}".format(event.dict()))
            continue
        if event.velocity == 0:
            continue
        return event.note




def play(begin=50, end=58):
    random_order = [x for x in range(begin, end)]
    random.shuffle(random_order)
    fill = [0] * begin
    random_order = fill + random_order
    new_order = random_order

    display_row(sorted(random_order), offset=20)
    display_row(random_order)

    while new_order != sorted(random_order):
        guesses = []
        for x in range(0, 2):
            guesses.append(receive_button_push())

        g1, g2 = guesses[0], guesses[1]
        if g1 - 1 not in random_order or g2 - 1 not in random_order:
            blink(color="RED", count=1)
            continue
        value1 = new_order[g1 - 1]
        value2 = new_order[g2 - 1]
        index1 = new_order.index(value1)
        index2 = new_order.index(value2)

        new_order[index1] = value2
        new_order[index2] = value1
        display_row(new_order)

    print("yay!")
    blink(color="GREEN")


clear(11, 99)
play()
