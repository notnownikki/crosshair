Crosshair
=========

Issue commands to your python app and reload its code on demand using SSH.

Features
--------
* RPC-like control over an SSH interface
* Code management through a plugin manager that supports reloading at runtime

Using the SSH Server
====================

So, you want to start your ssh server so you can issue commands to your application? Great! There are a couple of things you need to do before you start.

Set up keys
-----------

Generate a host key in RSA, DSA, or ECDSA format. Put this in a safe place on disk, for example, `/home/crosshair/keys/id_host_rsa`

Now you'll need to set up at least one key so you can access the server. Create a directory to store user keys, for example, `/home/crosshair/keys/users/` Then put each user's public key in that directory in a file named `username.pub`, for example, the user `nicola` would have her key in `/home/crosshair/keys/users/nicola.pub`

Now you're all set with the keys you need to run a crosshair SSH server.

Public keys can be added or removed at any time, the server does not need to restart to pick up changes.

Running the SSH Server
----------------------

`crosshair.ssh.SSHServer` takes the following arguments to `__init__`

* host_key_fname: the filename of the host key
* public_keys_path: the path to where user's public keys are stored
* address: two tuple of address and port to listen on

Example:

```
from crosshair import ssh

server = ssh.SSHServer(
    host_key_fname = '/home/crosshair/keys/host_rsa.key',
    public_keys_path = '/home/crosshair/keys/public_keys/',
    address = ('192.168.0.42', 9045))
```

Now you have your SSH Server ready! You probably want to load the core plugins next:

```
from crosshair import plugins

plugins.load('crosshair.commands')
```

Now start your server with:

```
server.serve_forever()
```

Client usage example:

```
$ ssh -p 9045 -i ./admin admin@192.168.0.42 list-commands
help
list-commands
reload-plugins
$ ssh -p 9045 -i ./admin admin@192.168.0.42 help list-commands
usage: list-commands
$ ssh -p 9045 -i ./admin admin@192.168.0.42 reload-plugins
Plugins reloaded.
```

Commands and Plugins
====================

Built in commands
-----------------

If you have loaded the `crosshair.commands` plugin, you will have these commands available:

* list-commands: Lists the available commands
* help <command name>: displays help for the specified command
* reload-plugins: reloads all crosshair plugins from disk


Writing Command Plugins
-----------------------

Commands should extend `crosshair.commands.Command`, and implement the following methods:

* execute(_self, channel_): run the command, sending any output to `channel` using `channel.send`
* setup_parser(_self_): Initialise `self.parser` with an argument parser that extends `crosshair.commands.ArgumentParser`, which is a standard Python `argparse.ArgumentParser` with slightly altered error handling

Once you have written your commands, register them with the plugin handler.

Example:

_`myplugin.py`_
```
from crosshair import plugins
from crosshair import commands


class HelloWorldCommand(commands.Command):
    def execute(self, channel):
        channel.send('Hello, world!\n')


plugins.register_command_handler('hello-world', HelloWorldCommand)
```

Remember to load your command plugin like this:

```
from crosshair import plugins

plugins.load('myplugin')
```
