from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch

import pygame

import logikus
from logikus import assets


class ResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        assets.clear_font_cache()
        pygame.font.quit()

    def test_source_paths_and_loading_do_not_depend_on_working_directory(self):
        package = Path(assets.__file__).resolve().parent
        with TemporaryDirectory() as temporary, chdir(temporary):
            self.assertEqual(assets.font(logikus.font), package / 'fonts' / logikus.font)
            self.assertEqual(assets.image('icon.png'), package / 'images' / 'icon.png')
            self.assertIsInstance(assets.load_icon(), pygame.Surface)
            self.assertGreater(assets.load_standard_font(20).get_height(), 0)

    def test_frozen_paths_match_spec_layout_and_load_resources(self):
        package = Path(assets.__file__).resolve().parent
        with TemporaryDirectory() as temporary:
            bundle = Path(temporary)
            for folder, name in [('fonts', logikus.font), ('images', 'icon.png')]:
                (bundle / folder).mkdir()
                (bundle / folder / name).write_bytes((package / folder / name).read_bytes())
            with patch.object(sys, '_MEIPASS', str(bundle), create=True):
                self.assertEqual(assets.font(logikus.font), bundle / 'fonts' / logikus.font)
                self.assertEqual(assets.image('icon.png'), bundle / 'images' / 'icon.png')
                self.assertIsInstance(assets.load_icon(), pygame.Surface)
                self.assertGreater(assets.load_standard_font(20).get_height(), 0)

    def test_missing_icon_is_optional(self):
        with TemporaryDirectory() as temporary:
            with patch.object(sys, '_MEIPASS', temporary, create=True):
                self.assertIsNone(assets.load_icon())

    def test_invalid_icon_is_not_silently_ignored(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'images'
            directory.mkdir()
            (directory / 'icon.png').write_bytes(b'not an image')
            with patch.object(sys, '_MEIPASS', temporary, create=True):
                with self.assertRaises(pygame.error):
                    assets.load_icon()


if __name__ == '__main__':
    unittest.main()
