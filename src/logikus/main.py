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
from importlib import resources
from pathlib import Path

import pygame

import logikus
from logikus.controller import Controller, STATE_QUITTING, STATE_REDRAWING
from logikus.logic import Logic
from logikus.ui import Ui


# ------------------------------------------- Main Loop -------------------------------------------------

def main(skin: str = "classic"):
    pygame.init()
    window = pygame.display.set_mode(logikus.window_size, pygame.SRCALPHA)
    pygame.display.set_caption("Spielcomputer LOGIKUS®")

    icon = _load_window_icon()
    if icon is not None:
        pygame.display.set_icon(icon)

    surface = pygame.Surface(logikus.window_size, pygame.SRCALPHA)
    logic = Logic()
    ui = Ui(surface, skin=skin, logic=logic)

    ui.draw()
    window.blit(surface, (0, 0))
    pygame.display.flip()

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
                    window.blit(surface, (0, 0))
                    pygame.display.flip()
        clock.tick(30)


# ---------------------------------- Safe loading of windows icon fromm resources -----------------------

def _load_window_icon() -> None | pygame.Surface:
    """Load the application icon from package resources or PyInstaller data."""
    try:
        icon_resource = resources.files("logikus.images").joinpath("icon.png")
        if icon_resource.is_file():
            with icon_resource.open("rb") as f:
                return pygame.image.load(f)
    except Exception:
        pass

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    for path in (base / "images" / "icon.png", base / "logikus" / "images" / "icon.png"):
        if path.is_file():
            return pygame.image.load(str(path))
    return None


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
