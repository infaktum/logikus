"""
Logikus - A Python Emulation of the Logikus Puzzle Computer

Board rendering, UI components, hit testing and project file I/O.

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

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

import pygame
from pygame import Surface, Rect

from logikus.assets import Assets, Point, RGB, SIZE, SKINS, Skin, load_standard_font
from logikus.logic import Logic, ON
from logikus.wiring import Wiring, Wire, Contact

# --------------------------------------------- States -------------------------------------------------

STATE_IDLE = 0
STATE_REDRAWING = 1
STATE_QUITTING = 2

MODE_NORMAL = 0
MODE_WIRING = 1

N_LAMPS = 10  # Number of Lamps
N_COLS = 10  # Number of columns

GridPosition: TypeAlias = tuple[int, int]  # (row, column)


# -------------------------------------------- Ui -------------------------------------------------


class Ui:
    """Render the board and coordinate graphical components with the circuit model.

    Components are indexed by (row, column); contacts additionally by physical
    IDs such as ``S0Aa.0``. ``update()`` copies model state into the controls,
    while ``draw()`` paints the current view without presenting the window.

    Project I/O includes wires, labels and an optional original lamp insert.
    Slider/button positions and the selected skin are not persisted.
    """

    surface: Surface
    logic: Logic
    cols: int
    rows: int
    grid_size: int
    grid_visible: bool
    contacts_visible: bool
    skin_name: str
    skin: Skin
    assets: Assets
    wiring: Wiring
    colors_wire: list[RGB]
    color_wire_active: int
    color_wire_live: RGB
    board: Surface
    menu: Menu
    button: Button
    color_picker: ColorPicker
    label: Surface

    def __init__(self, surface: Surface, logic: Logic, skin: str | Skin = "classic", rows: int = 68, cols: int = 77,
                 grid_size: int = 15) -> None:

        """
        Initialize the UI for the Logikus emulator.

        Args:
            surface: The Pygame surface where the UI will be drawn.
            logic: The logic controller for the emulator, handling the game state.
            skin: Registered skin name or matching legacy skin dictionary.
                Unknown values fall back to the classic skin.
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.
            grid_size: Cell size in pixels. Board artwork still contains fixed
                coordinates, so this does not provide arbitrary UI scaling.

        Pygame fonts and a display must be initialized before creating the UI.
        """

        self.surface = surface
        self.logic = logic
        self.cols = cols
        self.rows = rows
        self.grid_size = grid_size
        self.grid_visible = False
        self.contacts_visible = False

        # Accept both skin names and legacy skin dicts.
        if isinstance(skin, str) and skin in SKINS:
            self.skin_name = skin
        else:
            self.skin_name = next((name for name, skin_data in SKINS.items() if skin_data == skin), "classic")

        self.skin = SKINS[self.skin_name]
        self.assets = Assets(skin_name=self.skin_name)
        self.components: dict[GridPosition, Component] = {}
        self.contacts: dict[str, Contact] = {}
        self.wiring = Wiring()
        self.mouse_position: Point | None = None
        self.colors_wire = self.assets.skin["wire"]
        self.color_wire_active = 0
        self.color_wire_live = self.assets.skin["live_wire"]

        self.board = self.assets.images['board']

        self.lamps: list[Lamp] = []
        self.sliders: list[Slider] = []
        self.menu = Menu()

        self.init_contacts()
        self.init_sliders()
        self.init_lamps()
        self.button = self.init_button()
        self.init_menu()
        self.color_picker = self.init_active_color_box()

        self.label = self.init_labels()
        self.label_names: list[str] = []

    def cycle_skin(self) -> None:
        """Select the next registered skin, wrapping back to the first."""
        skin_names = list(SKINS.keys())
        current_index = skin_names.index(self.skin_name) if self.skin_name in SKINS else -1
        next_skin_name = skin_names[(current_index + 1) % len(skin_names)]
        self.set_skin(next_skin_name)

    def set_skin(self, skin_name: str) -> None:
        """Replace graphics, preserving contacts, wires, labels and the insert.

        Args:
            skin_name: Registered skin name; unknown names select classic.

        Existing control objects remain valid and are synchronized with the
        logic. Wire color indices are preserved and mapped during rendering.
        """
        skin_name = skin_name if skin_name in SKINS else "classic"
        assets = Assets(skin_name=skin_name)
        if self.assets.insert is not None:
            assets.set_insert(self.assets.insert)

        self.skin_name = skin_name
        self.skin = SKINS[self.skin_name]
        self.assets = assets
        self.colors_wire = self.assets.skin["wire"]
        self.color_wire_active %= len(self.colors_wire)
        self.color_wire_live = self.assets.skin["live_wire"]
        self.board = self.assets.images['board']

        # Keep object identities so wires and the controller retain valid references.
        for slider in self.sliders:
            slider.image = self.assets.images['slider']
        self.button.image = self.assets.images['button']
        self._update_lamp_images()
        menu_images = {'New': 'menu_new', 'Open': 'menu_open',
                       'Save': 'menu_save', 'Quit': 'menu_quit'}
        for item in self.menu.items:
            item.image = self.assets.images[menu_images[item.name]]
        self.color_picker.color = self.active_wire_color
        self.update()

    # -------------------------- Management of wire colors ----------------------------------

    @property
    def wire_colors(self) -> list[RGB]:
        """
        Get the list of available wire colors.

        Returns:
            list: List of RGB color tuples for wires.
        """
        return self.assets.skin['wire']

    @property
    def active_wire_color(self) -> RGB:
        """
        Return the RGB color selected for drawing or editing a wire.
        """
        return self.colors_wire[self.color_wire_active]

    def cycle_wire_color(self, direction: int = 1) -> None:
        """
        Cycles through the indices of available wire colors.

        Args:
            direction: Direction to cycle (-1 for backward, 1 for forward). Defaults to 1.
        """
        self.color_wire_active = (self.color_wire_active + direction) % len(self.colors_wire)
        self.color_picker.color = self.colors_wire[self.color_wire_active]
        if self.wiring.wire:
            self.wiring.wire.color = self.color_wire_active

    # -----------------------------------------------------------------------

    def init_contacts(self) -> None:
        """
        Initialize all contact points on the patchboard.

        Creates contacts for sliders (S0-S9), lamps (L0-L9), power source (Q),
        and button connections (Ta, Tb) with their respective grid positions.
        """
        # Physical contact IDs range from S0Aa.0 to S9Kb.2.
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

    def add_contact(self, id_: str, row: int, col: int) -> None:
        """
        Add a contact at the specified grid position.

        Args:
            id_: Unique identifier for the contact.
            row: Row position in the grid.
            col: Column position in the grid.
        """
        x, y = self.rc_to_xy(row, col)
        contact = Contact(id_, x, y)
        self.components[(row, col)] = contact
        self.contacts[contact.id] = contact

    def init_sliders(self) -> None:
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

    def init_button(self) -> Button:
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

    def init_lamps(self) -> None:
        """
        Initialize all lamp components and their grid positions.

        Creates 10 lamps (L0-L9), or refreshes existing lamps on repeated calls.
        """
        if self.lamps:
            self._update_lamp_images()
            return
        for l in range(10):
            col = 7 + 7 * l
            row = 0
            image_on, image_off = (self.assets.images[f'L{l}_on'], self.assets.images[f'L{l}_off'])
            lamp = Lamp(f'L{l}', image_on, image_off, self.rc_to_xy(row, col))
            lamp.state = self.logic.lamps[lamp.name].state == ON
            self.lamps.append(lamp)
            for c in range(col, col + 9):
                for r in range(row, row + 10):
                    self.components[(r, c)] = lamp

    def init_menu(self) -> None:
        """
        Initialize all menu items and their grid positions.

        Creates menu items (New, Open, Save, Quit) and registers them in the components map.
        """
        for n, (name, image) in enumerate(
                zip(["New", "Open", "Save", "Quit"], ["menu_new", "menu_open", "menu_save", "menu_quit"])):
            item = MenuItem(name, self.assets.images[image], (self.grid_size, (2 * n + 1) * self.grid_size))
            self.menu.add_item(item)
            for c in range(0, 7):
                self.components[(2 * n + 0, c + 1)] = item
                self.components[(2 * n + 1, c + 1)] = item

    def init_active_color_box(self) -> ColorPicker:
        """
        Initialize the color picker for wire color selection.

        Returns:
            ColorPicker: The initialized color picker instance.
        """
        box = ColorPicker(color=self.active_wire_color, size=self.grid_size)
        return box

    def init_labels(self) -> Surface:
        """
        Initialize the labels area and its grid positions.

        Register a surface as the label area's hit-test target. Label text is
        rendered directly onto the UI surface by ``draw_labels()``.

        Returns:
            pygame.Surface: The labels surface.
        """
        labels = pygame.Surface((70 * self.grid_size, self.grid_size))
        for c in range(9, 9 + 70):
            self.components[(51, c)] = labels
        return labels

    @property
    def width(self) -> int:
        """
        Get the total width of the UI in pixels.

        Returns:
            int: Width calculated from columns and grid size.
        """
        return self.grid_size * self.cols

    @property
    def height(self) -> int:
        """
        Get the total height of the UI in pixels.

        Returns:
            int: Height calculated from rows and grid size.
        """
        return self.grid_size * self.rows

    def slider(self, number: int) -> Slider | None:
        """
        Get a slider by its number.

        Args:
            number: Slider number (0-9).

        Returns:
            Slider: The slider instance, or None if not found.
        """
        for slider in self.sliders:
            if slider.name == f'S{number}':
                return slider
        return None

    def lamp(self, number: int) -> Lamp | None:
        """
        Get a lamp by its number.

        Args:
            number: Lamp number (0-9).

        Returns:
            Lamp: The lamp instance, or None if not found.
        """
        for lamp in self.lamps:
            if lamp.name == f'L{number}':
                return lamp
        return None

    def component_at_xy(self, pos: Point) -> Component | None:
        """
        Get the component at the specified pixel position.

        Args:
            pos: Pixel position (x, y).

        Returns:
            Component: The component at the position, or None.
        """
        return self.component_at(*self.xy_to_rc(pos))

    def component_at(self, col: int, row: int) -> Component | None:
        """
        Get the component at the specified grid position.

        Args:
            col: Row index (historical parameter name retained for callers).
            row: Column index (historical parameter name retained for callers).

        Returns:
            Component: The component at the position, or None.
        """
        return self.components.get((col, row))

    def rc_to_xy(self, row: int, col: int) -> Point:
        """
        Convert grid coordinates to pixel coordinates.

        Args:
            row: Row index.
            col: Column index.

        Returns:
            tuple: Pixel coordinates (x, y).
        """
        return col * self.grid_size, row * self.grid_size

    def xy_to_rc(self, pos: Point) -> GridPosition:
        """
        Convert pixel coordinates to grid coordinates.

        Args:
            pos: Pixel coordinates (x, y).

        Returns:
            tuple: Grid coordinates (row, col).
        """
        x, y = pos
        return y // self.grid_size, x // self.grid_size

    def set_labels(self, labels: list[str]) -> None:
        """
        Store the supplied label list by reference for subsequent drawing.

        Args:
            labels: List of label strings.
        """
        self.label_names = labels

    @property
    def mode(self) -> int:
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

    def put_wire(self, wire: Wire) -> None:
        """
        Add a wire to the UI and update the logic connections.

        Args:
            wire: The wire to add.

        Raises:
            ValueError: The wire has no start or end contact.

        Updates model connections but does not recompute lamp states.
        """
        self.wiring.add_wire(wire)
        if wire.start and wire.end:
            self.logic.add_connection([wire.start.name, wire.end.name])
        else:
            raise ValueError("Wire start and end must be defined to add a connection to logic.")

    def get_wire(self, contact1: str, contact2: str) -> Wire | None:
        """
        Find the first wire between two electrical contact names, in either direction.

        Args:
            contact1: First base name without hole suffix, e.g. ``Q``.
            contact2: Second base name, e.g. ``S0Aa``.

        Returns:
            Wire: The wire connecting the contacts, or None.
        """
        return self.wiring.wire_between(contact1, contact2)

    def remove_wire(self, wire: Wire) -> None:
        """
        Remove a wire from the UI and update the logic connections.

        Args:
            wire: The wire to remove.

        Raises:
            ValueError: An endpoint or the corresponding model connection is missing.

        Updates model connections but does not recompute lamp states.
        """
        self.wiring.remove_wire(wire)
        if wire.start and wire.end:
            self.logic.remove_connection([wire.start.name, wire.end.name])
        else:
            raise ValueError("Wire start and end must be defined to remove a wire.")

    def remove_wiring(self) -> None:
        """
        Remove completed wires from the UI and model; do not recompute lamps.

        The in-progress wire and highlighted path are not reset here.
        """
        for wire in self.wiring.wires[:]:
            self.remove_wire(Wire(wire.start, wire.end))

    # --------------------------------------------  Update-------------------------------------------------

    def update(self) -> None:
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

    def draw(self) -> None:
        """
        Draw the complete UI on the surface.

        Renders the board, all components, wiring, labels, and menu as needed.
        """
        self.surface.blit(self.board, (0, 0))

        self.draw_lamps_and_sliders()
        self.draw_labels()
        self.button.draw(self.surface)
        self.draw_wiring()
        self.draw_menu()
        self.draw_color_picker()

        if self.grid_visible:
            self.draw_grid()

        if self.contacts_visible:
            self.draw_slider_contacts()

    def draw_lamps_and_sliders(self) -> None:
        """
        Draw existing slider and lamp objects using their current visual states.

        """
        for slider in self.sliders:
            slider.draw(self.surface)
        for lamp in self.lamps:
            lamp.draw(self.surface)

    def draw_labels(self) -> None:
        """
        Draw the label texts on the board.
        """
        font = load_standard_font(14)
        for n, label in enumerate(self.label_names):
            text = font.render(label, True, (0, 0, 0))
            x_offset = (7 * self.grid_size - text.get_width()) // 4
            self.surface.blit(text, (8 * self.grid_size + 7 * n * self.grid_size + x_offset, 51 * self.grid_size - 1))

    def draw_wiring(self) -> None:
        """
        Draw completed wires, the highlighted signal path and any wire being edited.

        Stored color indices wrap within the current skin's palette.
        """
        for wire in self.wiring.wires:
            # Map at render time so returning to a larger palette restores colors.
            self.draw_wire(wire, color=self.colors_wire[wire.color % len(self.colors_wire)])

        for wire in self.wiring.live_wires():
            self.draw_wire(wire, color=self.color_wire_live)

        if self.wiring.wire:
            pygame.draw.lines(self.surface, self.active_wire_color, False, self.wiring.wire.path, 5)

    def draw_wire(self, wire: Wire, color: RGB) -> None:
        """
        Draw a single wire with the specified color.

        Args:
            wire: Wire with at least two path points.
            color: RGB color for the wire.
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
        Draw the color picker when visible; its position must be set beforehand.
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

    def draw_slider_contacts(self) -> None:
        """
        Draw the active contacts for debugging. The contact which are connected by the slider position are highlighted.
        """
        w, h = 5 * SIZE, 3 * SIZE
        y_offset = 21 * SIZE
        for slider in self.sliders:
            x = slider.rect.left - SIZE
            for y in range(10):
                if y % 2 != slider.state:
                    pygame.draw.rect(self.surface, self.assets.skin["live_wire"], Rect(x, y * h + y_offset, w, h),
                                     width=3)

    def screenshot(self) -> None:
        """
        Save a screenshot of the current UI to a file. The file is stored as screenshot-<timestamp>.png in the working directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"screenshot-{timestamp}.png"
        path = os.path.join(".", filename)
        pygame.image.save(self.surface, path)

    def snap_to_grid(self, pos: Point) -> Point:
        """
        Return the integer center of the grid cell containing the pixel position.

        Args:
            pos: Pixel position (x, y).

        Returns:
            Point: Snapped grid position.
        """
        x, y = pos
        grid_x = (x // self.grid_size) * self.grid_size + self.grid_size // 2
        grid_y = (y // self.grid_size) * self.grid_size + self.grid_size // 2
        return grid_x, grid_y

    # -------------------------------------------- Saving and Loading -------------------------------------------------

    def save_project(self, path: str | Path = 'projects/') -> None:
        """
        Save wiring, UTF-8 labels, and the original optional lamp insert.

        Writes ``wiring.lkw`` and ``labels.txt``, overwriting existing files.
        Writes ``insert.png`` when an original insert is present; otherwise
        removes an existing insert file. The three writes are not transactional.
        Labels use semicolons as separators and must not contain separators or
        line breaks. The skin and switch states are not stored.

        Args:
            path: Project directory, created if necessary.

        Raises:
            OSError: A directory or file cannot be created, written or removed.
            pygame.error: The insert cannot be encoded as a PNG image.
        """
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / 'wiring.lkw').open('w', encoding='utf-8') as f:
            for wire in self.wiring.wires:
                f.write(f'{wire.write()}\n')
        (directory / 'labels.txt').write_text(';'.join(self.label_names) + '\n', encoding='utf-8')
        insert_path = directory / 'insert.png'
        if self.assets.insert is not None:
            pygame.image.save(self.assets.insert, str(insert_path))
        else:
            # An older insert must not reappear when this project is loaded.
            insert_path.unlink(missing_ok=True)

    def load_project(self, path: str | Path = 'projects/00 Basic/') -> None:
        """
        Load wiring, an optional lamp insert and labels from a project directory.

        Wiring is appended to existing connections; callers must clear it first
        when replacing a project. A missing insert restores default lamp images,
        and missing labels clear the label list. Lamp logic is not recomputed.
        Loading is incremental: a later error does not undo earlier changes.

        Args:
            path: Directory path of the project to load.

        Raises:
            OSError: An existing project file cannot be read.
            ValueError: Wiring syntax, contact IDs or insert dimensions are invalid.
            pygame.error: The insert image cannot be loaded or processed.
        """
        directory = Path(path)
        self.load_wiring(directory / 'wiring.lkw')
        if (directory / 'insert.png').is_file():
            self.load_insert(directory / 'insert.png')
        else:
            self.assets.set_lamps()
            self._update_lamp_images()
        self.load_labels(directory / 'labels.txt')

    def load_insert(self, path: str | Path = 'projects/00 Basic/insert.png') -> None:
        """
        Load and scale an insert, refreshing existing lamp images and states.

        A missing file leaves the current insert unchanged. The original image
        is retained for project saves. Lamp objects and contact mappings survive.

        Args:
            path: Path to the lamp image file.

        Raises:
            OSError: The image file cannot be read.
            ValueError: Image or lamp dimensions cannot accommodate the borders.
            pygame.error: Pygame cannot decode or convert the image.
        """
        if os.path.exists(path):
            self.assets.load_insert(path)
            self._update_lamp_images()

    def _update_lamp_images(self) -> None:
        """Refresh images and visual states from assets and logic, preserving lamp objects."""
        for lamp in self.lamps:
            lamp.image_on = self.assets.images[f'{lamp.name}_on']
            lamp.image_off = self.assets.images[f'{lamp.name}_off']
            lamp.state = self.logic.lamps[lamp.name].state == ON

    def set_lamps(self, lamps: Iterable[bool]) -> None:
        """
        Set visual lamp states in order without modifying the circuit model.

        Missing states leave lamps unchanged; entries after L9 are ignored.
        A subsequent ``update()`` restores the model's lamp states.

        Args:
            lamps: List of lamp states (True for ON, False for OFF).
        """
        for n, state in enumerate(lamps):
            lamp = self.lamp(n)
            if lamp:
                lamp.state = state

    def load_wiring(self, path_str: str | Path) -> None:
        """
        Append wire connections and routed paths from an existing text file.

        Each line contains ``start_id-end_id [color]`` with an optional
        `` : (x,y) - (x,y)`` path suffix. IDs include physical hole suffixes,
        e.g. ``Q.0-L0.0 2``. Missing colors default to zero. Missing files are
        ignored. Blank lines and malformed records are not accepted.
        Existing wires are retained and lamp states are not recomputed.

        Args:
            path_str: Path to the wiring file.

        Raises:
            OSError: The file cannot be opened or read.
            ValueError: A record is malformed or references an unknown contact.

        Records loaded before an error remain in the UI and model.
        """
        if os.path.exists(path_str):
            with open(path_str, 'r') as f:
                for line in f:
                    contacts, path_text = line.strip().split(' : ') if ' : ' in line else (line.strip(), None)

                    start_end, color = contacts.split(' ') if ' ' in contacts else (contacts, '0')

                    start, end = start_end.split('-')
                    start_contact = self.contacts.get(start)
                    end_contact = self.contacts.get(end)

                    wire = Wire(start_contact, end_contact, int(color))
                    if start_contact:
                        wire.path = [start_contact.center]
                    else:
                        raise ValueError("Start connection must be defined.")
                    if path_text:
                        for point in path_text.split('-'):
                            x, y = point.strip().strip('()').split(',')
                            wire.path.append((int(x), int(y)))
                    if end_contact:
                        wire.path.append(end_contact.center)
                    else:
                        raise ValueError("End connection must be defined.")
                    self.put_wire(wire)

    def load_labels(self, path: str | Path) -> None:
        """
        Replace labels with the semicolon-separated first line of a UTF-8 file.

        An empty first line or a missing file clears the labels. Line endings
        are removed; other whitespace and empty fields between separators remain.

        Args:
            path: Path to the labels file.

        Raises:
            OSError: An existing file cannot be opened or read.
            UnicodeError: The file is not valid UTF-8.
        """
        if os.path.exists(path):
            with open(path, 'r', encoding='Utf-8') as f:
                line = f.readline().rstrip('\r\n')
                self.label_names = line.split(';') if line else []
        else:
            self.label_names = []

    # -------------------------------------------- Representations -------------------------------------------------

    def __repr__(self) -> str:
        """Return diagnostic counts, tolerating partially initialized UI objects."""
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
        name: Identifier of the slider (e.g. 'S0').
        image: Surface used to draw the slider.
        _rect_off: Rect when the slider is in the 'off' position.
        _rect_on: Rect when the slider is in the 'on' position.
        state: Current position state; True means 'on' (moved up), False means 'off'.
    """

    name: str
    image: Surface
    _rect_off: Rect
    _rect_on: Rect
    state: bool

    def __init__(self, name: str, image: Surface, pos: Point = (0, 0)) -> None:
        """
        Initialize the slider component and compute its on/off rectangles.

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
            surface: The surface to draw the slider on.
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
    UI button component used on the Logikus patchboard.

    Attributes:
        name: Button identifier (e.g. 'T').
        image: Surface used to draw the button.
        rect: Rectangle used for positioning the button on the screen.
        state: Visual state of the button; True means pressed/ON, False means released/OFF.
    """

    name: str
    image: Surface
    rect: Rect
    state: bool

    def __init__(self, name: str, image: Surface, pos: Point = (0, 0)) -> None:
        """
        Initialize the Button component.

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
    UI lamp component used on the Logikus patchboard.

    Attributes:
        name: Lamp identifier (e.g. 'L0').
        image_on: Surface displayed when the lamp is lit.
        image_off: Surface displayed when the lamp is off.
        rect: Rectangle used for positioning the lamp on the screen.
        state: Visual state of the lamp; True means ON (lit), False means OFF.
    """

    name: str
    image_on: Surface
    image_off: Surface
    rect: Rect
    state: bool

    def __init__(self, name: str, image_on: pygame.Surface, image_off: pygame.Surface, pos: Point = (0, 0)) -> None:
        """
        Initialize a Lamp component.

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
            surface: The surface to draw the lamp on.
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
    UI label component used on the Logikus patchboard.

    Attributes:
        name: Label identifier (e.g. 'L0').
        image: Surface used to draw the label.
        rect: Rectangle used for positioning the label on the screen.
    """

    name: str
    image: Surface
    rect: Rect

    def __init__(self, name: str, image: Surface, pos: Point = (0, 0)) -> None:
        """
        Initialize the Label component.

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
        name: Identifier for the color picker.
        surface: Surface used to display the current color.
        color: Current color (RGB tuple).
        visible: Whether the color picker is visible.
        pos: Pixel anchor, set before making the picker visible.
    """

    name: str
    surface: Surface
    color: RGB
    visible: bool
    pos: Point | None

    def __init__(self, color: RGB, size: int) -> None:
        """
        Initialize the ColorPicker.

        Args:
            color: Initial RGB color tuple.
            size: Grid cell size in pixels; the picker square is three cells wide.
        """
        self.name = "active color"
        self.surface = pygame.Surface((3 * size, 3 * size))
        self.color = color
        self.visible = False
        self.pos = None

    @property
    def image(self) -> Surface:
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
    UI menu item component used in the Logikus application.

    Attributes:
        name: Menu action name: 'New', 'Open', 'Save' or 'Quit'.
        image: Surface used to draw the menu item.
        rect: Rectangle used for positioning the menu item on the screen.
    """

    name: str
    image: Surface
    rect: Rect

    def __init__(self, name: str, image: Surface, pos: Point = (0, 0)) -> None:
        """
        Initialize the MenuItem component.

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
    UI menu container used in the Logikus application.
    
    Attributes:
        visible: Whether the menu is currently visible.
        items: List of MenuItem objects in the menu.
    """

    visible: bool
    items: list[MenuItem]

    def __init__(self) -> None:
        """
        Initialize the Menu container.
        """
        super().__init__()
        self.visible = False
        self.items = []

    def add_item(self, item: MenuItem) -> None:
        """
        Add a MenuItem to the menu.

        Args:
            item: MenuItem component to add to the menu.
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


# Values actually registered in Ui.components; annotations above are deferred.
Component: TypeAlias = Contact | Slider | Button | Lamp | MenuItem | Surface
