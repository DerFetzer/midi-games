from collections import deque
from enum import Enum
import mido
import pygame
import random
import threading
import time


class Direction(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3

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

lock = threading.Lock()
direction = Direction.Right
last_direction = Direction.Right

outport.send(mido.Message('note_on', channel=8, note=direction.value, velocity=127))


def receive_message(message: mido.Message):
    global direction
    global last_direction

    if message.dict()["type"] == 'note_on' and message.dict()["channel"] == 8:
        note = message.dict()["note"]

        if direction == Direction(note):
            return

        if last_direction == Direction.Left and Direction(note) == Direction.Right:
            return
        if last_direction == Direction.Right and Direction(note) == Direction.Left:
            return
        if last_direction == Direction.Up and Direction(note) == Direction.Down:
            return
        if last_direction == Direction.Down and Direction(note) == Direction.Up:
            return

        with lock:
            direction = Direction(note)

            for x in range(0, 4):
                if x == direction.value:
                    outport.send(mido.Message('note_on', channel=8, note=x, velocity=127))
                else:
                    outport.send(mido.Message('note_off', channel=8, note=x))


inport = mido.open_input(name="open-cleverpad MIDI 1", callback=receive_message)

apples = 0

active_notes = deque([26, 27, 28])
apple_pos = 26

while apple_pos in active_notes:
    n = random.randrange(0, 64)
    if n not in active_notes:
        apple_pos = n
        outport.send(mido.Message("note_on", note=apple_pos, velocity=112))

for n in active_notes:
    outport.send(mido.Message("note_on", note=n, velocity=96))

while True:
    with lock:
        last_direction = direction

        off_pad = active_notes.popleft()
        head = active_notes[-1]

        x = head % 8
        y = head // 8

        if direction == Direction.Up:
            if y == 0:
                on_pad = 7 * 8 + x
            else:
                on_pad = (y - 1) * 8 + x
        elif direction == Direction.Down:
            if y == 7:
                on_pad = 0 * 8 + x
            else:
                on_pad = (y + 1) * 8 + x
        elif direction == Direction.Left:
            if x == 0:
                on_pad = y * 8 + 7
            else:
                on_pad = y * 8 + (x - 1)
        elif direction == Direction.Right:
            if x == 7:
                on_pad = y * 8 + 0
            else:
                on_pad = y * 8 + (x + 1)

        if on_pad in active_notes:
            s_over.play()

            print("Game Over!\nApples: {}".format(apples))

            for x in range(0, 64):
                outport.send(mido.Message("note_off", note=x))
                time.sleep(.05)

            break

        on_mes = mido.Message("note_on", note=on_pad, velocity=96)
        off_mes = mido.Message("note_off", note=off_pad)

        active_notes.append(on_pad)

        if on_pad == apple_pos:
            s.play()
            apples += 1
            active_notes.appendleft(off_pad)

            while apple_pos in active_notes:
                n = random.randrange(0, 64)
                if n not in active_notes:
                    apple_pos = n
                    outport.send(mido.Message("note_on", note=apple_pos, velocity=112))
        else:
            outport.send(off_mes)

        outport.send(on_mes)

    time.sleep(.5)


time.sleep(.2)

for x in range(0, 64):
    outport.send(mido.Message("note_off", note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=8, note=x))

for x in range(0, 4):
    outport.send(mido.Message("note_off", channel=9, note=x))
