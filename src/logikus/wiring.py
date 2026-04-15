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

from typing import Tuple, List


# -------------------------------------------- Contact -------------------------------------------------

class Contact:
    """
    Element representing a single contact (hole) on the Logikus patchboard.

    Models a physical contact point that can be connected to exactly one other contact.
    It is used by the UI to draw and manage wiring between patchboard holes.
    Note: This class could inherit from pygame.Rect, however, I do not want this dependency
    in this module, so I implement only the necessary rectangle properties (esp. center) directly.
    """

    def __init__(self, id_: str, x: int, y: int, w: int = 15, h: int = 15) -> None:
        """
        Initialize a Contact instance.

        Args:
            id_ (str): Identifier of the contact (e.g. 'S0A-a-0' / 'L0-1' / 'Q-0').
            x (int): Top-left x coordinate in pixels.
            y (int): Top-left y coordinate in pixels.
            w (int): Width of the contact rectangle in pixels (default 15).
            h (int): Height of the contact rectangle in pixels (default 15).

        """
        self.rect = (x, y, w, h)

        self.id = id_
        self.connected_to = None
        self.active = False

    @property
    def name(self) -> str:
        """
        Return the base name of the contact.

        The base name is the portion of `id` before the first '-' character,
        e.g. for 'L0-1' this returns 'L0'.

        Returns:
            str: Base contact name.
        """
        return self.id.split('.')[0]

    @property
    def center(self) -> Tuple[int, int]:
        """
        Return the center point of the contact rectangle.

        Returns:
            tuple: (x, y) coordinates of the center point.
        """
        x, y, w, h = self.rect
        return int(x + w // 2), int(y + h // 2)

    @property
    def hole(self) -> int:
        """
        Return the hole index of the contact.

        The hole index is the numeric part after the '-' in `id`. This property
        converts that substring to an integer.

        Returns:
            int: Hole index (e.g. 0, 1, 2).
        """
        return int(self.id.split('.')[1])

    def connect(self, other_contact: Contact) -> None:
        """
        Connect this contact to another contact.

        This method records a reference to `other_contact` in `self.connected_to`.
        It does not perform validation (such as ensuring symmetry) — callers should
        manage mirrored connections when required.

        Args:
            other_contact (Contact): The contact to connect to.
        """
        self.connected_to = other_contact

    def disconnect(self) -> None:
        """
        Remove any existing connection from this contact.

        After calling this method `self.connected_to` will be None.
        """
        self.connected_to = None

    @property
    def empty(self) -> bool:
        """
        Check if the contact is unconnected.

        Returns:
            bool: True if not connected to any other contact, False otherwise.
        """
        return self.connected_to is None

    # ---------------------------------- String representations --------------------------

    def __repr__(self) -> str:
        """
        Return an unambiguous debug representation.

        Shows the contact name, hole index and the object currently connected to.
        """
        return f"Contact {self.name}-{self.hole}, connected to {self.connected_to}"

    def __str__(self) -> str:
        """
        Return a concise, human-readable representation.

        Delegates to __repr__ for consistent output.
        """
        return f"Contact {self.id}{' -> ' + self.connected_to.id if self.connected_to else ''}"


# -------------------------------------------- Wire ----------------------------------------------------

class Wire:
    """
    Element representing a wire connection between two contacts.

    A wire establishes a connection between two Contact objects and maintains
    a path (sequence of waypoints) representing how the wire is routed on the patchboard.
    """

    def __init__(self, start: Contact, end: Contact = None, color: int = 0) -> None:
        """
        Initialize a Wire instance.

        Args:
            start (Contact): The starting contact of the wire.
            end (Contact, optional): The ending contact of the wire (default None for dangling wires).
            color: the color of the wire in the UI
            
        Attributes:
            start (Contact): Starting contact.
            end (Contact): Ending contact.
            path (list): List of (x, y) coordinate tuples representing the wire routing path.
            active (bool): Whether the wire is currently active/conducting.
        """
        self.start = start
        self.end = end
        self.color = color
        self.path = []
        self.active = False

    def write(self) -> str:
        """
        Serialize the wire to a human-readable string format.

        Includes the start and end contact IDs, and the intermediate path points
        (excluding start and end points).

        Returns:
            str: Wire description in format 'start_id-end_id : (x1,y1) - (x2,y2) - ...'
        """
        text = f'{self.start.id}-{self.end.id} {self.color}'
        if self.path and len(self.path) > 2:
            text += (' : ' + ' - '.join(f'({x},{y})' for x, y in self.path[1:-1]))
        return text

    def __eq__(self, other: Wire) -> bool:
        """
        Check equality between two wires.

        Two wires are considered equal if they connect the same two contacts,
        regardless of direction (bidirectional comparison).

        Args:
            other (Wire): The wire to compare with.
            
        Returns:
            bool: True if both wires connect the same contacts, False otherwise.
        """
        return (self.start == other.start and self.end == other.end) or (
                self.start == other.end and self.end == other.start)

    # ---------------------------------- String representations --------------------------

    def __repr__(self) -> str:
        """
        Return a human-readable string representation of the wire.

        Shows the start and end contacts, and the complete routing path.
        For dangling wires (end is None), displays 'dangling' instead of end contact.

        Returns:
            str: String representation of the wire.
        """
        return f"Wire  {self.start.id} <-> {self.end.id if self.end else 'dangling'}, color: {self.color}, path: {self.path}"


# -------------------------------------------- Wiring -------------------------------------------------

class Wiring:
    """
    Container for managing all wires and their connections on the patchboard.

    This class maintains a collection of Wire objects, tracks the current active path,
    and provides methods to query and manipulate wire connections.
    """

    def __init__(self) -> None:
        """
        Initialize a Wiring instance.

        Attributes:
            wires (list): Collection of all Wire objects.
            path (list): Current signal propagation path through contacts.
            wire (Wire, optional): The currently selected or active wire.
        """
        self.wires = []
        self.path = None
        self.wire = None

    def wire_at(self, contact: Contact) -> Wire:
        """
        Find the first wire connected to a given contact.

        Args:
            contact (Contact): The contact to search for.
            
        Returns:
            Wire: The wire connected to the contact, or None if not found.
        """
        for wire in self.wires:
            if wire.start == contact or wire.end == contact:
                return wire
        return None

    def wire_between(self, contact1: Contact, contact2: Contact) -> Wire:
        """
        Find a wire connecting two contacts by their base names.

        Searches for a wire where either end has the specified contact names.
        Comparison is done using the 'name' property (base name before '-').

        Args:
            contact1 (str): Base name of first contact (e.g. 'L0').
            contact2 (str): Base name of second contact (e.g. 'S0A').
            
        Returns:
            Wire: The wire connecting the two contacts, or None if not found.
        """
        for wire in self.wires:
            if ((wire.start.name == contact1 and wire.end.name == contact2) or
                    (wire.start.name == contact2 and wire.end.name == contact1)):
                return wire
        return None

    def wire_in(self, contact: Contact) -> Wire:
        """
        Find a wire connected to a specific contact by exact ID.

        Args:
            contact (Contact): The contact to search for.
            
        Returns:
            Wire: The wire connected to the contact, or None if not found.
        """
        for wire in self.wires:
            if wire.start.id == contact.id or wire.end.id == contact.id:
                return wire
        return None

    def live_wires(self) -> List[Wire]:
        """
        Determine which wires are currently active in the signal path.

        Analyzes the current path and identifies all wires that form continuous
        connections through the path. Skips 'S' markers in the path.

        Returns:
            list: List of active Wire objects currently conducting in the path.
        """
        live_wires = []
        if self.path and len(self.path) > 1:
            for n in range(len(self.path) - 1):
                c1, c2 = self.path[n], self.path[n + 1]
                if c1 == "S":
                    continue
                live_wire = self.wire_between(c1, c2)
                if live_wire:
                    live_wires.append(live_wire)
        return live_wires

    def add_wire(self, wire: Wire) -> None:
        """
        Add a wire to the wiring and establish the connection.

        Connects the wire's start and end contacts to each other (bidirectional)
        and adds the wire to the collection.

        Args:
            wire (Wire): The wire to add.
        """
        wire.start.connect(wire.end)
        wire.end.connect(wire.start)
        self.wires.append(wire)

    def remove_wire(self, wire: Wire) -> None:
        """
        Remove a wire from the wiring and disconnect its contacts.

        Disconnects both ends of the wire from their respective contacts
        and removes the wire from the collection.

        Args:
            wire (Wire): The wire to remove.
        """
        for w in self.wires:
            if w == wire:
                wire.start.disconnect()
                wire.end.disconnect()
                self.wires.remove(w)
                return

    def clear(self) -> None:
        """
        Remove all wires from the wiring.

        Clears the wires collection completely. Note: Contact connections
        are not explicitly cleared by this method.
        """
        self.wires = []

    # ---------------------------------- String representations --------------------------
    def __repr__(self) -> str:
        """
        Return a string representation of all wires.

        Returns:
            str: Comma-separated list of wire representations.
        """
        return ', '.join(str(wire) for wire in self.wires)
