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

    def __init__(self, host_key_fname, address):
        socketserver.TCPServer.__init__(self, address, SSHHandler)
        # try each type of key paramiko supports. If we ever get another
        # key type, we should make this prettier.
        try:
            SSHServer.host_key = paramiko.ECDSAKey(
                filename=host_key_fname)
        except paramiko.ssh_exception.SSHException:
            try:
                SSHServer.host_key = paramiko.DSSKey(
                    filename=host_key_fname)
            except paramiko.ssh_exception.SSHException:
                try:
                    SSHServer.host_key = paramiko.RSAKey(
                        filename=host_key_fname)
                except paramiko.ssh_exception.SSHException:
                    raise UnknownKeyTypeException()

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
