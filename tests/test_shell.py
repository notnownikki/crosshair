import testtools
from mock import Mock, MagicMock, patch
from crosshair import plugins
from crosshair.shell import do_command


class ShellTestCase(testtools.TestCase):
    @patch.object(plugins, 'get_command_handler')
    def test_command_execute(self, mock_get_command):
        mock_command = Mock()
        mock_channel = Mock()
        mock_get_command.return_value = mock_command
        mock_command.parse_args.return_value = True
        do_command('list-commands 1 2 3 4', mock_channel)
        mock_get_command.assert_called_once_with('list-commands')
        mock_command.execute.assert_called_once_with(mock_channel)

    @patch.object(plugins, 'get_command_handler')
    def test_command_not_found(self, mock_get_command):
        mock_channel = Mock()
        mock_get_command.return_value = None
        do_command('list-commands 1 2 3 4', mock_channel)
        mock_get_command.assert_called_once_with('list-commands')
        mock_channel.send.assert_called_once_with('Command not found.\n')
