import unittest

from logikus.logic import Button, Logic, OFF, ON, Patchboard


class PathfindingTests(unittest.TestCase):
    def setUp(self):
        self.board = Patchboard({}, Button())

    def test_cycles_duplicates_and_shortest_path(self):
        self.board.put_connections([
            ['Q', 'A'], ['A', 'B'], ['B', 'L0'],
            ['Q', 'L0'], ['Q', 'A'], ['A', 'A'],
        ])
        self.assertEqual(self.board.find_path('Q', 'L0'), (True, ['Q', 'L0']))
        self.assertEqual(self.board.find_path('L0', 'Q'), (True, ['L0', 'Q']))
        self.assertEqual(self.board.find_path('Q', 'L9'), (False, []))

    def test_isolated_source_and_multiple_targets(self):
        self.assertEqual(self.board.find_path('Q', 'Q'), (True, ['Q']))
        self.assertEqual(self.board.find_paths('Q', ['Q', 'L0']), {'Q': ['Q']})

    def test_prefix_is_preserved_without_mutation_or_revisiting(self):
        self.board.put_connections([['A', 'Q'], ['Q', 'L0'], ['A', 'B'], ['B', 'L0']])
        prefix = ['Q']
        self.assertEqual(self.board.find_path('A', 'L0', prefix),
                         (True, ['Q', 'A', 'B', 'L0']))
        self.assertEqual(self.board.find_path('A', 'missing', prefix), (False, []))
        self.assertEqual(prefix, ['Q'])

    def test_long_path_does_not_require_recursion(self):
        self.board.connections = [[str(i), str(i + 1)] for i in range(2000)]
        self.assertEqual(self.board.find_path('0', '2000'),
                         (True, [str(i) for i in range(2001)]))
        self.assertEqual(self.board.find_path('2000', '0'), (False, []))

    def test_changes_and_parallel_wires_are_reflected(self):
        self.board.put_connections([['Q', 'L0'], ['Q', 'L0']])
        self.board.remove_connection(['Q', 'L0'])
        self.assertTrue(self.board.find_path('Q', 'L0')[0])
        self.board.remove_connection(['Q', 'L0'])
        self.assertEqual(self.board.find_path('Q', 'L0'), (False, []))

    def test_lamps_follow_slider_button_and_removed_wires(self):
        logic = Logic()
        logic.add_connections([
            ['Q', 'S0Aa'], ['S0Ab', 'L0'], ['Q', 'Ta'], ['Tb', 'L1'],
        ])
        logic.compute()
        self.assertTrue(all(lamp.state == OFF for lamp in logic.lamps.values()))
        logic.move_slider('S0', 'y')
        self.assertEqual(logic.lamps['L0'].path, ['Q', 'S0Aa', 'S0Ab', 'L0'])
        logic.push_button()
        self.assertEqual(logic.lamps['L1'].state, ON)
        self.assertEqual(logic.lamps['L1'].path, ['Q', 'Ta', 'Tb', 'L1'])
        logic.release_button()
        self.assertIsNone(logic.lamps['L1'].path)
        logic.move_slider('S0', 'x')
        self.assertIsNone(logic.lamps['L0'].path)
        logic.patchboard.remove_connections()
        logic.compute()
        self.assertTrue(all(lamp.state == OFF for lamp in logic.lamps.values()))


if __name__ == '__main__':
    unittest.main()
