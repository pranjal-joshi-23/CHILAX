#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class MyNode(Node):
    def __init__(self):
        super().__init__("keyboard_controller")
        self.key_subscriber = self.create_subscription(String, "keyboard_input", self.callback_key_press, 10)
        self.velocity_publisher = self.create_publisher(Twist, "velocity_control", 10)

    def callback_key_press(self, data: String):
        key = data.data

        velocity = Twist()

        if key == "w":
            velocity.linear.x = 6.0
        elif key == "W":
            velocity.linear.x = 8.0
        elif key == "s":
            velocity.linear.x = -6.0
        elif key == "S":
            velocity.linear.x = -8.0
        else:
            velocity.linear.x = 0.0

        self.velocity_publisher.publish(velocity)

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
