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

import pygame
from pygame.event import Event

from logikus.logic import Logic
from logikus.ui import Contact, Button, Slider, Lamp, MenuItem, STATE_IDLE, STATE_REDRAWING, STATE_QUITTING, \
    MODE_WIRING, MODE_NORMAL, Ui
from logikus.wiring import Wire


# ------------------------------------------ Controller ------------------------------------------------

class Controller:
    """
    Main controller class that handles user input and coordinates between UI and logic components.

    The Controller manages the application's event loop, processing mouse and keyboard events,
    and coordinating actions between the user interface (UI) and the underlying logic engine.
    It supports both normal operation mode and wiring mode for creating circuit connections.
    """

    def __init__(self, surface: pygame.Surface, ui_: Ui, logic: Logic) -> None:
        """
        Initialize the Controller with UI, logic, and surface components.

        Args:
            surface (pygame.Surface): The main display surface.
            ui_ (UI): The user interface instance.
            logic (Logic): The logic engine instance.

            
        Attributes:
            surface (pygame.Surface): The main display surface.
            logic (Logic): Reference to the logic engine.
        """
        self.ui = ui_
        self.logic = logic
        self.surface = surface
        self.state = STATE_IDLE

        self.current_path = 'projects'
        self.active_component = None

    # ------------------------------------------- Event Handling -------------------------------------------------

    UI_EVENTS = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.KEYDOWN, pygame.KEYUP]

    def handle_event(self, event: Event) -> int:
        """
        Main event handler that routes events based on current UI mode.

        Delegates event processing to either wiring mode or normal mode handlers
        depending on the current UI state.

        Args:
            event (pygame.Event): The pygame event to process.
            
        Returns:
            int: State change result (STATE_IDLE, STATE_REDRAWING, etc.).
        """
        if self.ui.mode == MODE_WIRING:
            return self.handle_event_wiring_mode(event)
        else:
            return self.handle_event_normal_mode(event)

    # ------------------------------------------- Wiring Mode Events-------------------------------------------------

    def handle_event_wiring_mode(self, event: Event) -> int:
        """
        Handle events specifically for wiring mode.

        In wiring mode, users can create and modify wire connections between contacts.
        Only mouse events are processed; keyboard events are ignored.

        Args:
            event (pygame.Event): The pygame event to process.
            
        Returns:
            int: State change result.
        """

        if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            # Cycle color of wire
            if event.key in [pygame.K_c] and event.type == pygame.KEYDOWN:
                self.ui.cycle_wire_color()
                return STATE_REDRAWING


            else:  # Ignore other keyboard events in wiring mode
                return STATE_IDLE

        wire = self.ui.wiring.wire

        # Handle mouse motion events to update the wiring path
        if event.type in [pygame.MOUSEMOTION]:
            wire.path[-1] = event.pos
            return STATE_REDRAWING

        # Handle right mouse button to cancel the last segment or exit wiring mode
        if event.type in [pygame.MOUSEBUTTONDOWN] and event.button == 3:
            if len(wire.path) > 2:
                wire.path[-2] = self.ui.snap_to_grid(event.pos)
                del wire.path[-1]
            else:
                self.ui.mouse_position = None
                self.ui.wiring.wire = None
                self.state = STATE_IDLE
            return STATE_REDRAWING

        # Handle left mouse button to create a connection
        if event.type in [pygame.MOUSEBUTTONDOWN]:
            component = self.ui.component_at_xy(event.pos)
            if component and isinstance(component, Contact) and component != self.ui.wiring.wire.start:
                if component.empty:
                    wire.end = component
                    wire.path[-1] = component.center
                    self.ui.put_wire(wire)
                    self.logic.compute()
                    self.ui.mouse_position = None
                    self.ui.wiring.wire = None
                    self.state = STATE_IDLE
                    return STATE_REDRAWING

            if component is None:
                wire.path[-1] = self.ui.snap_to_grid(event.pos)
                wire.path.append(event.pos)
                return STATE_REDRAWING

        return STATE_IDLE

    # ------------------------------------------- Normal Mode Events-------------------------------------------------

    def handle_event_normal_mode(self, event: Event) -> int:
        """
        Handle events for normal operation mode.

        In normal mode, all UI events are processed including mouse, keyboard,
        and component interactions.

        Args:
            event (pygame.Event): The pygame event to process.
            
        Returns:
            int: State change result.
        """
        if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            return self.handle_key_event(event)

        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            return self.handle_mouse_button_event(event)

        if event.type in [pygame.MOUSEMOTION] and self.ui.mode == MODE_NORMAL:
            return self.handle_mouse_motion_event(event)

        return STATE_IDLE

    # --------------------------- Mouse Motion Events-------------------------------------------------

    def handle_mouse_motion_event(self, event: Event) -> int:
        """
        Handle mouse movement events in normal mode.

        Updates UI state based on mouse position, including component hovering,
        cursor changes, and path visualization for lamps.

        Args:
            event (pygame.Event): The mouse motion event.
            
        Returns:
            int: State change result.
        """
        pos = event.pos
        component = self.ui.component_at_xy(pos)
        if component is None:
            if self.active_component is not None:
                self.ui.menu.visible = False
                self.ui.color_picker.visible = False
                self.ui.wiring.path = None
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                return STATE_REDRAWING  # always redrawing...
            else:
                self.ui.mouse_position = pos
                return STATE_REDRAWING

        self.active_component = component

        if isinstance(component, Contact):
            return STATE_IDLE

        if isinstance(component, Slider):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
            return STATE_IDLE

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        if isinstance(component, MenuItem):
            self.ui.menu.visible = True
            return STATE_REDRAWING

        if isinstance(component, Lamp):
            self.ui.wiring.path = self.logic.lamps[component.name].path
            return STATE_REDRAWING
        else:
            self.ui.wiring.path = None
            return STATE_REDRAWING

    # --------------------------------------- Mouse Button Events-------------------------------------------------

    def handle_mouse_button_event(self, event: Event) -> int:
        """
        Handle mouse button press and release events.

        Processes clicks on various UI components including contacts, sliders,
        buttons, lamps, and menu items.

        Args:
            event (pygame.Event): The mouse button event.
            
        Returns:
            int: State change result.
        """

        if event.button == 3:  # Right mouse button resets any started action
            self.ui.wiring.path = None
            self.ui.mouse_position = None
            self.ui.color_picker.visible = False
            self.state = STATE_IDLE
            return STATE_REDRAWING

        if event.button in [4, 5]:  # Mouse wheel opens pop up color picker at mouse position
            self.ui.color_picker.visible = True
            self.ui.color_picker.pos = event.pos
            self.ui.cycle_wire_color(1 if event.button == 4 else -1)
            return STATE_REDRAWING

        if event.type == pygame.MOUSEBUTTONDOWN and self.ui.color_picker.visible:
            self.ui.color_picker.visible = False
            return STATE_REDRAWING

        component = self.ui.component_at_xy(event.pos)

        # Ignore mouse button up events when no component is clicked
        if not component and event.type == pygame.MOUSEBUTTONUP:
            return STATE_IDLE

        if not component and event.type == pygame.MOUSEBUTTONDOWN and self.active_component is not None:
            return STATE_IDLE

        # A contact is clicked, wiring mode begins
        if isinstance(component, Contact) and event.type == pygame.MOUSEBUTTONDOWN:
            contact = component
            if contact.empty:  # empty contact, begin wiring mode with new wire
                self.ui.wiring.wire = Wire(contact, color=self.ui.color_wire_active)
                self.ui.wiring.wire.path = [contact.center, contact.center]
            else:  # Contact with wire is clicked - begin wiring mode with existing wire
                wire = self.ui.wiring.wire_in(contact)  # identify clicked wire
                self.ui.remove_wire(wire)
                self.logic.compute()

                if contact == wire.start:  # reverse wire if necessary
                    wire.start, wire.end = wire.end, wire.start
                    wire.path = wire.path[::-1]

                wire.path[-1] = event.pos
                self.ui.wiring.wire = wire
                wire.color = self.ui.color_wire_active  # active color replaces old color
                return STATE_REDRAWING
            return STATE_REDRAWING

        # ------------------ Handling of Slider, Buttons, Menu  and lamps ------------------------

        if isinstance(component, Slider) and event.type == pygame.MOUSEBUTTONDOWN:
            self.logic.move_slider(component.name)
            return STATE_REDRAWING

        if isinstance(component, Button) and event.type == pygame.MOUSEBUTTONDOWN:
            self.logic.push_button()
            return STATE_REDRAWING

        if isinstance(component, Button) and event.type == pygame.MOUSEBUTTONUP:
            self.logic.release_button()
            return STATE_REDRAWING

        if isinstance(component, Lamp) and event.type == pygame.MOUSEBUTTONDOWN:
            path = dialog_choose_file("Loading insert for lamps...", default_path=self.current_path)
            if path:
                self.ui.load_insert(path)
                return STATE_REDRAWING
            else:
                return STATE_IDLE

        if component == self.ui.label_names and event.type == pygame.MOUSEBUTTONDOWN:
            return self.do_load_labels()

        if isinstance(component, MenuItem) and event.type == pygame.MOUSEBUTTONDOWN:
            return self.handle_clicked_menu_item(component)

        return STATE_IDLE

    def do_load_wiring(self):
        """
        Load wiring configuration from a file.

        Opens a file dialog to select a wiring file and loads it into the UI.

        Returns:
            int: STATE_REDRAWING if successful, STATE_IDLE otherwise.
        """
        file = dialog_choose_file('Load wiring from file?', default_path=self.current_path)
        if file is not None:
            self.ui.remove_wiring()
            self.ui.load_wiring(file)
            self.logic.compute()
            return STATE_REDRAWING
        else:
            return STATE_IDLE

    def do_load_labels(self):
        """
        Load label configuration from a file.

        Opens a file dialog to select a labels file and loads it into the UI.

        Returns:
            int: STATE_REDRAWING if successful, STATE_IDLE otherwise.
        """
        file = dialog_choose_file('Load labels from file?', default_path=self.current_path)
        if file is not None:
            self.ui.load_labels(file)
            return STATE_REDRAWING
        else:
            return STATE_IDLE

    # -------------------------------------- Menu Item Events-------------------------------------------------

    def handle_clicked_menu_item(self, menu_item: MenuItem) -> int:
        """
        Handle clicks on menu items.

        Processes different menu actions including New, Open, Save, and Quit.

        Args:
            menu_item (MenuItem): The clicked menu item.
            
        Returns:
            int: State change result.
        """
        if menu_item.name == "New":
            result = dialog_query("Delete all wires?", "Do you really want to remove all wires?")
            if result == 'yes':
                self.ui.remove_wiring()
                for slider in self.logic.sliders.values():
                    slider.position = 0
                self.logic.compute()
                return STATE_REDRAWING
            return STATE_IDLE

        if menu_item.name == "Open":
            path = dialog_choose_dir("Open project...", default_path=self.current_path)
            if path:
                self.current_path = path + '/'
                self.ui.remove_wiring()
                self.ui.load_project(self.current_path)
                self.logic.compute()
                return STATE_REDRAWING
            return STATE_IDLE

        if menu_item.name == "Save":
            path = dialog_choose_dir("Save Project...", default_path=self.current_path)
            if path:
                self.current_path = path + '/'
                self.ui.save_project(self.current_path)
                return STATE_REDRAWING
            return STATE_IDLE

        if menu_item.name == "Quit":
            result = dialog_query("Quit?", "Do you really want to quit?")
            if result == 'yes':
                return STATE_QUITTING
            else:
                return STATE_IDLE

        return STATE_IDLE

    # -------------------------------- Keyboard Events----------------------------------------------

    BUTTON_EVENTS = [pygame.K_b, pygame.K_t, pygame.K_SPACE]
    SLIDER_EVENTS = list(range(pygame.K_0, pygame.K_9 + 1))

    def handle_key_event(self, event: Event) -> int:
        """
        Handle keyboard events for various shortcuts and controls.

        Processes key presses for sliders (0-9), button control (B, T, Space),
        screenshots (P), debugging (L), and grid visibility (G).

        Args:
            event (pygame.Event): The keyboard event.
            
        Returns:
            int: State change result.
        """
        key, event_type = event.key, event.type
        # Moving the sliders
        if key in self.SLIDER_EVENTS and event_type == pygame.KEYDOWN:
            slider = f'S{(key - pygame.K_0 - 1) % 10}'
            self.logic.move_slider(slider)
            return STATE_REDRAWING

        # Pressing and releasing the button
        if key in self.BUTTON_EVENTS and event_type == pygame.KEYDOWN:
            self.logic.push_button()
            return STATE_REDRAWING

        if key in self.BUTTON_EVENTS and event_type == pygame.KEYUP:
            self.logic.release_button()
            return STATE_REDRAWING

        # Taking a screenshot with 'p'
        if key in [pygame.K_p] and event_type == pygame.KEYDOWN:
            self.ui.screenshot()
            return STATE_IDLE

        if key in [pygame.K_l] and event_type == pygame.KEYDOWN:
            print(self.ui.logic)
            return STATE_IDLE

        # Toggling grid visibility with 'g'
        if key in [pygame.K_g]:
            self.ui.grid_visible = (event_type == pygame.KEYDOWN)
            return STATE_REDRAWING

        return STATE_IDLE


