#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys
import tty
import termios
import threading

class MyNode(Node):
    def __init__(self):
        super().__init__("keyboard_input_node")
        self.key_publisher = self.create_publisher(String, "keyboard_input", 10)

        self.running = True

        self.input_thread = threading.Thread(target=self.keyboard_loop)
        self.input_thread.daemon = True
        self.input_thread.start()

        self.get_logger().info("Keyboard Controller Initialized!")

    def keyboard_loop(self):
        # storing original terrminal settings
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while self.running:
                key = sys.stdin.read(1)

                msg = String()
                msg.data = key

                self.key_publisher.publish(msg)
            
        finally:
            # resetting terminal settings to original
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def destroy_node(self):
        self.running = False
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
