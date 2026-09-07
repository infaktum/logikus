import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

from logikus.logic import Logic
from logikus.ui import Ui
from logikus.wiring import Contact, Wire, convert_grid_point


class GridConversionTests(unittest.TestCase):
    def test_cell_centers_survive_different_grid_sizes_without_drift(self):
        for point in [(7, 7), (97, 427), (1102, 232), (-8, -23)]:
            for size in (11, 15, 22, 30):
                with self.subTest(point=point, size=size):
                    scaled = convert_grid_point(point, 15, size)
                    self.assertEqual(scaled[0] % size, size // 2)
                    self.assertEqual(scaled[1] % size, size // 2)
                    self.assertEqual(convert_grid_point(scaled, size, 15), point)

    def test_noncentered_points_snap_and_invalid_sizes_are_rejected(self):
        self.assertEqual(convert_grid_point((90, 420), 15, 11), (71, 313))
        for source, target in [(0, 15), (15, 0), (-1, 15)]:
            with self.assertRaises(ValueError):
                convert_grid_point((0, 0), source, target)

    def test_serialization_uses_reference_coordinates_without_mutating_path(self):
        wire = Wire(Contact('Q.0', 11, 132, 11, 11), Contact('L0.0', 99, 132, 11, 11), 2)
        wire.path = [wire.start.center, (71, 313), (71, 236), wire.end.center]
        previous = list(wire.path)
        self.assertEqual(wire.write(11), 'Q.0-L0.0 2 : (97,427) - (97,322)')
        self.assertEqual(wire.path, previous)


class WiringGridRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_example_round_trip_between_grid_sizes_preserves_routes(self):
        source = Path(__file__).resolve().parents[1] / 'projekte/15 BauerWolfZiegeKohl/wiring.lkw'
        expected = source.read_text(encoding='utf-8').splitlines()
        with TemporaryDirectory() as temporary:
            destination = Path(temporary)
            for size in (15, 11, 22, 30, 15):
                with self.subTest(size=size):
                    ui = Ui(pygame.Surface((77 * size, 62 * size)), Logic(), grid_size=size)
                    ui.load_wiring(source)
                    self.assertTrue(any(len(wire.path) > 2 for wire in ui.wiring.wires))
                    for wire in ui.wiring.wires:
                        self.assertEqual(wire.path[0], wire.start.center)
                        self.assertEqual(wire.path[-1], wire.end.center)
                        for x, y in wire.path[1:-1]:
                            self.assertEqual((x % size, y % size), (size // 2, size // 2))
                    ui.save_project(destination)
                    source = destination / 'wiring.lkw'
                    self.assertEqual(source.read_text(encoding='utf-8').splitlines(), expected)


if __name__ == '__main__':
    unittest.main()