# ------------------------------------------- Dialogs -------------------------------------------------

from tkinter import Tk, filedialog, messagebox


def dialog_choose_file(title: str, default_path: str = 'projects/') -> str:
    """
    Open a file selection dialog using tkinter.

    Displays a native file open dialog allowing the user to select a file.
    The dialog is hidden from view and only the file selection window appears.

    Args:
        title (str): The title text for the file dialog window.
        default_path (str): The initial directory to open the dialog in.
                           Defaults to 'projects/'.

    Returns:
        str: The selected file path, or empty string if canceled.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title=title, defaultextension='png', initialdir=default_path)
    return file_path


def dialog_choose_dir(title: str, default_path: str = 'projects/') -> str:
    """
    Open a directory selection dialog using tkinter.

    Displays a native directory selection dialog allowing the user to choose a folder.
    The dialog is hidden from view and only the directory selection window appears.

    Args:
        title (str): The title text for the directory dialog window.
        default_path (str): The initial directory to open the dialog in.
                           Defaults to 'projects/'.

    Returns:
        str: The selected directory path, or empty string if canceled.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    path = filedialog.askdirectory(title=title, initialdir=default_path)
    return path


def dialog_query(title: str, text: str) -> str:
    """
    Display a yes/no question dialog using tkinter.

    Shows a modal message box with Yes/No buttons for user confirmation.
    The dialog is hidden from view and only the message box appears.

    Args:
        title (str): The title text for the message box.
        text (str): The question text to display in the message box.

    Returns:
        str: 'yes' if user clicked Yes, 'no' if user clicked No.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    result = messagebox.askquestion(title, text)
    return result
