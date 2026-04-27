Logikus User Guide
******************


Welcome to the User Guide of LOGIKUS, the toy computer emulation!

This guide will help you get started with LOGIKUS, providing step-by-step instructions and examples to make the most out of this educational tool. Whether you're a beginner or an experienced programmer, you'll find valuable information to enhance your understanding of computer architecture and programming concepts.


The History: What was LOGIKUS?
=========================

On LOGIKUS was a toy computer of the German company KOSMOS, which was sold in the 1960/70s. It was designed to teach children and beginners about the basics of computer architecture and programming. LOGIKUS featured a simple design with a limited set of instructions, making it an ideal tool for learning.

.. image:: images/Logikus_Box.jpg
    :alt: The LOGIKUS box, as it was sold in 1968.
    :align: center
    :width: 50%



To be frank: LOGIKUS was no computer at all, at least in the sense we are now talking of computers. It was more of a electro-mechanical device, where programming was done by putting wires into a patchboards, similar to a telephone switchboard. There were ten lamps on the top of the device, and the idea was to program the device in such a way that the lamps would light up when certain conditions were met. there were ten sliders on the bottom of the device, which were *not* linked to a specific lamp. However, moving them up and down would connect and disconnect the contacts on the patchboard, which in turn would affect the behavior of the lamps. The device was designed to be simple and intuitive, allowing users to experiment with different configurations and see the results immediately. Two accompanying booklets provided instructions and exercises to help users learn how to use the device effectively. LOGIKUS was a popular educational tool in its time, and it remains a nostalgic piece of computing history for many enthusiasts today.



..  image:: images/Logikus1.jpg
      :alt: The LOGIKUS device with its patchboard and lamps.
      :align: center
      :width: 50%



The Presence: Why this Emulation?
=========================




How to use the emulator
=======================

Core Interaction
----------------

- Connect contacts with wires.
- Toggle sliders S0-S9.
- Press button T.
- Observe lamp states L0-L9.

All interaction is possible using the mouse, but keyboard shortcuts are also available for faster operation.

Creating a wire connection
--------------------------

The most important part of the interaction is connecting contacts with wires. To do this, simply click on an empty contact to start a wire, then click on another empty contact to finish the connection.

Since having all wires going straight from one contact to another will make the wiring quickly very messy. It is possible to *bend* wires by clicking on intermediate points on the patchboard. This way you can form neat rectangular or diagonal paths between contact. Please not that the wires will *snap* to certain grid point, so it is not possible to place wires at arbitrary positions. This may be a drawback; however, it also makes it easier to create neat and organized wiring, which is especially important when working with complex configurations.

Removing or relocating a wire
--------------------------------

To remove a wire, simply click on either end of it. Then push the right mouse button to remove it. If you have intermediate points in the wire, you have to click the button for each point. This is also the way to relocate a wire, i. e. connect it to another contact.

Moving a slider or pushing a button
--------------------------------

To move any of the slider or push the button simply click on it.

Chaning the color of wires
--------------------------------

Use the mouse wheel to scroll through different colors for the wire you are currently creating. You may even re-color existing wires by clicking on either end of them.


Keyboard commands
-----------------

* Number keys 0-9: Toggle slider S0-S9.
* T key: Press the space bar to toggle button T.

Special keys

- Ctrl+S: Save project.
- Ctrl+L: Load project.
- P: Creates a screenshot in the working directory.
- G: Shows the grid.
- Z: Toggles through different skins / themes of the device.


TODO
----

- Describe keyboard shortcuts.
- Add section for project load/save workflow.




.. toctree::
   :maxdepth: 2



