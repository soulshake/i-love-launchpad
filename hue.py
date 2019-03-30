#!/usr/bin/env python
import random
import mido
import colors

mido.get_ioport_names()

portnames = mido.get_ioport_names()
p = mido.open_ioport(portnames[1])

begin = 50
end = 58
random_order = [x for x in range(begin, end)]
random.shuffle(random_order)
fill = [0] * begin
random_order = fill + random_order
new_order = random_order

def clear(begin, end):
    for note in range(begin, end):
        event = {'type': 'note_off', 'note': note, 'channel': 0}
        to_send = mido.Message.from_dict(event)
        p.send(to_send)

def display_row(order, offset=0):
    i = 0
    for item in order:
        i += 1
        if not item:
            continue
        try:
            event = {'type': 'note_on', 'time': 0, 'note': i + offset, 'velocity': order[i-1], 'channel': 0}
        except:
            from IPython import embed; embed()
        print("sending event: {}".format(event))
        to_send = mido.Message.from_dict(event)
        p.send(to_send)


def receive_button_push():
    while True:
        event = p.receive()
        if event.type in ["polytouch"]:
            continue
        if event.velocity == 0:
            continue
        #print("returning note event: {}".format(event))
        return event.note


clear(0, 100)

display_row(sorted(random_order), offset=20)
display_row(random_order)

while new_order != sorted(random_order):
    guesses = []
    for x in range(0, 2):
        guesses.append(receive_button_push())

    g1, g2 = guesses[0], guesses[1]
    if g1 not in random_order or g2 not in random_order:
        continue
    print("Guessed: {} and {}".format(g1, g2))
    value1 = new_order[g1 - 1]
    value2 = new_order[g2 - 1]
    index1 = new_order.index(value1)
    index2 = new_order.index(value2)
    #value1 = new_order[index1]
    #value2 = new_order[index2]

    print(sorted(random_order)[begin:])
    print(new_order[begin:])
    new_order[index1] = value2
    new_order[index2] = value1
    print(new_order[begin:])
    display_row(new_order)

    #from IPython import embed; embed()

print("yay!")
