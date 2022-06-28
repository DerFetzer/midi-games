from enum import Enum
import mido
import pygame
import random
import threading
import time


class Color(Enum):
    Black = 0
    White = 16
    Yellow = 32
    Aqua = 48
    Purple = 64
    Blue = 80
    Green = 96
    Red = 112

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

        if len(active_notes) == 64:
            s_over.play()

            print("Game Over!\nRound: {}".format(rnd))

            for x in range(0, 64):
                outport.send(mido.Message("note_off", note=x))
                time.sleep(.05)

            break

    if rnd < 10:
        time.sleep(1)
    elif rnd < 30:
        time.sleep(.8)
    elif rnd < 70:
        time.sleep(.6)
    elif rnd < 140:
        time.sleep(.4)
    elif rnd < 240:
        time.sleep(.3)
    elif rnd < 300:
        time.sleep(.25)
    elif rnd < 500:
        time.sleep(.2)
    elif rnd < 800:
        time.sleep(.15)
    elif rnd < 1000:
        time.sleep(.1)
    else:
        time.sleep(.05)

time.sleep(.2)

for x in range(0, 64):
    outport.send(mido.Message("note_off", note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=8, note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=9, note=x))
