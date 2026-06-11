#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import time

class MyNode(Node):
    def __init__(self):
        super().__init__("keyboard_controller")
        self.key_subscriber = self.create_subscription(String, "keyboard_input", self.callback_key_press, 10)
        self.velocity_publisher = self.create_publisher(Twist, "velocity_control", 10)

        self.velocity = Twist()
        self.timer_ = self.create_timer(0.01, self.callback_publisher)
        self.last_key_time = 0.0

    def callback_key_press(self, data: String):
        key = data.data

        if key == "w":
            self.velocity.linear.x = 6.0
        elif key == "W":
            self.velocity.linear.x = 8.0
        elif key == "x":
            self.velocity.linear.x = -6.0
        elif key == "X":
            self.velocity.linear.x = -8.0
        elif key == "a":
            self.velocity.angular.z = 6.0
        elif key == "A":
            self.velocity.angular.z = 8.0
        elif key == "d":
            self.velocity.angular.z = -6.0
        elif key == "D":
            self.velocity.angular.z = -8.0
        elif key == "q":
            self.velocity.linear.x = 6.0
            self.velocity.angular.z = 6.0
        elif key == "z":
            self.velocity.linear.x = -6.0
            self.velocity.angular.z = 6.0
        elif key == "c":
            self.velocity.linear.x = -6.0
            self.velocity.angular.z = -6.0
        elif key == "e":
            self.velocity.linear.x = 6.0
            self.velocity.angular.z = -6.0
        # else:
        #     self.velocity.linear.x = 0.0
        #     self.velocity.angular.z = 0.0
        self.last_key_time = time.time()

    def callback_publisher(self):
        if time.time() - self.last_key_time > 0.01:
            self.velocity.linear.x = 0.0
            self.velocity.angular.z = 0.0
        self.velocity_publisher.publish(self.velocity)

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
