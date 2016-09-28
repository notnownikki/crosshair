import os
import shutil
import testtools
from types import ModuleType
from crosshair import plugins


PLUGIN_SRC = """
import argparse
from crosshair import plugins
from crosshair.commands import Command


def funfunfun():
    return "%s"


class DoThingCommand(Command):
    def setup_parser(self):
        self.parser.add_argument('--things', help='Things to do')

    def execute(self):
        return "%s"

plugins.register_command_handler('do-thing', DoThingCommand)

"""

class PluginManagerTestCase(testtools.TestCase):
    def _create_test_plugin(self, return_value):
        shutil.rmtree('test_plugin', ignore_errors=True)
        os.mkdir('test_plugin')
        fp = open('test_plugin/__init__.py', 'w')
        fp.write(PLUGIN_SRC % (return_value, return_value))
        fp.close()

    def setUp(self):
        super(PluginManagerTestCase, self).setUp()
        self._create_test_plugin('Default')
        plugins.reload()

    def tearDown(self):
        super(PluginManagerTestCase, self).tearDown()
        shutil.rmtree('test_plugin', ignore_errors=True)

    def test_plugin_imported(self):
        plugin = plugins.load('test_plugin')
        self.assertEqual(
            'Default',
            plugin.funfunfun())

    def test_reload_plugin(self):
        plugin = plugins.load('test_plugin')
        self._create_test_plugin('New Code')
        self.assertEqual(
            'Default',
            plugin.funfunfun())
        plugins.reload()
        plugin = plugins.load('test_plugin')
        self.assertEqual(
            'New Code',
            plugin.funfunfun())

    def test_register_command_handler(self):
        plugin = plugins.load('test_plugin')
        handler = plugins.get_command_handler('do-thing')
        self.assertEqual(
            'Default',
            handler.execute())

    def test_command_handler_is_reloaded(self):
        plugin = plugins.load('test_plugin')
        self._create_test_plugin('Reloaded command')
        plugins.reload()
        handler = plugins.get_command_handler('do-thing')
        self.assertEqual(
            'Reloaded command',
            handler.execute())

    def test_handlers_default_none(self):
        handler = plugins.get_command_handler('INVALID')
        self.assertEqual(
            None,
            handler)
