from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from threading import Thread
from time import sleep

class Osc_Interface(Thread):
    """
    Class used to create:
      - an OSC client used to send messages to SuperCollider
      - an OSC server to listen to messages coming from SuperCollider
    """

    def __init__(self, client_host='127.0.0.1', client_port=57120, server_host='127.0.0.1', server_port=57130):
        """
        Class constructor
        :param client_host: URL used to reach OSC listener of SuperCollider
        :param client_port: port used to reach OSC listener of SuperCollider
        :param server_host: URL used to reach this running OSC server instance
        :param server_port: port used to reach this running OSC server instance
        """

        # Initiate OSC client
        self._osc_client = udp_client.SimpleUDPClient(client_host, client_port)

        # Register a default dispatcher
        self._dispatcher = Dispatcher()
        self._dispatcher.set_default_handler(self._print_message)

        # Save some init params to the class
        self._server_host = server_host
        self._server_port = server_port

        # Initiate OSC server
        self._start_server()

    def _print_message(address, *args):
        """
        Default handler, prints unhandled messages as they come
        :param args: any data passed in the OSC frame
        """
        print(f"DEFAULT {address}: {args}")

    def _start_server(self):
        """
        Start the OSC server
        """
        self._running = True
        self._server = None
        Thread.__init__(self)

    def run(self):
        """
        OSC server thread startup method
        """
        self._server = BlockingOSCUDPServer((self._server_host, self._server_port), self._dispatcher)
        self._server.serve_forever()

    def stop(self):
        """
        Stop the running OSC server (if it is running)
        """
        self._running = False
        if self._server:
            self._server.shutdown()

    def is_running(self):
        """
        Boldly checks if the OSC server is running
        """
        return self._running

    def add_handler(self, trigger, handler):
        """
        Àdds an OSC handler to the server instance
        :param trigger: name of the trigger in the OSC message coming from SuperCollider
        :param handler: the claas.method that will receive data and process it
        """
        self._dispatcher.map('/' + trigger, handler)

    def send(self, osc_handler, msg):
        """
        Send an OSC message to SuperCollider
        :param osc_handler: name of the handler defined in SuperCollider that will process the message data
        :param msg: message data
        """
        self._osc_client.send_message('/' + osc_handler, msg)
