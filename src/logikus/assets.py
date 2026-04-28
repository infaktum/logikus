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

import sys
from importlib import resources
from pathlib import Path
from typing import TypeAlias, Tuple

import pygame
from pygame import Vector2, Surface

import logikus

RGB: TypeAlias = tuple[int, int, int]
Point: TypeAlias = tuple[int, int]

# -------------------------------------------- Constants -------------------------------------------------

SIZE = logikus.grid_size

SIZE_SLIDER = (35, 75)
SIZE_BUTTON = (35, 95)

SIZE_PATCHBOARD = (77 * SIZE, 62 * SIZE)
SIZE_LAMP = (7 * SIZE, 10 * SIZE)

FONT_SIZE_MENU = 20
FONT_SIZE_KOSMOS = 38
FONT_SIZE_ABC = 26
FONT_SIZE_A_B = 18
FONT_SIZE_S_T = 32
FONT_SIZE_X_Y = 20

"""
SIZE = 11  # 15  # 15

SIZE_SLIDER = (25, 60)
SIZE_BUTTON = (25, 70)
"""

# ---------------------------------------------- Skin Colors -------------------------------------------

SKIN_CLASSIC = {'bg': (195, 175, 145), 'fg': (187, 68, 62), 'lamp_on': (244, 247, 225), 'lamp_off': (110, 45, 7),
                'wire': [(50, 50, 200), (50, 150, 50), (200, 50, 50), (200, 50, 200), (50, 200, 200), (255, 255, 50),
                         (150, 150, 150), (50, 50, 50), (250, 250, 250)],
                'live_wire': (0, 255, 0)}
SKIN_HULK = {'bg': (50, 175, 50), 'fg': (190, 60, 190), 'lamp_on': (230, 90, 220), 'lamp_off': (190, 60, 190),
             'wire': [(190, 60, 190)], 'live_wire': (230, 90, 220)}
SKIN_MILITARY = {'bg': (88, 89, 68), 'fg': (107, 94, 59), 'lamp_on': (255, 255, 255), 'lamp_off': (30, 40, 30),
                 'wire': [(107, 94, 59), (107, 94, 59), (107, 94, 59)], 'live_wire': (255, 255, 255)}

SKIN_METAL = {'bg': (120, 120, 120), 'fg': (150, 150, 150), 'lamp_on': (150, 150, 150), 'lamp_off': (70, 70, 70),
              'wire': [(20, 20, 20), (100, 100, 100), (180, 180, 180)], 'live_wire': (255, 255, 255)}

SKIN_BW = {'bg': (240, 240, 240), 'fg': (20, 20, 20), 'lamp_on': (255, 255, 255), 'lamp_off': (50, 50, 50),
           'wire': [(20, 20, 20), (100, 100, 100), (180, 180, 180)], 'live_wire': (255, 255, 255)}

SKINS = {"classic": SKIN_CLASSIC, "hulk": SKIN_HULK, "military": SKIN_MILITARY, "metal": SKIN_METAL, "bw": SKIN_BW}

# ----------------------------------------- Texts in menu -------------------------------------------------


TEXT = {'QUIT': 'Quit', 'LOAD': 'Load', 'SAVE': 'Save', 'NEW': 'New'}


# -------------------------------------------- Resources -------------------------------------------------

