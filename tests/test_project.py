import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

from logikus.logic import Logic
from logikus.assets import SKINS
from logikus.controller import Controller
from logikus.logic import ON, OFF
from logikus.ui import Ui
from logikus.wiring import Wire


class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_ui(self):
        return Ui(pygame.Surface((1155, 930)), Logic())

    def make_insert(self, path):
        image = pygame.Surface((1050, 150), pygame.SRCALPHA)
        for i in range(10):
            image.fill((20 * i, 255 - 20 * i, 80, 180), (i * 105, 0, 105, 150))
        pygame.image.save(image, str(path))
        return image

    def test_button_release_outside_and_over_other_components(self):
        ui = self.make_ui()
        controller = Controller(ui.surface, ui, ui.logic)
        ui.logic.add_connections([['Q', 'Ta'], ['Tb', 'L0']])
        for position in [(-100, -100), ui.sliders[0].rect.center, ui.contacts['Q.0'].center]:
            with self.subTest(position=position):
                controller.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                        button=1, pos=ui.button.rect.center))
                self.assertEqual(ui.logic.lamps['L0'].state, ON)
                controller.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position))
                ui.update()
                self.assertEqual(ui.logic.button.state, OFF)
                self.assertFalse(ui.lamps[0].state)

    def test_button_tracks_multiple_inputs_and_focus_loss(self):
        ui = self.make_ui()
        controller = Controller(ui.surface, ui, ui.logic)
        def key(event_type, value):
            controller.handle_event(pygame.event.Event(event_type, key=value, mod=0))

        controller.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                button=1, pos=ui.button.rect.center))
        key(pygame.KEYDOWN, pygame.K_SPACE)
        key(pygame.KEYDOWN, pygame.K_t)
        key(pygame.KEYDOWN, pygame.K_t)  # Key repeat must not require another release.
        controller.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(-1, -1)))
        key(pygame.KEYUP, pygame.K_SPACE)
        self.assertEqual(ui.logic.button.state, ON)
        ui.wiring.wire = Wire(ui.contacts['Q.0'])
        key(pygame.KEYUP, pygame.K_t)  # Release is processed even in wiring mode.
        self.assertEqual(ui.logic.button.state, OFF)
        ui.wiring.wire = None
        key(pygame.KEYDOWN, pygame.K_SPACE)
        controller.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(ui.logic.button.state, OFF)
        key(pygame.KEYDOWN, pygame.K_t)
        key(pygame.KEYUP, pygame.K_t)
        self.assertEqual(ui.logic.button.state, OFF)

    def test_reinitializing_and_reloading_lamps_preserves_identity_and_state(self):
        ui = self.make_ui()
        lamps = list(ui.lamps)
        ui.logic.add_connection(['Q', 'L0'])
        ui.logic.compute()
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'insert.png'
            self.make_insert(source)
            for _ in range(3):
                ui.init_lamps()
                ui.load_insert(source)
                self.assertEqual(len(ui.lamps), 10)
                self.assertTrue(all(current is original for current, original in zip(ui.lamps, lamps)))
                self.assertTrue(ui.lamps[0].state)
                self.assertFalse(ui.lamps[1].state)
                self.assertIs(ui.component_at_xy(ui.lamps[0].rect.center), ui.lamps[0])
        ui.logic.remove_connection(['Q', 'L0'])
        ui.logic.compute()
        ui.init_lamps()
        self.assertFalse(ui.lamps[0].state)

    def test_round_trip_preserves_wires_labels_and_original_insert(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.png'
            original = self.make_insert(source)
            ui = self.make_ui()
            ui.load_insert(source)
            source.unlink()  # Saving must not depend on the source file still existing.
            ui.set_labels(['Größe', 'Fußball', '', 'Zürich'])
            wire = Wire(ui.contacts['Q.0'], ui.contacts['L0.0'], color=2)
            wire.path = [wire.start.center, (97, 202), wire.end.center]
            ui.put_wire(wire)
            destination = root / 'new' / 'project'
            ui.save_project(destination)

            restored = self.make_ui()
            restored.load_project(destination)
            self.assertEqual(restored.label_names, ui.label_names)
            self.assertEqual([w.write() for w in restored.wiring.wires], [wire.write()])
            self.assertEqual(pygame.image.tobytes(restored.assets.insert, 'RGBA'),
                             pygame.image.tobytes(original, 'RGBA'))
            self.assertEqual(len(restored.lamps), 10)
            for name in ('L0_on', 'L9_off'):
                self.assertEqual(pygame.image.tobytes(restored.assets.images[name], 'RGBA'),
                                 pygame.image.tobytes(ui.assets.images[name], 'RGBA'))
            restored.save_project(destination)  # Also works in the original project directory.
            restored.load_insert(destination / 'insert.png')
            self.assertEqual(len(restored.lamps), 10)
            self.assertEqual(pygame.image.tobytes(restored.assets.insert, 'RGBA'),
                             pygame.image.tobytes(original, 'RGBA'))

    def test_empty_project_overwrites_stale_labels_and_insert(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.make_insert(directory / 'insert.png')
            (directory / 'labels.txt').write_text('old', encoding='utf-8')
            ui = self.make_ui()
            ui.save_project(directory)
            self.assertFalse((directory / 'insert.png').exists())
            restored = self.make_ui()
            restored.load_project(directory)
            self.assertEqual(restored.label_names, [])
            self.assertEqual(restored.wiring.wires, [])
            self.assertIsNone(restored.assets.insert)

    def test_skin_changes_preserve_contacts_controls_and_wire_colors(self):
        ui = self.make_ui()
        wire = Wire(ui.contacts['Q.0'], ui.contacts['L0.0'], color=8)
        wire.path = [wire.start.center, wire.end.center]
        ui.put_wire(wire)
        ui.logic.move_slider('S0', 'y')
        ui.logic.push_button()
        ui.update()
        ui.set_labels(['Test'])
        ui.menu.visible = True
        ui.color_wire_active = 8
        components = dict(ui.components)

        for skin in [*SKINS, 'classic', 'unknown']:
            with self.subTest(skin=skin):
                ui.set_skin(skin)
                ui.draw()  # All wire indices must work even with a one-color palette.
                self.assertTrue(all(ui.components[key] is value
                                    for key, value in components.items()))
                self.assertIs(ui.contacts['Q.0'], wire.start)
                self.assertIs(wire.start.connected_to, wire.end)
                self.assertFalse(wire.start.empty)
                self.assertEqual(wire.color, 8)
                self.assertEqual(ui.label_names, ['Test'])
                self.assertTrue(ui.menu.visible)
                self.assertTrue(ui.sliders[0].state)
                self.assertTrue(ui.button.state)
                self.assertTrue(ui.lamps[0].state)
                self.assertEqual(ui.color_picker.color, ui.active_wire_color)
                self.assertEqual(ui.surface.get_at(wire.path[0])[:3], ui.colors_wire[8 % len(ui.colors_wire)])

        ui.remove_wire(wire)
        ui.logic.compute()
        self.assertTrue(wire.start.empty)
        self.assertTrue(wire.end.empty)
        self.assertEqual(ui.wiring.wires, [])

    def test_skin_change_preserves_insert_and_recolors_off_images(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / 'source.png'
            original = self.make_insert(source)
            ui = self.make_ui()
            ui.load_insert(source)
            source.unlink()
            original_on = pygame.image.tobytes(ui.lamps[0].image_on, 'RGBA')
            original_off = pygame.image.tobytes(ui.lamps[0].image_off, 'RGBA')
            ui.set_skin('hulk')
            self.assertEqual(pygame.image.tobytes(ui.lamps[0].image_on, 'RGBA'), original_on)
            self.assertNotEqual(pygame.image.tobytes(ui.lamps[0].image_off, 'RGBA'), original_off)
            ui.save_project(directory)
            saved = pygame.image.load(str(directory / 'insert.png'))
            self.assertEqual(pygame.image.tobytes(saved, 'RGBA'), pygame.image.tobytes(original, 'RGBA'))
            ui.set_skin('classic')
            self.assertEqual(pygame.image.tobytes(ui.lamps[0].image_off, 'RGBA'), original_off)
            self.assertEqual(len(ui.lamps), 10)

    def test_loading_without_insert_restores_default_lamps(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / 'source.png'
            self.make_insert(source)
            ui = self.make_ui()
            default = pygame.image.tobytes(ui.assets.images['L0_on'], 'RGBA')
            ui.load_insert(source)
            ui.load_project(directory)
            self.assertIsNone(ui.assets.insert)
            self.assertEqual(len(ui.lamps), 10)
            self.assertEqual(pygame.image.tobytes(ui.lamps[0].image_on, 'RGBA'), default)


if __name__ == '__main__':
    unittest.main()
