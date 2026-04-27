"""
Logikus - A Python Emulation of the Logikus Puzzle Computer

MIT License

Copyright (c) 2022 Heiko Sippel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import sys

import pygame

import logikus
from logikus.assets import load_icon
from logikus.controller import Controller, STATE_QUITTING, STATE_REDRAWING
from logikus.logic import Logic
from logikus.ui import Ui


# ------------------------------------------- Main Loop -------------------------------------------------

def main(skin: str = "classic"):
    pygame.init()

    window = pygame.Window("Spielcomputer LOGIKUS®", size=logikus.window_size)
    window.set_icon(load_icon())
    screen = window.get_surface()

    surface = pygame.Surface(logikus.window_size, pygame.SRCALPHA)
    logic = Logic()
    ui = Ui(surface, skin=skin, logic=logic)

    ui.draw()

    screen.blit(surface, (0, 0))

    controller = Controller(surface, ui, logic)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            else:
                state = controller.handle_event(event)
                if state == STATE_QUITTING:
                    pygame.quit()
                    sys.exit()
                if state == STATE_REDRAWING:
                    ui.update()
                    ui.draw()

                    screen.blit(surface, (0, 0))
                    window.flip()
        clock.tick(30)


# ------------------------------------------- Entry Point -------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Logikus with selectable skin")
    parser.add_argument(
        "--skin",
        default="classic",
        choices=['classic', 'hulk', 'metal', 'bw'],
        help="Skin name (default: classic)"
    )
    args = parser.parse_args()

    main(args.skin)