class Assets:
    """
    Manages all graphical assets and resources for the Logikus application.

    This class handles the creation and management of all visual elements including
    the game board, buttons, sliders, lamps, and menu items. It supports different
    visual skins/themes for customization.
    """

    def __init__(self, skin_name: str = "classic") -> None:
        """
        Initialize the Assets manager with a specific visual skin.

        Creates all necessary graphical elements using the Painter class and
        generates default lamp images.

        Args:
            skin_name: Name of color scheme dictionary containing 'bg', 'fg', 'lamp_on',
                        'lamp_off', 'wire', and 'live_wire' color definitions.
                        Defaults to SKIN_CLASSIC.
                        
        Attributes:
            skin_name (str): The current color scheme.
        """

        self.skin = SKINS[skin_name]
        painter = Painter(self.skin['bg'], self.skin['fg'], self.skin['lamp_off'])

        self.images = {'board': painter.paint_board(),
                       'slider': painter.paint_slider(),
                       'button': painter.paint_button(),
                       'menu_new': painter.paint_menu_item(TEXT['NEW']),
                       'menu_open': painter.paint_menu_item(TEXT['LOAD']),
                       'menu_save': painter.paint_menu_item(TEXT['SAVE']),
                       'menu_quit': painter.paint_menu_item(TEXT['QUIT']),
                       }

        self.set_lamps()

    def set_lamps(self) -> None:
        """
        Generate default rectangular lamp images for all 10 lamps (L0-L9).

        Creates both 'on' and 'off' states for each lamp using solid colored rectangles
        based on the current skin colors.
        """
        for lamp in range(10):
            surface = pygame.Surface(SIZE_LAMP)
            surface.set_colorkey((255, 0, 255))
            surface.fill((255, 0, 255))
            pygame.draw.rect(surface, self.skin['lamp_on'], (1, 0, *SIZE_LAMP - pygame.Vector2(2, 0)))
            self.create_lamp_images(surface, lamp)

    def load_insert(self, path: str | Path) -> None:
        """
        Load lamp images from an external image file.

        Divides the loaded image into 10 equal parts horizontally and creates
        lamp surfaces from each segment. Only creates 'on' state insert.

        Args:
            path (str): File path to the lamp image file.
        """
        insert = pygame.image.load(f'{path}').convert_alpha()
        img_w, img_h = insert.get_size()
        w = img_w // 10

        for l in range(10):
            surface = pygame.Surface(SIZE_LAMP)
            surface.set_colorkey((255, 0, 255))
            surface.fill((255, 0, 255))
            rect = pygame.Rect(2 + l * w, 2 + 0, w - 4, img_h - 4)
            part = insert.subsurface(rect).copy()
            surface.blit(part, (2, 2, w - 4, img_h - 4))
            pygame.draw.rect(surface, (0, 0, 0), (1, 0, *SIZE_LAMP - pygame.Vector2(2, 0)), width=1)
            self.images[f'L{l}_on'] = surface
            self.images[f'L{l}_off'] = self.create_dark_insert(surface)

    def create_dark_insert(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Taints an image for a lamp with the "lamp off color". This image can then be used on
        the lamps row, so that it can only nearly be seen.

        Args:
            surface: the original surface

        Returns:
            the darkened image
        """
        dark_surface = pygame.Surface(surface.get_size(), flags=pygame.SRCALPHA)
        dark_surface.blit(surface, (0, 0))
        dark_color = self.skin['lamp_off']
        dark_surface.fill(dark_color, special_flags=pygame.BLEND_MULT)

        return dark_surface

    def create_lamp_images(self, surface: Surface, lamp: int):
        """
        Create and store on/off lamp images for a specific lamp.

        Args:
            surface (pygame.Surface): The lamp surface in 'on' state.
            lamp (int): Lamp index (0-9).
        """
        self.images[f'L{lamp}_on'] = surface
        surface = pygame.Surface(SIZE_LAMP)
        surface.set_colorkey((255, 0, 255))
        surface.fill((255, 0, 255))
        pygame.draw.rect(surface, self.skin['lamp_off'], (1, 0, *SIZE_LAMP - pygame.Vector2(2, 0)))
        self.images[f'L{lamp}_off'] = surface


# ------------------------------------------- Drawing Helpers -------------------------------------------------


def draw_rect_3d(surface: pygame.Surface, color1: RGB, color2: RGB, rect: pygame.Rect, width: int = 1,
                 raised: bool = True, ) -> None:
    """
    Draw a rectangle with a 3D effect using two colors.

    Creates a raised/embossed appearance by drawing the main rectangle with color1
    and adding highlight lines with color2 on the top and left edges.

    Args:
        surface (pygame.Surface): The surface to draw on.
        color1 (tuple): Main fill color (RGB tuple).
        color2 (tuple): Highlight color for 3D effect (RGB tuple).
        rect (pygame.Rect): Rectangle dimensions and position.
        width (int): Line width for the rectangle outline. Defaults to 1.
        raised (bool): flag ig 3d rectangle is raised (default) im imprinted
    """

    if raised:
        pygame.draw.rect(surface, color1, rect, width)
        pygame.draw.line(surface, color2, rect.topleft, rect.topright - Vector2(width, 0), width)
        pygame.draw.line(surface, color2, rect.topleft, rect.bottomleft - Vector2(0, width), width)
    else:
        pygame.draw.rect(surface, color1, rect, width)
        pygame.draw.line(surface, color2, rect.bottomleft - Vector2(-width, width),
                         rect.bottomright - Vector2(width, width), width)
        pygame.draw.line(surface, color2, rect.topright - Vector2(width, 0), rect.bottomright - Vector2(width, width),
                         width)


def draw_hole(surface: pygame.Surface, color: RGB, center: Point) -> None:
    """
    Draw a contact hole with a 3D appearance.

    Creates a circular hole with a light outer ring and dark inner circle
    to simulate depth.

    Args:
        surface (pygame.Surface): The surface to draw on.
        color (tuple): Color for the outer ring (RGB tuple).
        center (tuple): Center position (x, y) of the hole.
    """
    pygame.draw.circle(surface, color, center, 4, width=0)
    pygame.draw.circle(surface, (0, 0, 0), center, 3, width=0)


def draw_text(surface: pygame.Surface, color1: RGB, text: str, size: int, position: Point) -> None:
    """
    Draw simple text on a surface.

    Renders text using the Arial system font and blits it to the surface.

    Args:
        surface (pygame.Surface): The surface to draw on.
        color1 (tuple): Text color (RGB tuple).
        text (str): The text to render.
        size (int): Font size in points.
        position (tuple): Position (x, y) to place the text.
    """

    standard_font = load_standard_font(size)
    text_surf = standard_font.render(text, True, color1)
    surface.blit(text_surf, position + pygame.Vector2(0, 0))


def draw_text3d(surface: pygame.Surface, color1: RGB, text: str, size: int, position: Point) -> None:
    """
    Draw text with a 3D shadow effect.

    Renders text twice - first a black shadow offset by (1,1), then the main
    text in the specified color, creating a raised appearance.

    Args:
        surface (pygame.Surface): The surface to draw on.
        color1 (tuple): Main text color (RGB tuple).
        text (str): The text to render.
        size (int): Font size in points.
        position (tuple): Position (x, y) to place the text.
    """

    standard_font = load_standard_font(size)
    shadow_surf = standard_font.render(text, True, (0, 0, 0))
    surface.blit(shadow_surf, position + pygame.Vector2(1, 1))
    text_surf = standard_font.render(text, True, color1)
    surface.blit(text_surf, position + pygame.Vector2(0, 0))


# ----------------------------------- Resource helpers ------------------------------------------


def get_base_path() -> Path:
    """
    Get the base path for loading assets.

    For PyInstaller builds, returns the temporary directory. Otherwise,
    returns the directory containing the current module.

    Returns:
        Path: The base path for asset resources.
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_PATH = get_base_path()


def asset_path(*parts) -> Path:
    """
    Construct a path to an asset file relative to the base path.

    Args:
        *parts: Path components to join with the base path.

    Returns:
        Path: The complete path to the asset.
    """
    return BASE_PATH.joinpath(*parts)


def font(name: str) -> Path:
    """
    Get the path to a font file in the 'fonts' directory.

    Args:
        name (str): The font filename.

    Returns:
        Path: The full path to the font file.
    """
    return asset_path(".", "fonts", name)


def image(name: str) -> Path:
    """
    Get the path to an image file in the 'images' directory.

    Args:
        name (str): The image filename.

    Returns:
        Path: The full path to the image file.
    """
    return asset_path("logikus", "images", name)


def load_standard_font(size: int) -> pygame.font.Font:
    """
    Loads the standard font of the game with a given size from the package
    Args:
        size: The size of the font to be loaded.

    Returns: the font in the fonts directory

    """
    return pygame.font.Font(font(logikus.font), size)


# -------------------------------------------- Painter -------------------------------------------------

class Painter:
    """
    Handles all graphical painting operations for the Logikus board.

    This class is responsible for creating all visual elements of the Logikus
    puzzle computer interface, including the board, contacts, sliders, buttons,
    and decorative elements. It uses color variations to create 3D effects.
    """

    def __init__(self, color_bg_medium: RGB, color_button_medium: RGB, color_hud: RGB) -> None:
        """
        Initialize the Painter with base colors.

        Calculates light and dark variations of the base colors for creating
        3D visual effects throughout the interface.

        Args:
            color_bg_medium (tuple): Base background color (RGB tuple).
            color_button_medium (tuple): Base button color (RGB tuple).
            
        Attributes:
            color_bg_medium (tuple): Medium background color.
            color_button_medium (tuple): Medium button color.
        """
        self.color_bg_medium = color_bg_medium
        self.color_button_medium = color_button_medium
        self.color_hud = color_hud

        self.color_bg_light = tuple(max(0, min(255, c + 50)) for c in color_bg_medium)
        self.color_bg_dark = tuple(max(0, min(255, c - 50)) for c in color_bg_medium)

        self.color_button_light = tuple(max(0, min(255, c + 50)) for c in color_button_medium)
        self.color_button_dark = tuple(max(0, min(255, c - 50)) for c in color_button_medium)

        self.size_slider = SIZE_SLIDER
        self.size_button = SIZE_BUTTON

    def paint_board(self) -> pygame.Surface:
        """
        Create the complete Logikus board surface.

        Assembles all board components including contacts, sliders, logo,
        and decorative elements into a single surface.

        Returns:
            pygame.Surface: Complete board image with alpha channel.
        """
        surface = pygame.Surface(SIZE_PATCHBOARD)
        surface.fill(self.color_bg_medium, (0, 0, *SIZE_PATCHBOARD))

        self.paint_hud(surface)
        self.paint_contacts(surface)
        self.paint_sliders(surface)
        self.draw_logo_and_letters(surface)
        self.draw_insert(surface)

        logikus_image = surface.copy().convert_alpha()
        return logikus_image

    # ------------------------------------------- Paint Menu -------------------------------------------------

    def paint_menu_item(self, name: str) -> pygame.Surface:
        """
        Create a menu item surface with the specified name.

        Args:
            name (str): Text to display on the menu item.
            
        Returns:
            pygame.Surface: Menu item surface with 3D border and text.
        """
        surface = pygame.Surface((5 * SIZE, 2 * SIZE))
        surface.fill(self.color_bg_medium)
        draw_rect_3d(surface, self.color_bg_dark, self.color_bg_light, pygame.Rect(0, 0, 5 * SIZE, 2 * SIZE), width=2)
        draw_text3d(surface, self.color_bg_light, name, FONT_SIZE_MENU, (SIZE, 2))
        return surface

    # ------------------------------------------- Paint Slider -------------------------------------------------

    def paint_slider(self) -> pygame.Surface:
        """
        Create a slider control surface.

        Returns:
            pygame.Surface: Slider surface with 3D appearance and texture.
        """
        slider = pygame.Surface(self.size_slider + pygame.Vector2(10, 0))

        slider.set_colorkey((255, 255, 255))
        slider.fill((255, 255, 255))
        rect = pygame.Rect(4, 0, *self.size_slider)

        slider.fill(self.color_button_medium, (5, 0, *self.size_slider))

        for y in range(5, rect.h, 5):
            pygame.draw.line(slider, self.color_button_dark, (4, y), (SIZE_SLIDER[0] + 4, y), width=2)
            pygame.draw.line(slider, self.color_button_light, (4, y - 1), (SIZE_SLIDER[0] + 4, y - 1), width=1)

        pygame.draw.line(slider, self.color_button_dark, rect.topleft, rect.bottomleft, width=2)
        pygame.draw.line(slider, self.color_button_dark, rect.topright, rect.bottomright, width=2)
        pygame.draw.line(slider, self.color_button_light, rect.topleft, rect.topright, width=2)

        slider_image = slider.copy().convert_alpha()

        return slider_image

    # ------------------------------------------- Paint Button -------------------------------------------------

    def paint_button(self) -> pygame.Surface:
        """
        Create a button control surface in the "off" state.

        Returns:
            pygame.Surface: Button surface with 3D appearance and texture.
        """
        button = pygame.Surface(self.size_button)
        button.set_colorkey((255, 255, 255))
        button.fill((255, 255, 255))
        rect = pygame.Rect(0, 0, *self.size_button)

        # Draw button in "off" state

        button.fill(self.color_button_medium, (0, 2, *self.size_button - pygame.Vector2(2, 0)))
        for y in range(8, rect.h, 5):
            pygame.draw.line(button, self.color_button_dark, (0, y), (43, y), width=2)
            pygame.draw.line(button, self.color_button_light, (0, y - 1), (43, y - 1), width=1)
            pass

        pygame.draw.line(button, self.color_button_dark, rect.topleft + pygame.Vector2(0, 2), rect.bottomleft, width=2)
        pygame.draw.line(button, self.color_button_light, rect.topleft + pygame.Vector2(0, 2),
                         rect.topright + pygame.Vector2(0, 2), width=2)
        pygame.draw.line(button, (0, 0, 0), rect.topright + pygame.Vector2(-1, 0),
                         rect.bottomright + pygame.Vector2(-1, 0), width=3)

        return button

    # ------------------------------------------- Paint Logo and Letters -------------------------------------------------

    def draw_insert(self, surface: pygame.Surface) -> None:
        """
        Draw the decorative inlay line on the board.

        Args:
            surface (pygame.Surface): The board surface to draw on.
        """
        draw_rect_3d(surface, self.color_bg_light, self.color_bg_dark, pygame.Rect(8 * SIZE, 51 * SIZE, 1020, SIZE))

    def draw_logo_and_letters(self, surface: pygame.Surface) -> None:
        """
        Draw the KOSMOS logo and letter labels on the board.

        Args:
            surface (pygame.Surface): The board surface to draw on.
        """
        draw_rect_3d(surface, self.color_bg_dark, self.color_bg_light, pygame.Rect(SIZE, 195, 12 * SIZE, 4 * SIZE),
                     width=2, raised=False)
        draw_text3d(surface, self.color_bg_light, 'KOSMOS', FONT_SIZE_KOSMOS, (22, 202))

        for n, letter in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K']):
            x = 94
            y = 320 + n * 45

            draw_text3d(surface, self.color_bg_light, letter, FONT_SIZE_ABC, (x, y))

            draw_text3d(surface, self.color_bg_light, 'S', FONT_SIZE_S_T, (94, 840))
            draw_text3d(surface, self.color_bg_light, 'T', FONT_SIZE_S_T, (40, 780))
            draw_text3d(surface, self.color_bg_light, 'y', FONT_SIZE_X_Y, (94, 780))
            draw_text3d(surface, self.color_bg_light, 'x', FONT_SIZE_X_Y, (94, 900))

    # ------------------------------------------- Paint Contacts -------------------------------------------------

    def paint_contacts(self, surface: pygame.Surface) -> None:
        """
        Draw all contact points and related elements on the board.

        This includes the main contact grid, lamp contacts, power contacts,
        and decorative elements.

        Args:
            surface (pygame.Surface): The board surface to draw on.
        """
        for x in range(120, 120 + 10 * 105, 105):
            for y in range(315, 17 * 45, 45):
                rect = pygame.Rect(x, y, 5 * SIZE, 3 * SIZE)
                draw_rect_3d(surface, self.color_bg_dark, self.color_bg_light, rect)
                draw_hole(surface, self.color_bg_light, rect.topleft + pygame.Vector2(7, 7))
                draw_hole(surface, self.color_bg_light, rect.topleft + pygame.Vector2(7, 7 + SIZE))
                draw_hole(surface, self.color_bg_light, rect.topleft + pygame.Vector2(7, 7 + 30))
                draw_hole(surface, self.color_bg_light, rect.topright + pygame.Vector2(-7, 7))
                draw_hole(surface, self.color_bg_light, rect.topright + pygame.Vector2(-7, 7 + SIZE))
                draw_hole(surface, self.color_bg_light, rect.topright + pygame.Vector2(-7, 7 + 30))

                pygame.draw.rect(surface, (0, 0, 0), (x + 16, y + 18, 3 * 15 - 2, 15 - 4), width=0)
                pygame.draw.rect(surface, self.color_button_medium, (x + 16 + 10, y + 20, 3 * 15 - 20, 15 - 10),
                                 width=0)

        # Lamp contacts at y=180
        for n, x in enumerate(range(9 * 15, 9 * 15 + 10 * 7 * 15, 7 * 15)):
            y = 180
            self.paint_contact(surface, (x, y))

            draw_text3d(surface, self.color_bg_light, f'L{n}', 16, (x - 16, y - 18))

        # Contacts of power source and button
        self.paint_contact(surface, (15, 180))
        draw_text3d(surface, self.color_bg_light, 'Q', 16, (60, 180 - 18))

        draw_rect_3d(surface, self.color_bg_dark, self.color_bg_light, pygame.Rect(5, 300, 5 * 15 + 5, 14 * 15),
                     width=2)

        self.paint_contact_mirrored(surface, (15, 315))
        draw_text3d(surface, self.color_bg_light, 'Ta', 22, (28, 315 + 40))

        self.paint_contact_mirrored(surface, (15, 420))
        draw_text3d(surface, self.color_bg_light, 'Tb', 22, (28, 420 + 40))

    def paint_contact(self, surface: pygame.Surface, pos: Point) -> None:
        """
        Draw a standard contact element at the specified position.

        Args:
            surface (pygame.Surface): The surface to draw on.
            pos (tuple): Position (x, y) for the contact.
        """
        self.paint_holes(surface, pos)
        x, y = pos
        rect = pygame.Rect(x + 16, y - 13, 15, 11)
        pygame.draw.rect(surface, self.color_bg_light, rect, width=0)
        pygame.draw.rect(surface, (0, 0, 0), (x + 17, y - 12, 13, 9), width=0)
        pygame.draw.line(surface, self.color_bg_dark, rect.topleft, rect.topright - pygame.Vector2(2, 0), width=1)
        pygame.draw.line(surface, self.color_bg_dark, rect.topleft, rect.bottomleft - pygame.Vector2(0, 2), width=1)

    def paint_contact_mirrored(self, surface: pygame.Surface, pos: Point) -> None:
        """
        Draw a mirrored contact element at the specified position.

        Args:
            surface (pygame.Surface): The surface to draw on.
            pos (tuple): Position (x, y) for the contact.
        """
        self.paint_holes(surface, pos)
        x, y = pos
        rect = pygame.Rect(x + 16, y + 17, 15, 11)
        pygame.draw.rect(surface, self.color_bg_light, rect, width=0)
        pygame.draw.rect(surface, (0, 0, 0), (x + 17, y + 18, 13, 9), width=0)
        pygame.draw.line(surface, self.color_bg_dark, rect.topleft, rect.topright - pygame.Vector2(2, 0), width=1)
        pygame.draw.line(surface, self.color_bg_dark, rect.topleft, rect.bottomleft - pygame.Vector2(0, 2), width=1)

    def paint_holes(self, surface: Surface, pos: Tuple[int, int], ) -> Tuple[int, int]:
        """
        Paint three contact holes at the specified position.
        Args:
            surface: The surface to draw on.
            pos: The position (x, y) for the contact.
        """
        draw_hole(surface, self.color_bg_light, pos + pygame.Vector2(7, 7))
        draw_hole(surface, self.color_bg_light, pos + pygame.Vector2(7 + 15, 7))
        draw_hole(surface, self.color_bg_light, pos + pygame.Vector2(7 + 30, 7))

    # ------------------------------------------- Draw Sliders -------------------------------------------------

    def paint_sliders(self, surface: pygame.Surface) -> None:
        """
        Draw all slider controls on the board.

        Args:
            surface (pygame.Surface): The board surface to draw on.
        """
        for n, x in enumerate(range(10 * 15, 10 * 15 + 10 * 7 * 15, 7 * 15)):
            self.paint_slider_top(surface, x)
            self.paint_slider_bottom(surface, x)

            draw_text3d(surface, self.color_bg_light, f'{n}', 28, (x + 30, 850))

            # Hole for button
        pygame.draw.rect(surface, (0, 0, 0), (31, 824, *self.size_button), width=0)

    def paint_slider_top(self, surface: pygame.Surface, x: int) -> None:
        """
        Draw the top portion of a slider at the specified x position.

        Args:
            surface (pygame.Surface): The surface to draw on.
            x (int): X-coordinate for the slider position.
        """
        for x1 in [x - 6, x + 12]:
            y = 285
            pygame.draw.rect(surface, (0, 0, 0), (x1, y, 10, 28), width=0)
            pygame.draw.rect(surface, self.color_button_medium, (x1 + 3, y, 7, 25), width=0)
            pygame.draw.line(surface, self.color_bg_light, (x1 + 10, y), (x1 + 10, y) - pygame.Vector2(10, 0), width=1)
            pygame.draw.line(surface, self.color_bg_light, (x1 + 10, y), (x1 + 10, y) + pygame.Vector2(0, 25), width=1)

            draw_text3d(surface, self.color_bg_light, 'a', FONT_SIZE_A_B, (x - 20, y + 8))
            draw_text3d(surface, self.color_bg_light, 'b', FONT_SIZE_A_B, (x + 24, y + 8))

    def paint_slider_bottom(self, surface: pygame.Surface, x: int) -> None:
        """
        Draw the bottom portion of a slider at the specified x position.

        Args:
            surface (pygame.Surface): The surface to draw on.
            x (int): X-coordinate for the slider position.
        """
        y = 780
        pygame.draw.rect(surface, (0, 0, 0), (x, y, SIZE, 12 * SIZE + 14), width=0)
        pygame.draw.rect(surface, self.color_button_medium, (x + 1, y + 1, 13, 7 * SIZE), width=0)

    def paint_hud(self, surface: pygame.Surface) -> None:
        """
        Draw the part of the hud left and right from the lamps
        Args:
            surface: The Logikus surface

        Returns:
            None

        """
        w = 5 * SIZE
        pygame.draw.rect(surface, self.color_hud, (1, 0, w - 2, 10 * SIZE - 2), width=0)

        w = int((1.8) * SIZE)

        pygame.draw.rect(surface, self.color_hud, (SIZE_PATCHBOARD[0] - w + 2, 0, w - 3, 10 * SIZE - 2), width=0)


# ---------------------------------- Safe loading of windows icon fromm resources -----------------------

def load_icon() -> None | pygame.Surface:
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
