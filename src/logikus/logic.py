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

from __future__ import annotations

from typing import Tuple, List, Dict

# -------------------------------------- Constants --------------------------------------

Q = 'Q'
A, B, C, D, E, F, G, H, I, K = 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K'
S0, S1, S2, S3, S4, S5, S6, S7, S8, S9 = 'S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'
a, b, x, y = 'a', 'b', 'x', 'y'
ON, OFF = 'ON', 'OFF'
L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 = 'L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9'
LAMPS = [L0, L1, L2, L3, L4, L5, L6, L7, L8, L9]
SLIDERS = [S0, S1, S2, S3, S4, S5, S6, S7, S8, S9]


# -------------------------------------- LOGIKUS --------------------------------------

class Logic:
    """
    Represents the Logikus game computer.

    Attributes:
        button (Button): The push-button of the Logikus.
        lamps (Dict[str, Lamp]): Dictionary of lamps keyed by name.
        sliders (Dict[str, Slider]): Dictionary of sliders (switches) keyed by name.
        patchboard (Patchboard): The programming field containing wire and switch connections.
    """

    def __init__(self) -> None:
        """
        Initialize a new Logikus game computer instance.
        """
        self.button: Button = Button()
        self.lamps: Dict[str, Lamp] = {l: Lamp(l) for l in LAMPS}
        self.sliders: Dict[str, Slider] = {slider: Slider(slider) for slider in SLIDERS}
        self.patchboard: Patchboard = Patchboard(self.sliders, self.button)

    def add_connection(self, connection: List[str]) -> None:
        """
        Add a single wire connection to the programming field.

        Args:
            connection (List[str]): A list with two contact points to connect.
        """
        self.patchboard.put_connection(connection)

    def add_connections(self, connections: List[List[str]]) -> None:
        """
        Add multiple wire connections to the programming field.

        Args:
            connections (List[List[str]]): A list of connections.
        """
        for connection in connections:
            self.add_connection(connection)

    def remove_connection(self, connection: List[str]) -> None:
        """
        Remove a wire connection from the programming field.

        Args:
            connection (List[str]): A list with two contact points whose connection should be removed.
        """
        self.patchboard.remove_connection(connection)

    def move_slider(self, slider: str, position: str = None) -> None:
        """
        Move a slider (switch) to the given position or toggle it, then recompute lamp states.

        Args:
            slider (str): The name of the slider.
            position (str, optional): The new position of the slider (x or y). If None, the slider toggles.
        """
        if slider in self.sliders:
            self.sliders[slider].move(position)
            self.compute()

    def push_button(self) -> None:
        """
        Press the button and recompute lamp states.
        """
        self.button.push()
        self.compute()

    def release_button(self) -> None:
        """
        Release the button and recompute lamp states.
        """
        self.button.release()
        self.compute()

    def compute(self) -> None:
        """
        Update connections and set lamp states based on current connections.

        This updates the programming field's active connections (wires, sliders, button)
        and then searches for a path from the source `Q` to each lamp. Lamps with a
        found path are turned ON and store the path; others are turned OFF.
        """
        self.patchboard.sync_connections()
        for lamp in self.lamps.values():
            found, path = self.patchboard.find_path(Q, lamp.name)
            if found:
                lamp.on(path)
            else:
                lamp.off()

    def lamp_states(self) -> str:
        """
        Return a string describing the current lamp states.

        Returns:
            str: A string representation where 'o' means ON and '.' means OFF.
        """
        return "Lamps:\t\t" + ''.join('o' if lamp.state == ON else '.' for lamp in self.lamps.values())

    def slider_states(self) -> str:
        """
        Return a string describing the current slider positions.

        Returns:
            str: A string listing each slider position.
        """
        return "Sliders:\t" + ''.join(slider.position for slider in self.sliders.values())

    def __repr__(self) -> None:
        """
        Print lamp and slider states to the console (keeps original behavior).
        """
        print(self.lamp_states())
        print(self.slider_states())

    def __str__(self) -> str:
        """
        Return a string describing the full state of the Logikus instance.

        Returns:
            str: A multi-line string listing lamps, sliders and programming-field connections.
        """
        s = 'Lamps:\n' + ', '.join(str(lamp) for lamp in self.lamps.values())
        s += '\nSwitches:\n' + ','.join(str(slider) for slider in self.sliders.values())
        s += '\nDConnection:\n' + ', '.join(str(v) for v in self.patchboard.connections)
        return s


# --------------------------------- Patchboard --------------------------------------

