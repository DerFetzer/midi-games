import random
import time

import mido
import pygame

pygame.init()
s = pygame.mixer.Sound("/home/derfetzer/sounds_wav/message.wav")
s_over = pygame.mixer.Sound("/home/derfetzer/sounds_wav/suspend-error.wav")

outport = mido.open_output(name="open-cleverpad MIDI 1")

while True:
    for n in range(64):
        outport.send(mido.Message("note_on", note=n, velocity=n, channel=0))

    for c in range(3):
        for n in range(4):
            outport.send(mido.Message("note_on", note=c * 4 + n, velocity=n << c * 2, channel=1))

    for n in range(4):
        outport.send(mido.Message("note_on", note=n, velocity=n | n << 2 | n << 4, channel=2))

    for n in range(64):
        outport.send(mido.Message("note_on", note=n, velocity=random.randrange(64), channel=3))

    time.sleep(1)
