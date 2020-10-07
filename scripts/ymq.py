import zmq
import threading


class YPubNode:
    """ Dedicated publish yNode"""
    def __init__(self, default_topic="TheForce", channel=5555, ):
        """
        :param default_topic: default topic to publish on.
        :param channel: channel for pub server. default 5555.
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(f"tcp://localhost:{channel}")
        self.topic = default_topic

    def set_def_topic(self, topic):
        """
        Set default topic to publish. If this node just write to one topic, this function is recommended to avoid
        writing the topic every time in the post function.
        :param topic: default topic for publish.
        """
        self.topic = topic

    def post(self, message, topic=None):
        """
        Post message into yServer
        :param message: well, the message.
        :param topic: The topic to subscribe. Default is None. if no parameter, the message will be published in
                      the default topic
        """
        if topic is None:
            topic = self.topic
        else:
            topic = topic.replace(" ", "")
        self.socket.send_string(f"{topic} {message}")


class YSubNode:
    """ Dedicated Subscription node"""
    def __init__(self, topic, channel=5556):
        """
        Init the dedicated sub ynode string. Topics can be just a topic or a list of topic to listen.
        :param topic: topic or list of topics.
        :param channel:
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)

        self.socket.connect(f"tcp://localhost:{channel}")

        if isinstance(topic, list):
            for t in topic:
                self.socket.setsockopt_string(zmq.SUBSCRIBE, t)
        else:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def subscribe(self, topic):
        """
        subscribe to additional topic or list of topics
        :param topic: topic or list of topics
        """
        if isinstance(topic, list):
            for t in topic:
                self.socket.setsockopt_string(zmq.SUBSCRIBE, t)
        else:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def get(self):
        """
        Get the data
        :return: message
        :return: topic
        """
        string = self.socket.recv_string()
        topic, message = string.split(" ", 1)
        return message, topic


class YPubSubNode:
    def __init__(self, pub_channel=5555, sub_channel=5556):
        self.sub_context = zmq.Context()
        self.sub_socket = self.sub_context.socket(zmq.SUB)

        self.pub_context = zmq.Context()
        self.pub_socket = self.pub_context.socket(zmq.PUB)

        self.pub_channel = pub_channel
        self.sub_channel = sub_channel

        self.pub_topic = "default"

    def init_pub_node(self):
        self.pub_socket.connect(f"tcp://localhost:{self.pub_channel}")

    def init_sub_node(self, topic=""):
        self.sub_socket.connect(f"tcp://localhost:{self.sub_channel}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def init_pubsub_node(self, topic=""):
        self.pub_socket.connect(f"tcp://localhost:{self.pub_channel}")
        self.sub_socket.connect(f"tcp://localhost:{self.sub_channel}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def set_pub_topic(self, topic):
        self.pub_topic = topic

    def post(self, message, topic=None):
        if topic is None:
            topic = self.pub_topic
        else:
            topic = topic.replace(" ", "")
        self.pub_socket.send_string(f"{topic} {message}")

    def get(self):
        return self.sub_socket.recv_string()

    # def subscribe(self, topic):


class YServer:

    def __init__(self, pub_channel=5555, sub_channel=5556, verbose=False):
        self.ymqserver = threading.Thread(target=self._server_thread_)
        self.pub_channel = pub_channel
        self.sub_channel = sub_channel
        self.verbose = verbose
        self.server_running = False

    def start(self):
        self.server_running = True
        self.ymqserver.start()

    def stop(self):
        self.server_running = False

    def _server_thread_(self):
        # Subscribe to the PUB channel
        self.sub_context = zmq.Context()
        self.sub_socket = self.sub_context.socket(zmq.SUB)
        self.sub_socket.bind(f"tcp://*:{self.pub_channel}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # Publish in the SUB channel
        self.pub_context = zmq.Context()
        self.pub_socket = self.pub_context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{self.sub_channel}")

        print("YMQ Server Started")

        try:
            while self.server_running:
                string = self.sub_socket.recv_string()
                self.pub_socket.send_string(string)
                topic, messagedata = string.split(" ", 1)
                if self.verbose:
                    print(f"{topic} -> {messagedata}")
            self.sub_socket.close()
            self.pub_socket.close()
            self.sub_context.term()
            self.pub_context.term()
        except Exception as e:
            print("error: ", e)
        finally:
            self.sub_socket.close()
            self.pub_socket.close()
            self.sub_context.term()
            self.pub_context.term()