class Patchboard:
    """
    Represents the programming field (patchboard) of the Logikus computer.

    The patchboard manages all electrical connections including wire connections,
    slider positions, and button states. It provides pathfinding functionality
    to determine if signals can flow between contacts.

    Attributes:
        connections (List[List[str]]): All currently active connections.
        wire_connections (List[List[str]]): Wire connections added by the user.
        slider (Dict[str, Slider]): Reference to all sliders.
        button (Button): Reference to the button.
    """

    def __init__(self, slider: Slider, button: Button) -> None:
        """
        Initialize a new patchboard instance.

        Args:
            slider (Dict[str, Slider]): Dictionary of all sliders.
            button (Button): The button instance.
        """
        self.connections: List[List[str]] = []
        self.wire_connections: List[List[str]] = []
        self.wire_connections: List[List[str]] = []
        self.slider: Dict[str, Slider] = slider
        self.button: Button = button

    def put_connection(self, connection: List[str]) -> None:
        """
        Add a single wire connection between two contacts.

        Creates bidirectional connections and updates the active connections.

        Args:
            connection (List[str]): List with two contact points to connect.
        """
        self.wire_connections.append(connection)
        self.wire_connections.append(connection[::-1])
        self.sync_connections()

    def put_connections(self, connections: List[List[str]]) -> None:
        """
        Add multiple wire connections.

        Args:
            connections (List[List[str]]): List of connection pairs to add.
        """
        for connection in connections:
            self.put_connection(connection)

    def remove_connection(self, verbindung: List[str]) -> None:
        """
        Remove a wire connection between two contacts.

        Removes both directions of the connection and updates active connections.

        Args:
            verbindung (List[str]): List with two contact points to disconnect.
        """
        self.wire_connections.remove(verbindung)
        self.wire_connections.remove(verbindung[::-1])
        self.sync_connections()

    def remove_connections(self) -> None:
        """
        Remove all wire connections from the patchboard.
        """
        self.wire_connections = []
        self.sync_connections()

    def sync_connections(self) -> None:
        """
        Update active connections based on current slider and button states.

        Combines wire connections with slider and button connections to create
        the complete list of currently active electrical connections.
        """
        self.connections = [v for slider in self.slider.values() for v in slider.connections]
        self.connections += self.button.connections
        self.connections += self.wire_connections

    def find_path(self, contact1: str, contact2: str, path: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Search for a connection path between two contacts using depth-first search.

        Args:
            contact1 (str): Starting contact name.
            contact2 (str): Target contact name.
            path (List[str], optional): Current search path. Defaults to None.

        Returns:
            Tuple[bool, List[str]]: (found, path) where found is True if a path exists,
                                   and path contains the contact sequence.
        """
        if path is None:
            path = [contact1]
        else:
            path.append(contact1)

        if contact1 == contact2:
            return True, path

        for v in self.connections:
            if v[0] == contact1 and v[1] not in path:
                found, new_path = self.find_path(v[1], contact2, path.copy())
                if found:
                    return True, new_path

        path.pop()
        return False, []

    def __str__(self) -> str:
        """
        Return a string representation of the patchboard's connections.

        Returns:
            str: Multi-line string showing all active connections and wire connections.
        """
        s = 'Programmierfeld Verbindungen:\n'
        s += '\n'.join(f'{v[0]} -> {v[1]}' for v in self.connections)
        s += '\nWire connections:\n'
        s += '\n'.join(str(wire) for wire in self.wire_connections)
        return s


# -------------------------------------- Lamp --------------------------------------

class Lamp:
    """
    Represents a single lamp in the Logikus game computer.

    Attributes:
        name (str): The lamp's identifier (e.g. 'L0').
        state (str): Current state, either ON or OFF.
        path (Optional[List[str]]): The connection path that lights this lamp, or None if off.
    """

    def __init__(self, name: str, state: str = OFF) -> None:
        """
        Initialize a Lamp.

        Args:
            name (str): The lamp name/identifier.
            state (str): Initial state (default is OFF).
        """
        self.name: str = name
        self.state: str = state
        # path stores the connection path (list of contact names) that led to the lamp being on
        self.path = None

    def on(self, path: List[str]) -> None:
        """
        Turn the lamp on and store the path that caused it.

        Args:
            path (List[str]): Connection path from the source to this lamp.
        """
        self.state = ON
        self.path = path

    def off(self) -> None:
        """
        Turn the lamp off and clear any stored path.
        """
        self.state = OFF
        self.path = None

    def __str__(self) -> str:
        """
        Return a human-readable representation of the lamp.

        Returns:
            str: A string describing the lamp name and its current state.
        """
        return f'Lamp {self.name} is {self.state}'


# -------------------------------------- Slider / Switch --------------------------------------


class Slider:
    """
    Represents a slider (switch) in the Logikus game computer.

    Attributes:
        name (str): The slider identifier (e.g. 'S0').
        position (str): Current position of the slider (x or y).
        connections_x (List[List[str]]): Connections active when the slider is in the x position.
        connections_y (List[List[str]]): Connections active when the slider is in the y position.
        connections (List[List[str]]): Currently active connections based on the slider position.
    """

    def __init__(self, name: str, position: str = x) -> None:
        """
        Initialize a Slider.

        Args:
            name (str): Slider name/identifier.
            position (str): Initial position (x or y). Defaults to x.
        """
        self.name: str = name
        self.position: str = position
        # connections for x-position (rows B, D, F, H, K)
        self.connections_x: List[List[str]] = \
            [
                [f'{name}{reihe}{s1}', f'{name}{reihe}{s2}'] for reihe in [B, D, F, H, K] for s1, s2 in
                [(a, b), (b, a)]
            ]
        # connections for y-position (rows A, C, E, G, I)
        self.connections_y: List[List[str]] = \
            [
                [f'{name}{reihe}{s1}', f'{name}{reihe}{s2}'] for reihe in [A, C, E, G, I] for s1, s2 in
                [(a, b), (b, a)]
            ]

        # set current connections according to initial position
        self.connections: List[List[str]] = self.connections_x if self.position == x else self.connections_y

    def move(self, position: str = None) -> None:
        """
        Move the slider to a given position or toggle if no position is provided.

        Args:
            position (str, optional): New position (x or y). If None, the slider toggles.
        """
        if position:
            self.position = position
        else:
            # toggle between x and y
            self.position = y if self.position == x else x
        # update active connections after moving
        self.connections = self.connections_x if self.position == x else self.connections_y

    def __str__(self) -> str:
        """
        Return a human-readable representation of the slider and its active connections.

        Returns:
            str: A string describing the slider name, position and active connections.
        """
        s = f'Slider {self.name} in position {self.position}\n'
        s += ', '.join(f'{c1}->{c2}' for c1, c2 in self.connections)
        return s


# -------------------------------------- Button --------------------------------------

T, Ta, Tb = 'T', 'Ta', 'Tb'


class Button:
    """
    Represents the button in the Logikus game computer.

    Attributes:
        name (str): The button's identifier (default 'T' for "Taster" = "Button").
        state (str): Current state, either ON or OFF.
        connections (List[List[str]]): Active connections while the button is pressed.
    """

    def __init__(self, name: str = T, state: str = OFF):
        """
        Initialize a Button.

        Args:
            name (str): Button name/identifier (default: T).
            state (str): Initial state (default OFF).
        """
        self.name: str = name
        self.state: str = state
        self.connections: List[List[str]] = []

    def push(self) -> None:
        """
        Press the button and establish connections.

        Sets the state to ON and creates the bidirectional connection between Ta and Tb.
        """
        self.state = ON
        self.connections = [[Ta, Tb], [Tb, Ta]]

    def release(self) -> None:
        """
        Release the button and remove connections.

        Sets the state to OFF and clears any active connections.
        """
        self.state = OFF
        self.connections = []

    def __str__(self) -> str:
        """
        Return a human-readable representation of the button.

        Returns:
            str: A string describing the button's name and current state.
        """
        return f'Button {self.name}: {self.state}'


# --------------------------------------- main --------------------------------------

def main() -> None:
    """
    Main demonstration function for the Logikus logic simulation.

    Creates a Logikus instance, adds a sample "Leuchtband" (light band) circuit,
    and demonstrates slider movements and their effects on lamp states.
    Prints the state after each change to show the simulation in action.
    """
    logic = Logic()
    leuchtband: List[List[str]] = [["Q", "S2Da"], ["S2Db", "S3Da"], ["S3Db", "L2"], ["S2Db", "S3Ea"],
                                   ["S3Eb", "L5"], ["Q", "S2Ca"], ["S2Cb", "S3Ca"], ["S3Cb", "L4"],
                                   ["S2Cb", "S3Ba"], ["S3Bb", "L3"]]

    logic.add_connections(leuchtband)
    logic.compute()
    print(logic)
    logic.move_slider(S3, y)
    print(logic)
    logic.move_slider(S2, y)
    print(logic)
    logic.move_slider(S3, x)
    print(logic)
    print()


# -----------------------------------------------------------------------

if __name__ == '__main__':
    main()
