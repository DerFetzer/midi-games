from enum import Enum
import mido
import numpy as np
import pygame
import random
import threading
import time


class Color(Enum):
    Black = 0
    White = 63
    Yellow = 3 | 3 << 2
    Red = 3

pygame.init()
s = pygame.mixer.Sound("/home/derfetzer/sounds_wav/message.wav")
s_over = pygame.mixer.Sound("/home/derfetzer/sounds_wav/suspend-error.wav")

outport = mido.open_output(name="open-cleverpad MIDI 1")

for x in range(0, 64):
    outport.send(mido.Message("note_off", note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=8, note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=9, note=x))

active_notes = dict()
lock = threading.Lock()


def get_random_color_value() -> (int, int):
    rem = random.randrange(1, 7)

    if rem < 4:
        return Color.White.value, 1
    elif rem < 6:
        return Color.Yellow.value, 2
    elif rem == 6:
        return Color.Red.value, 3
    else:
        raise ValueError("Invalid value {}!".format(rem))


def get_color_rem(rem: int) -> Color:
    if rem == 1:
        return Color.White
    elif rem == 2:
        return Color.Yellow
    elif rem == 3:
        return Color.Red
    else:
        raise ValueError("Invalid value {}!".format(rem))


def receive_message(message: mido.Message):
    if message.dict()["channel"] != 0:
        # reset channel to 0
        outport.send(mido.Message("control_change", control=111, value=0))

    if message.dict()["type"] == 'note_on' and message.dict()["channel"] == 0:
        note = message.dict()["note"]
        with lock:
            if note in active_notes:
                new_remaining = active_notes[note] - 1
                if new_remaining == 0:
                    s.play()
                    outport.send(message.copy(velocity=Color.Black.value))
                    del active_notes[note]
                else:
                    active_notes[note] = new_remaining
                    outport.send(message.copy(velocity=get_color_rem(new_remaining).value))


def rnd_to_delay(rnd: int) -> float:
    if rnd < 10:
        return 1
    elif rnd < 500:
        m = 0.8600255887271939
        t = 0.010486791741646434
        return m * np.exp(-t * rnd) + .2
    else:
        a = -0.0002
        n = 0.3
        return a * rnd + n


inport = mido.open_input(name="open-cleverpad MIDI 1", callback=receive_message)

rnd = 0

while True:
    rnd += 1
    note = None
    with lock:
        while note is None:
            n = random.randrange(0, 64)
            if n not in active_notes:
                note = n

        vel, remaining = get_random_color_value()

        mes = mido.Message("note_on", note=note, velocity=vel)

        active_notes[note] = remaining

        outport.send(mes)

        if len(active_notes) >= 64:
            s_over.play()

            print("Game Over!\nRound: {}".format(rnd))

            for x in range(0, 64):
                outport.send(mido.Message("note_off", note=x))
                time.sleep(.05)

            break

    d = rnd_to_delay(rnd)
    time.sleep(d)

time.sleep(.2)

for x in range(0, 64):
    outport.send(mido.Message("note_off", note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=8, note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=9, note=x))
