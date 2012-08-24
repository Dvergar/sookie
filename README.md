# Sookie

Sookie is a TCP game server framework, its primary use is to be able to just work for any platform you are using, flash, javascript or anything.

## Usage
Make a connection class and feed it to sookie.

    class Connection:
        def on_connection(self):
            pass

        def on_message(self, msg):
            self.bs.put_data(msg)
            while self.bs.working():
                msg_type = self.bs.read_byte()
                if msg_type == PLAYER_UPDATE:
                    left, right, up, down, attack = self.bs.read_byte(), \
                            self.bs.read_byte(), self.bs.read_byte(), \
                            self.bs.read_byte(), self.bs.read_byte()
                    self.player.net_update(left, right, up, down)
                    ...

        def on_close(self, reason):
            pass`


    if __name__ == '__main__':
        game = Game()
        sookie.start_server(9999, appmanager=game, protocol=Connection, \
                            apprate=1 / 60., netrate=1 / 10.)

The websocket port will be your defined port +1 (10000 in that case)