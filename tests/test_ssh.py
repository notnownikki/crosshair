try:
    from socketserver import TCPServer
except ImportError:
    from SocketServer import TCPServer
import testtools
import paramiko
from mock import Mock, patch
from crosshair.ssh import SSHHandler, SSHServer


class TestableHandler(SSHHandler):
    def __init__(self):
        # The SSHHandler is a stream request handler that expects all
        # kinds of request related things. Instead of mocking it, this
        # class allows us to supply things in a more readable way.
        # Don't judge me.
        pass


class SSHTestCase(testtools.TestCase):
    @patch.object(TCPServer, '__init__')
    def setUp(self, mock_init):
        super(SSHTestCase, self).setUp()
        self.handler = TestableHandler()
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

    def test_getting_command_times_out(self):
        pass

    def test_channel_failure_closes_transport(self):
        pass

    def test_command_executed(self):
        pass
