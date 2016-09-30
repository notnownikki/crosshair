import os
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import paramiko


class UnknownKeyTypeException(Exception):
    pass


class SSHHandler(socketserver.StreamRequestHandler):
    pass


class SSHServer(
        socketserver.ThreadingMixIn, socketserver.TCPServer,
        paramiko.ServerInterface):
    host_key = None

    def __init__(self, host_key_fname, public_keys_path, address):
        socketserver.TCPServer.__init__(self, address, SSHHandler)
        SSHServer.host_key = self._load_key_from_file(host_key_fname)
        SSHServer.public_keys_path = public_keys_path

    def _load_key_from_file(self, filename):
        # try each type of key paramiko supports. If we ever get another
        # key type, we should make this prettier.
        try:
            key = paramiko.ECDSAKey(filename=filename)
        except paramiko.ssh_exception.SSHException:
            try:
                key = paramiko.DSSKey(filename=filename)
            except paramiko.ssh_exception.SSHException:
                try:
                    key = paramiko.RSAKey(filename=filename)
                except paramiko.ssh_exception.SSHException:
                    raise UnknownKeyTypeException()
        return key

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, exec_command):
        setattr(channel, 'crosshair_command', exec_command.decode())
        return True

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_shell_request(self, channel):
        return False

    def check_channel_pty_request(self, channel, term, width, height,
                                  pixelwidth, pixelheight, modes):
        return False

    def check_auth_publickey(self, username, key):
        key_path = os.path.join(self.public_keys_path, username) + '.pub'
        try:
            with open(key_path, 'r') as pub_key_file:
                pub_key_base64 = pub_key_file.read().strip().split(' ')[1]
        except IOError:
            return paramiko.AUTH_FAILED
        if key.get_base64() == pub_key_base64:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
