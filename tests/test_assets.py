import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

from logikus import assets


class AssetTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        assets.clear_font_cache()
        # Image processing can be exercised independently of board rendering.
        self.assets = assets.Assets.__new__(assets.Assets)
        self.assets.skin = assets.SKIN_CLASSIC
        self.assets.images = {}
        self.assets.set_lamps()

    def tearDown(self):
        pygame.quit()

    def test_fonts_are_reused_by_size_and_cleared_on_shutdown(self):
        first = assets.load_standard_font(20)
        self.assertIs(first, assets.load_standard_font(20))
        self.assertIsNot(first, assets.load_standard_font(22))
        pygame.quit()
        self.assertEqual(assets._load_font.cache_info().currsize, 0)
        pygame.init()
        fresh = assets.load_standard_font(20)
        self.assertIsNot(first, fresh)
        self.assertGreater(fresh.render('Test', True, (255, 255, 255)).get_width(), 0)

    def test_segments_scale_up_and_down_to_narrow_lamps(self):
        with patch.object(assets, 'SIZE_LAMP', (60, 80)):
            for width, height in [(53, 7), (2073, 300)]:
                with self.subTest(size=(width, height)):
                    source = pygame.Surface((width, height), pygame.SRCALPHA)
                    for index in range(10):
                        left, right = index * width // 10, (index + 1) * width // 10
                        source.fill((20 * index, 100, 200, 255), (left, 0, right - left, height))
                    self.assets.set_insert(source)
                    for index in range(10):
                        lamp = self.assets.images[f'L{index}_on']
                        self.assertEqual(lamp.get_size(), (60, 80))
                        for position in [(2, 2), (57, 77)]:
                            actual = lamp.get_at(position)
                            self.assertTrue(all(abs(a - b) <= 2 for a, b in
                                                zip(actual, (20 * index, 100, 200, 255))))
                    self.assertIs(self.assets.insert, source)

    def test_scaling_preserves_both_ends_instead_of_cropping(self):
        source = pygame.Surface((2100, 300), pygame.SRCALPHA)
        for index in range(10):
            source.fill((255, 0, 0), (index * 210, 0, 105, 300))
            source.fill((0, 0, 255), (index * 210 + 105, 0, 105, 300))
        self.assets.set_insert(source)
        lamp = self.assets.images['L0_on']
        # Smoothscale's integer interpolation can round full intensity down slightly.
        left = lamp.get_at((3, 3))
        right = lamp.get_at((lamp.get_width() - 4, 3))
        self.assertGreaterEqual(left.r, 252)
        self.assertEqual(left.b, 0)
        self.assertGreaterEqual(right.b, 252)
        self.assertEqual(right.r, 0)

    def test_invalid_insert_leaves_previous_images_unchanged(self):
        valid = pygame.Surface((100, 20), pygame.SRCALPHA)
        self.assets.set_insert(valid)
        previous = dict(self.assets.images)
        for size in [(49, 20), (100, 4)]:
            with self.assertRaises(ValueError):
                self.assets.set_insert(pygame.Surface(size))
            self.assertIs(self.assets.insert, valid)
            self.assertTrue(all(self.assets.images[key] is value for key, value in previous.items()))


if __name__ == '__main__':
    unittest.main()
