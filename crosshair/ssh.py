import os
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import paramiko
import socket
import time
from crosshair import shell


class UnknownKeyTypeException(Exception):
    pass


class SSHHandler(socketserver.StreamRequestHandler):
    accept_timeout = 20
    wait_time = 1

    def do_command(self, cli, channel):
        shell.do_command(cli, channel)

    def set_keepalive(self, after_idle_sec=1, interval_sec=3, max_fails=5):
        """Set TCP keepalive on the request."""
        self.request.setsockopt(
            socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.request.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
        self.request.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
        self.request.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

    def handle(self, *args, **kwargs):
        self.set_keepalive(self.request)
        t = paramiko.Transport(self.request)
        t.add_server_key(self.server.host_key)

        # Note that this actually spawns a new thread to handle the requests.
        # (paramiko.Transport is a subclass of Thread)
        t.start_server(server=self.server)
        channel = t.accept(self.accept_timeout)

        if channel is None:
            t.close()
            return

        time_taken = 0.0
        while getattr(channel, 'crosshair_command', False) is False:
            time.sleep(self.wait_time)
            time_taken += self.wait_time
            if time_taken > self.accept_timeout:
                break

        if getattr(channel, 'crosshair_command', False) is False:
            t.close()
            return

        self.do_command(channel.crosshair_command, channel)
        channel.close()
        t.close()


class SSHServer(
        socketserver.ThreadingMixIn, socketserver.TCPServer,
        paramiko.ServerInterface):
    host_key = None
    public_keys_path = None

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
