from crosshair import plugins


def do_command(cli, channel):
    cmd = cli.split(' ')[0]
    args = ' '.join(cli.split(' ')[1:])
    command = plugins.get_command_handler(cmd)

    if not command:
        channel.send('Command not found.\n')
        return

    if command.parse_args(args):
        command.execute(channel)
    else:
        command.help(channel)
