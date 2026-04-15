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

import os
from datetime import datetime
from typing import Tuple, Dict

import pygame
from pygame import Surface

from logikus.assets import Assets, SKIN_CLASSIC, load_standard_font
from logikus.logic import Logic, ON
from logikus.wiring import Wiring, Wire, Contact

# --------------------------------------------- States -------------------------------------------------

STATE_IDLE = 0
STATE_REDRAWING = 1
STATE_QUITTING = 2

MODE_NORMAL = 0
MODE_WIRING = 1


# -------------------------------------------- Ui -------------------------------------------------


class Ui:

    def __init__(self, surface: Surface, logic: Logic, skin=SKIN_CLASSIC, rows: int = 68, cols: int = 77,
                 grid_size: int = 15) -> None:

        """
        Initialize the UI for the Logikus emulator.

        Args:
            surface (Surface): The Pygame surface where the UI will be drawn.
            logic (Logic): The logic controller for the emulator, handling the game state.
            skin: The visual skin/theme for the emulator.
            rows (int): Number of rows in the grid.
            cols (int): Number of columns in the grid.
        """

        self.surface = surface
        self.logic = logic
        self.cols = cols
        self.rows = rows
        self.grid_size = grid_size
        self.grid_visible = False

        self.assets = Assets(skin)
        self.components = {}
        self.contacts: Dict[str, Contact] = {}
        self.wiring = Wiring()
        self.mouse_position = None
        self.colors_wire = self.assets.skin["wire"]
        self.color_wire_active = 0
        self.color_wire_live = self.assets.skin["live_wire"]

        self.board = self.assets.images['board']

        self.lamps = []
        self.sliders = []
        self.menu = Menu()

        self.init_contacts()
        self.init_sliders()
        self.init_lamps()
        self.button = self.init_button()
        self.init_menu()
        self.color_picker = self.init_active_color_box()

        self.label = self.init_labels()
        self.label_names = []

    # -------------------------- Management of wire colors ----------------------------------

    @property
    def wire_colors(self):
        """
        Get the list of available wire colors.

        Returns:
            list: List of RGB color tuples for wires.
        """
        return self.assets.skin['wire']

    @property
    def active_wire_color(self):
        """
        Returns the active color for wires
        Returns: the current color for wires
        """
        return self.colors_wire[self.color_wire_active]

    def cycle_wire_color(self, direction: int = 1) -> None:
        """
        Cycles through the indices of available wire colors.

        Args:
            direction (int): Direction to cycle (-1 for backward, 1 for forward). Defaults to 1.
        """
        self.color_wire_active = (self.color_wire_active + direction) % len(self.colors_wire)
        self.color_picker.color = self.colors_wire[self.color_wire_active]
        if self.wiring.wire:
            self.wiring.wire.color = self.color_wire_active

    # -----------------------------------------------------------------------

    def init_contacts(self):
        """
        Initialize all contact points on the patchboard.

        Creates contacts for sliders (S0-S9), lamps (L0-L9), power source (Q),
        and button connections (Ta, Tb) with their respective grid positions.
        """
        # Contacts S0a0 - S9K2 of the patchboard
        offset_col, offset_row = 8, 21

        for c in range(10):
            for r, row_name in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K']):
                for s, side in enumerate(['a', 'b']):
                    for hole in [0, 1, 2]:
                        id_ = f'S{c}{row_name}{side}.{hole}'
                        col = offset_col + 7 * c + 4 * s
                        row = offset_row + 3 * r + hole
                        self.add_contact(id_, row, col)

        # Contacts for the Lamps L0 - L9

        for l in range(10):
            for hole in [0, 1, 2]:
                id_ = f'L{l}.{hole}'
                col, row = 9 + 7 * l + hole, 12
                self.add_contact(id_, row, col)

        # Contacts for the power source Q

        for hole in [0, 1, 2]:
            id_ = f'Q.{hole}'
            col, row = hole + 1, 12
            self.add_contact(id_, row, col)

        # Contacts for the button T

        for hole in [0, 1, 2]:
            id_ = f'Ta.{hole}'
            col, row = hole + 1, 21
            self.add_contact(id_, row, col)

            id_ = f'Tb.{hole}'
            col, row = hole + 1, 28
            self.add_contact(id_, row, col)

    def add_contact(self, id_, row, col):
        """
        Add a contact at the specified grid position.

        Args:
            id_ (str): Unique identifier for the contact.
            row (int): Row position in the grid.
            col (int): Column position in the grid.
        """
        x, y = self.rc_to_xy(row, col)
        contact = Contact(id_, x, y)
        self.components[(row, col)] = contact
        self.contacts[contact.id] = contact

    def init_sliders(self):
        """
        Initialize all slider components and their grid positions.

        Creates 10 sliders (S0-S9) and registers them in the components map.
        """
        for number in range(10):
            col, row = 9 + 7 * number, 57
            pos = self.rc_to_xy(row, col)
            slider = Slider(f'S{number}', self.assets.images['slider'], pos)

            self.sliders.append(slider)
            for c in range(col, col + 3):
                for r in range(row - 5, row + 5):
                    self.components[(r, c)] = slider

    def init_button(self):
        """
        Initialize the button component and its grid positions.

        Returns:
            Button: The initialized button instance.
        """
        col, row = 2, 55
        button = Button('T', self.assets.images['button'], self.rc_to_xy(row, col))
        for c in range(col, col + 3):
            for r in range(row, row + 7):
                self.components[(r, c)] = button
        return button

    def init_lamps(self):
        """
        Initialize all lamp components and their grid positions.

        Creates 10 lamps (L0-L9) with on/off images and registers them in the components map.
        """
        for l in range(10):
            col = 7 + 7 * l
            row = 0
            image_on, image_off = (self.assets.images[f'L{l}_on'], self.assets.images[f'L{l}_off'])
            lamp = Lamp(f'L{l}', image_on, image_off, self.rc_to_xy(row, col))
            self.lamps.append(lamp)
            for c in range(col, col + 7):
                for r in range(row, row + 10):
                    self.components[(r, c)] = lamp

    def init_menu(self):
        """
        Initialize all menu items and their grid positions.

        Creates menu items (New, Open, Save, Quit) and registers them in the components map.
        """
        for n, (name, image) in enumerate(
                zip(["New", "Open", "Save", "Quit"], ["menu_new", "menu_open", "menu_save", "menu_quit"])):
            item = MenuItem(name, self.assets.images[image], (self.grid_size, (2 * n + 1) * self.grid_size))
            self.menu.add_item(item)
            for c in range(0, 7):
                self.components[(2 * n + 1, c)] = item
                self.components[(2 * n + 2, c)] = item

    def init_active_color_box(self):
        """
        Initialize the color picker for wire color selection.

        Returns:
            ColorPicker: The initialized color picker instance.
        """
        box = ColorPicker(color=self.active_wire_color, size=self.grid_size)
        return box

    def init_labels(self):
        """
        Initialize the labels area and its grid positions.

        Creates a surface for rendering labels on the patchboard.

        Returns:
            pygame.Surface: The labels surface.
        """
        labels = pygame.Surface((70 * self.grid_size, self.grid_size))
        for c in range(9, 9 + 70):
            self.components[(51, c)] = labels
        return labels

    @property
    def width(self):
        """
        Get the total width of the UI in pixels.

        Returns:
            int: Width calculated from columns and grid size.
        """
        return self.grid_size * self.cols

    @property
    def height(self):
        """
        Get the total height of the UI in pixels.

        Returns:
            int: Height calculated from rows and grid size.
        """
        return self.grid_size * self.rows

    def slider(self, number):
        """
        Get a slider by its number.

        Args:
            number (int): Slider number (0-9).

        Returns:
            Slider: The slider instance, or None if not found.
        """
        for slider in self.sliders:
            if slider.name == f'S{number}':
                return slider
        return None

    def lamp(self, number):
        """
        Get a lamp by its number.

        Args:
            number (int): Lamp number (0-9).

        Returns:
            Lamp: The lamp instance, or None if not found.
        """
        for lamp in self.lamps:
            if lamp.name == f'L{number}':
                return lamp
        return None

    def component_at_xy(self, pos):
        """
        Get the component at the specified pixel position.

        Args:
            pos (tuple): Pixel position (x, y).

        Returns:
            Component: The component at the position, or None.
        """
        return self.component_at(*self.xy_to_rc(pos))

    def component_at(self, col, row):
        """
        Get the component at the specified grid position.

        Args:
            col (int): Column index.
            row (int): Row index.

        Returns:
            Component: The component at the position, or None.
        """
        return self.components.get((col, row))

    def rc_to_xy(self, row, col):
        """
        Convert grid coordinates to pixel coordinates.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            tuple: Pixel coordinates (x, y).
        """
        return col * self.grid_size, row * self.grid_size

    def xy_to_rc(self, pos):
        """
        Convert pixel coordinates to grid coordinates.

        Args:
            pos (tuple): Pixel coordinates (x, y).

        Returns:
            tuple: Grid coordinates (row, col).
        """
        x, y = pos
        return y // self.grid_size, x // self.grid_size

    def set_labels(self, labels):
        """
        Set the label names for display.

        Args:
            labels (list): List of label strings.
        """
        self.label_names = labels

    @property
    def mode(self):
        """
        Get the current UI mode.

        Returns:
            int: MODE_WIRING if a wire is being created, otherwise MODE_NORMAL.
        """
        if self.wiring.wire:
            return MODE_WIRING
        else:
            return MODE_NORMAL

    # -------------------------------------------- Wiring -------------------------------------------------

    def put_wire(self, wire: Wire):
        """
        Add a wire to the UI and update the logic connections.

        Args:
            wire (Wire): The wire to add.
        """
        self.wiring.add_wire(wire)
        if wire.start and wire.end:
            self.logic.add_connection([wire.start.name, wire.end.name])
        else:
            raise ValueError("Wire start and end must be defined to add a connection to logic.")

    def get_wire(self, contact1, contact2) -> Wire:
        """
        Get a wire connecting two contacts.

        Args:
            contact1: First contact.
            contact2: Second contact.

        Returns:
            Wire: The wire connecting the contacts, or None.
        """
        return self.wiring.wire_between(contact1, contact2)

    def remove_wire(self, wire: Wire):
        """
        Remove a wire from the UI and update the logic connections.

        Args:
            wire (Wire): The wire to remove.
        """
        self.wiring.remove_wire(wire)
        if wire.start and wire.end:
            self.logic.remove_connection([wire.start.name, wire.end.name])
        else:
            raise ValueError("Wire start and end must be defined to remove a wire.")

    def remove_wiring(self):
        """
        Remove all wires from the UI.
        """
        for wire in self.wiring.wires[:]:
            self.remove_wire(Wire(wire.start, wire.end))

    # --------------------------------------------  Update-------------------------------------------------

    def update(self):
        """
        Update all UI components to reflect the current logic state.

        Synchronizes slider positions, lamp states, and button state with the logic engine.
        """
        for slider in self.sliders:
            slider.state = (self.logic.sliders[slider.name].position == 'y')
        for lamp in self.lamps:
            lamp.state = (self.logic.lamps[lamp.name].state == ON)
        self.button.state = (self.logic.button.state == ON)

    # -------------------------------------------- Drawing -------------------------------------------------

    def draw(self):
        """
        Draw the complete UI on the surface.

        Renders the board, all components, wiring, labels, and menu as needed.
        """
        self.surface.blit(self.board, (0, 0))

        for slider in self.sliders:
            slider.draw(self.surface)
        for lamp in self.lamps:
            lamp.draw(self.surface)
        self.button.draw(self.surface)
        self.draw_wiring()
        self.draw_labels()
        self.draw_menu()
        self.draw_color_picker()

        if self.grid_visible:
            self.draw_grid()

    def draw_labels(self):
        """
        Draw the label texts on the board.
        """
        font = load_standard_font(14)
        for n, label in enumerate(self.label_names):
            text = font.render(label, True, (0, 0, 0))
            x_offset = (7 * self.grid_size - text.get_width()) // 4
            self.surface.blit(text, (8 * self.grid_size + 7 * n * self.grid_size + x_offset, 51 * self.grid_size - 1))

    def draw_wiring(self):
        """
        Draw all wires and live wire paths.
        """
        for wire in self.wiring.wires:
            self.draw_wire(wire, color=self.colors_wire[wire.color])

        for wire in self.wiring.live_wires():
            self.draw_wire(wire, color=self.color_wire_live)

        if self.wiring.wire:
            pygame.draw.lines(self.surface, self.active_wire_color, False, self.wiring.wire.path, 5)

    def draw_wire(self, wire: Wire, color: Tuple[int, int, int]) -> None:
        """
        Draw a single wire with the specified color.

        Args:
            wire (Wire): The wire to draw.
            color (Tuple[int, int, int]): RGB color for the wire.
        """
        pygame.draw.lines(self.surface, color, False, wire.path, width=5)

        for p in wire.path[1:-1]:  # round edges with circles
            pygame.draw.circle(self.surface, color, p, 2)

    def draw_menu(self) -> None:
        """
        Draw the menu if it is visible.
        """
        if self.menu.visible:
            for item in self.menu.items:
                self.surface.blit(item.image, item.rect.topleft)

    def draw_color_picker(self) -> None:

        """
        Draws the color picker.
        """
        if self.color_picker.visible:
            self.surface.blit(self.color_picker.image,
                              pygame.Vector2(self.color_picker.pos) - pygame.Vector2(self.grid_size, self.grid_size))

    def draw_grid(self) -> None:
        """
        Draw the grid overlay for debugging.
        """
        for contact in self.contacts.values():
            pygame.draw.rect(self.surface, (0, 0, 255), contact.rect, width=2)

        for x in range(0, self.width, self.grid_size):
            pygame.draw.line(self.surface, (200, 200, 200), (x, 0), (x, self.height), width=1)
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self.surface, (200, 200, 200), (0, y), (self.width, y), width=1)

    def screenshot(self) -> None:
        """
        Save a screenshot of the current UI to a file.
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"screenshot-{timestamp}.png"
        path = os.path.join(".", filename)
        pygame.image.save(self.surface, path)

    def snap_to_grid(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Snap a pixel position to the nearest grid point.

        Args:
            pos (Tuple[int, int]): Pixel position (x, y).

        Returns:
            Tuple[int, int]: Snapped grid position.
        """
        x, y = pos
        grid_x = (x // self.grid_size) * self.grid_size + self.grid_size // 2
        grid_y = (y // self.grid_size) * self.grid_size + self.grid_size // 2
        return grid_x, grid_y

    # -------------------------------------------- Saving and Loading -------------------------------------------------

    def save_project(self, path: str = 'projects/'):
        """
        Save the current project wiring to a file.

        Args:
            path (str): Directory path to save the wiring file.
        """
        file = f'{path}/wiring.lkw'
        with open(file, 'w') as f:
            for wire in self.wiring.wires:
                f.write(f'{wire.write()}\n')
        pass

    def load_project(self, path: str = 'projects/00 Basic/') -> None:
        """
        Load a complete project including wiring, lamps, and labels.

        Args:
            path (str): Directory path of the project to load.
        """
        self.load_wiring(path + "/" + 'wiring.lkw')
        self.load_insert(path + "/" + 'insert.png')
        self.load_labels(path + "/" + 'labels.txt')

    def load_insert(self, path: str = 'projects/00 Basic/insert.png') -> None:
        """
        Load custom lamp images from a file.

        Args:
            path (str): Path to the lamp image file.
        """
        if os.path.exists(path):
            self.assets.load_insert(path)
            self.init_lamps()

    def set_lamps(self, lamps):
        """
        Set the states of all lamps.

        Args:
            lamps: List of lamp states (True for ON, False for OFF).
        """
        for n, state in enumerate(lamps):
            lamp = self.lamp(n)
            if lamp:
                lamp.state = state

    def load_wiring(self, path_str: str) -> None:
        """
        Load wiring configuration from a file.

        Args:
            path_str (str): Path to the wiring file.
        """
        if os.path.exists(path_str):
            with open(path_str, 'r') as f:
                for line in f:
                    contacts, path_str = line.strip().split(' : ') if ' : ' in line else (line.strip(), None)

                    start_end, color = contacts.split(' ') if ' ' in contacts else (contacts, '0')

                    start, end = start_end.split('-')
                    start_contact = self.contacts.get(start)
                    end_contact = self.contacts.get(end)

                    wire = Wire(start_contact, end_contact, int(color))
                    if start_contact:
                        wire.path = [start_contact.center]
                    else:
                        raise ValueError("Start connection must be defined.")
                    if path_str:
                        for point in path_str.split('-'):
                            x, y = point.strip().strip('()').split(',')
                            wire.path.append((int(x), int(y)))
                    if end_contact:
                        wire.path.append(end_contact.center)
                    else:
                        raise ValueError("End connection must be defined.")
                    self.put_wire(wire)

    def load_labels(self, path: str) -> None:
        """
        Load label configuration from a file.

        Args:
            path (str): Path to the labels file.
        """
        if os.path.exists(path):
            with open(path, 'r', encoding='Utf-8') as f:
                self.label_names = f.readline().strip().split(';')
        else:
            self.label_names = []

    # -------------------------------------------- Representations -------------------------------------------------

    def __repr__(self) -> str:
        contacts_count = len(self.contacts) if getattr(self, "contacts", None) is not None else 0
        wiring = getattr(self, "wiring", None)
        wires = getattr(wiring, "wires", []) if wiring is not None else []
        wires_count = len(wires)
        sliders_count = len(self.sliders) if getattr(self, "sliders", None) is not None else 0
        lamps_count = len(self.lamps) if getattr(self, "lamps", None) is not None else 0
        active = getattr(getattr(self, "active_contact", None), "id", None)
        board_present = bool(getattr(self, "board", None))
        resources_info = None
        resources = getattr(self, "resources", None)
        if resources is not None:
            resources_info = getattr(resources, "skin", None) or getattr(resources, "name", None)

        return (
            f"Ui(cols={getattr(self, 'cols', '?')}, rows={getattr(self, 'rows', '?')}, "
            f"grid_size={getattr(self, 'grid_size', '?')}, contacts={contacts_count}, "
            f"wires={wires_count}, sliders={sliders_count}, "
            f"lamps={lamps_count}, active_contact={active}, board={board_present}, "
            f"resources={resources_info})"
        )

    def __str__(self) -> str:
        """
        Return a concise, readable description of the Ui state.
        """
        contacts_count = len(self.contacts) if getattr(self, "contacts", None) is not None else 0
        wires_count = len(getattr(getattr(self, "wiring", None), "wires", []))
        sliders_count = len(self.sliders) if getattr(self, "sliders", None) is not None else 0
        lamps_count = len(self.lamps) if getattr(self, "lamps", None) is not None else 0
        active = getattr(getattr(self, "active_contact", None), "id", None)
        return (
            f"Ui(cols={self.cols}, rows={self.rows}, grid_size={self.grid_size}, "
            f"contacts={contacts_count}, wires={wires_count}, "
            f"sliders={sliders_count}, lamps={lamps_count}, active_contact={active})"
        )


# -------------------------------------------- Slider -------------------------------------------------

class Slider:
    """
    UI slider (switch) used on the Logikus patchboard.

    Attributes:
        name (str): Identifier of the slider (e.g. 'S0').
        image (pygame.Surface): Surface used to draw the slider.
        _rect_off (pygame.Rect): Rect when the slider is in the 'off' position.
        _rect_on (pygame.Rect): Rect when the slider is in the 'on' position.
        state (bool): Current position state; True means 'on' (moved up), False means 'off'.
    """

    def __init__(self, name: str, image: Surface, pos: Tuple[int, int] = (0, 0)) -> None:
        """
        Initialize the slider sprite and compute its on/off rectangles.

        Args:
            name: Slider identifier.
            image: Image surface for the slider.
            pos: Top-left position for the 'off' rect; the 'on' rect is offset vertically.
        """
        super().__init__()
        self.name = name
        self.image = image
        # rectangle shown in the 'off' position (base position)
        self._rect_off = self.image.get_rect(topleft=pos)
        # rectangle shown in the 'on' position (visual offset upwards)
        self._rect_on = self.image.get_rect(topleft=(pos[0], pos[1] - 70))
        self.state = False

    @property
    def rect(self) -> pygame.Rect:
        """
        Return the current pygame.Rect for rendering based on state.

        Returns:
            pygame.Rect: _rect_on when state is True, otherwise _rect_off.
        """
        return self._rect_on if self.state else self._rect_off

    def move(self) -> None:
        """
        Toggle the slider's state between on and off.
        """
        self.state = not self.state

    def draw(self, surface: Surface) -> None:
        """
        Draw the slider on the given surface.
        
        Args:
            surface (pygame.Surface): The surface to draw the slider on.
        """
        surface.blit(self.image, self.rect.topleft)

    def __repr__(self) -> str:
        """
        Short debug representation showing name and boolean state.
        """
        return f"Slider {self.name} -> {self.state}"

    def __str__(self) -> str:
        """
        Short representation showing name and boolean state.
        """
        return f"Slider {self.name} -> {self.state}"


# -------------------------------------------- Button -------------------------------------------------

class Button:
    """
    UI button sprite used on the Logikus patchboard.

    Attributes:
        name (str): Button identifier (e.g. 'T').
        image (pygame.Surface): Surface used to draw the button.
        rect (pygame.Rect): Rectangle used for positioning the button on the screen.
        state (bool): Visual state of the button; True means pressed/ON, False means released/OFF.
    """

    def __init__(self, name: str, image: Surface, pos: Tuple[int, int] = (0, 0)) -> None:
        """
        Initialize the Button sprite.

        Args:
            name: Identifier for the button.
            image: Surface used to render the button.
            pos: Top-left position (x, y) for the button's rect.
        """
        super().__init__()
        self.name = name
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.state = False

    def draw(self, surface: Surface) -> None:
        """
        Draw the button on the given surface.

        When pressed, the image is drawn with a small offset to simulate depression.
        """
        if self.state:
            # slight visual offset when button is pressed
            surface.blit(self.image, (self.rect.topleft[0] + 2, self.rect.topleft[1] - 2))
        else:
            surface.blit(self.image, self.rect.topleft)

    def __repr__(self) -> str:
        """
        Short debug representation showing name and boolean state.

        Returns:
            str: Debug representation of the button.
        """
        return f"Button {self.name} -> {self.state}"

    def __str__(self) -> str:
        """
        Short representation showing name and boolean state.

        Returns:
            str: String representation of the button.
        """
        return f"Button {self.name} -> {self.state}"


# -------------------------------------------- Lamp -------------------------------------------------


class Lamp:
    """
    UI lamp sprite used on the Logikus patchboard.

    Attributes:
        name (str): Lamp identifier (e.g. 'L0').
        image_on (pygame.Surface): Surface displayed when the lamp is lit.
        image_off (pygame.Surface): Surface displayed when the lamp is off.
        rect (pygame.Rect): Rectangle used for positioning the lamp on the screen.
        state (bool): Visual state of the lamp; True means ON (lit), False means OFF.
    """

    def __init__(self, name: str, image_on: pygame.Surface, image_off: pygame.Surface, pos: Tuple[int, int] = (0, 0)):
        """
        Initialize a Lamp sprite.

        Args:
            name: Identifier for the lamp.
            image_on: Surface used when the lamp is ON.
            image_off: Surface used when the lamp is OFF.
            pos: Top-left position (x, y) for the lamp's rect.
        """
        super().__init__()
        self.name = name
        self.image_on = image_on
        self.image_off = image_off
        self.rect = image_on.get_rect(topleft=pos)
        self.state = False

    @property
    def image(self) -> pygame.Surface:
        """
        Return the currently active image according to the lamp state.

        Returns:
            pygame.Surface: image_on if state is True, otherwise image_off.
        """
        return self.image_on if self.state else self.image_off

    def __repr__(self) -> str:
        """
        Short debug representation showing name and boolean state.

        Returns:
            str: Debug representation of the lamp.
        """
        return f"Lamp {self.name} -> {self.state}"

    def draw(self, surface: Surface) -> None:
        """
        Draw the lamp on the given surface.

        Args:
            surface (pygame.Surface): The surface to draw the lamp on.
        """
        surface.blit(self.image, (self.rect.topleft[0] + 2, self.rect.topleft[1] - 2))

    def __str__(self) -> str:
        """
        Short representation showing name and boolean state.

        Returns:
            str: String representation of the lamp.
        """
        return f"Lamp {self.name} -> {self.state}"


class Label:
    """
    UI label sprite used on the Logikus patchboard.

    Attributes:
        name (str): Label identifier (e.g. 'L0').
        image (pygame.Surface): Surface used to draw the label.
        rect (pygame.Rect): Rectangle used for positioning the label on the screen.
    """

    def __init__(self, name: str, image: Surface, pos: Tuple[int, int] = (0, 0)) -> None:
        """
        Initialize the Label sprite.

        Args:
            name: Identifier for the label.
            image: Surface used to render the label.
            pos: Top-left position (x, y) for the label's rect.
        """
        super().__init__()
        self.name = name
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

    def __repr__(self) -> str:
        """
        Short debug representation showing name.
        
        Returns:
            str: Debug representation of the label.
        """
        return f"Label {self.name}"

    def __str__(self) -> str:
        """
        Short representation showing name.
        
        Returns:
            str: String representation of the label.
        """
        return f"Label {self.name}"


# ----------------------------------------- Active Color Box -------------------------------

class ColorPicker:
    """
    A color picker display element for wire color selection.
    
    Attributes:
        name (str): Identifier for the color picker.
        surface (pygame.Surface): Surface used to display the current color.
        color (tuple): Current color (RGB tuple).
        visible (bool): Whether the color picker is visible.
        pos (tuple): Position (x, y) for the color picker.
    """

    def __init__(self, color, size) -> None:
        """
        Initialize the ColorPicker.

        Args:
            color (tuple): Initial RGB color tuple.
            size (int): Size in pixels for the color picker square.
        """
        self.name = "active color"
        self.surface = pygame.Surface((3 * size, 3 * size))
        self.color = color
        self.visible = False
        self.pos = None

    @property
    def image(self):
        """
        Get the current color picker image.

        Returns:
            pygame.Surface: Surface displaying the current color with black border.
        """
        self.surface.fill(self.color)
        local_rect = self.surface.get_rect()  # (0,0,w,h)
        pygame.draw.rect(self.surface, (0, 0, 0), local_rect, 1)
        return self.surface

    def __repr__(self) -> str:
        """
        Short debug representation showing name, color, visibility, and position.

        Returns:
            str: Debug representation of the color picker.
        """
        return f"ColorPicker(name={self.name!r}, color={self.color}, visible={self.visible}, pos={self.pos})"


# -------------------------------------------- Menu and  MenuItem -------------------------------------------------

class MenuItem:
    """
    UI menu item sprite used in the Logikus application.

    Attributes:
        name (str): Menu item identifier (e.g. 'File', 'Edit').
        image (pygame.Surface): Surface used to draw the menu item.
        rect (pygame.Rect): Rectangle used for positioning the menu item on the screen.
    """

    def __init__(self, name: str, image: Surface, pos: Tuple[int, int] = (0, 0)) -> None:
        """
        Initialize the MenuItem sprite.

        Args:
            name: Identifier for the menu item.
            image: Surface used to render the menu item.
            pos: Top-left position (x, y) for the menu item's rect.
        """
        super().__init__()
        self.name = name
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

    def __repr__(self) -> str:
        """
        Short debug representation showing name.
        
        Returns:
            str: Debug representation of the menu item.
        """
        return f"MenuItem {self.name}"

    def __str__(self) -> str:
        """
        Short representation showing name.
        
        Returns:
            str: String representation of the menu item.
        """
        return f"MenuItem {self.name}"


class Menu:
    """
    UI menu sprite group used in the Logikus application.
    
    Attributes:
        visible (bool): Whether the menu is currently visible.
        items (list): List of MenuItem objects in the menu.
    """

    def __init__(self) -> None:
        """
        Initialize the Menu sprite group.
        """
        super().__init__()
        self.visible = False
        self.items = []

    def add_item(self, item: MenuItem) -> None:
        """
        Add a MenuItem to the menu.

        Args:
            item: MenuItem sprite to add to the menu.
        """
        self.items.append(item)

    def __repr__(self) -> str:
        """
        Short debug representation showing number of items.
        
        Returns:
            str: Debug representation of the menu.
        """
        return f"Menu with {len(self.items)} items"

    def __str__(self) -> str:
        """
        Short representation showing number of items.
        
        Returns:
            str: String representation of the menu.
        """
        return f"Menu with {len(self.items)} items"
