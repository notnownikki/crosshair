try:
    from socketserver import TCPServer, StreamRequestHandler
except ImportError:
    from SocketServer import TCPServer, StreamRequestHandler
import testtools
import paramiko
import socket
from mock import Mock, MagicMock, patch
from crosshair import plugins
from crosshair.ssh import SSHHandler, SSHServer


class SSHServerTestCase(testtools.TestCase):
    @patch.object(TCPServer, '__init__')
    def setUp(self, mock_tcp_init):
        super(SSHServerTestCase, self).setUp()
        mock_tcp_init.return_value = None
        self.server = SSHServer(
            'tests/data/host_key', 'tests/data/public_keys',
            ('0.0.0.0', 4022))

    def test_sshserver_hostkey_loaded_from_filename(self):
        """Check the public key matches the key in the filename we specify"""
        self.assertEqual(
            'AAAAB3NzaC1yc2EAAAADAQABAAABAQCx+ZW4Yicm6pQh2Caw4JHGrJqkh5R6QPIA'
            'pRuJ04QQmJxlp53d0sZ9JMn6VBJaRbRh49qVXHkSvUTUP+/dmP7qxzqs9UyUFq0v'
            'qWxOyVBl8805ifQQd4UDnkh1gx82aUV3F4tCQE3PDHUV3QTvaSB2pgfn+tukdNzy'
            'xa2wezWd2/poimj64dIimesH01G5/PiXBvjNVItDDg+bgCJehUgpZGjFOTb9NFW5'
            'h90GBY5fBJWCavjH4alScMz6s/iveYwGKvVTUdPPbLldiXwIO654T3Mjof+OonT3'
            'Y/zGaDaJeKoZvvLf0WynhwRAVeFnpUKEskBFEHEQeB80kyKj1yC9',
            self.server.host_key.get_base64())

    def test_command_set_on_channel(self):
        channel = Mock()
        self.server.check_channel_exec_request(channel, b'command')
        self.assertEqual(
            'command',
            channel.crosshair_command)

    def test_authentication_valid_key(self):
        key = paramiko.RSAKey(filename='tests/data/private_keys/admin')
        self.assertEqual(
            paramiko.AUTH_SUCCESSFUL,
            self.server.check_auth_publickey('admin', key))

    def test_authentication_invalid_key(self):
        key = paramiko.RSAKey(filename='tests/data/private_keys/user')
        self.assertEqual(
            paramiko.AUTH_FAILED,
            self.server.check_auth_publickey('admin', key))

    def test_authentication_invalid_username(self):
        key = paramiko.RSAKey(filename='tests/data/private_keys/user')
        self.assertEqual(
            paramiko.AUTH_FAILED,
            self.server.check_auth_publickey('idonotexist', key))


class SSHHandlerTestCase(testtools.TestCase):
    @patch.object(StreamRequestHandler, '__init__')
    def setUp(self, mock_stream_init):
        super(SSHHandlerTestCase, self).setUp()
        mock_stream_init.return_value = None
        self.handler = SSHHandler()
        self.handler.server = Mock()
        self.handler.server.host_key = 'A Key'
        self.request = Mock()
        self.handler.request = self.request

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_transport_constructed(self, mock_transport, mock_do_com):
        mock_transport.return_value = Mock()
        self.handler.handle()
        mock_transport.assert_called_once_with(self.request)

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_host_key_set_on_transport(self, mock_transport, mock_do_com):
        transporter = Mock()
        mock_transport.return_value = transporter
        self.handler.handle()
        transporter.add_server_key.assert_called_once_with('A Key')

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_server_gets_started(self, mock_transport, mock_do_com):
        transporter = Mock()
        mock_transport.return_value = transporter
        self.handler.handle()
        transporter.start_server.assert_called_once_with(
            server=self.handler.server)

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_getting_command_timeout(self, mock_transport, mock_do_com):
        transporter = Mock()
        mock_transport.return_value = transporter
        channel = Mock()
        # no command will be set
        channel.crosshair_command = False
        transporter.accept.return_value = channel
        self.handler.accept_timeout = 0.1
        self.handler.wait_time = 0.2
        self.handler.handle()
        # accept the channel
        transporter.accept.assert_called_once_with(
            self.handler.accept_timeout)
        # no command, so just close the transport
        transporter.close.assert_called_once()
        
    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_socket_options_set(self, mock_transport, mock_do_com):
        transporter = Mock()
        mock_transport.return_value = transporter
        self.handler.handle()
        self.assertTrue(self.handler.request.setsockopt.called)

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_channel_failure_closes_transport(self, mock_transport, mock_do_com):
        transporter = Mock()
        mock_transport.return_value = transporter
        transporter.accept.return_value = None
        self.handler.handle()
        transporter.accept.assert_called_once_with(
            self.handler.accept_timeout)
        # no channel, transport should get closed
        transporter.close.assert_called_once()

    @patch.object(SSHHandler, 'do_command')
    @patch.object(paramiko, 'Transport')
    def test_command_executed(self, mock_transport, mock_do_command):
        transporter = Mock()
        mock_transport.return_value = transporter
        channel = Mock()
        channel.crosshair_command = 'list-commands'
        transporter.accept.return_value = channel
        self.handler.handle()
        mock_do_command.assert_called_once_with('list-commands', channel)

    @patch.object(plugins, 'get_command_handler')
    def test_command_help_on_bad_args(self, mock_get_command):
        mock_command = Mock()
        mock_channel = Mock()
        mock_get_command.return_value = mock_command
        mock_command.parse_args.return_value = False
        self.handler.do_command('list-commands 1 2 3 4', mock_channel)
        mock_get_command.assert_called_once_with('list-commands')
        mock_command.parse_args.assert_called_once_with('1 2 3 4')
        mock_command.help.assert_called_once_with(mock_channel)

    @patch.object(plugins, 'get_command_handler')
    def test_command_execute(self, mock_get_command):
        mock_command = Mock()
        mock_channel = Mock()
        mock_get_command.return_value = mock_command
        mock_command.parse_args.return_value = True
        self.handler.do_command('list-commands 1 2 3 4', mock_channel)
        mock_get_command.assert_called_once_with('list-commands')
        mock_command.execute.assert_called_once_with(mock_channel)

    @patch.object(plugins, 'get_command_handler')
    def test_command_not_found(self, mock_get_command):
        mock_channel = Mock()
        mock_get_command.return_value = None
        self.handler.do_command('list-commands 1 2 3 4', mock_channel)
        mock_get_command.assert_called_once_with('list-commands')
        mock_channel.send.assert_called_once_with('Command not found.\n')
