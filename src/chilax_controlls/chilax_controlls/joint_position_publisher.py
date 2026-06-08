#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from chilax_interfaces.msg import Positions

class MyNode(Node):
    def __init__(self):
        super().__init__("joint_position_publisher_node")
        
        self.get_positions = self.create_subscription(Positions, "joint_positions", self.callback_publish_position, 10)
        
        self.fl0 = self.create_publisher(Float64, "/fl0/cmd_pos", 10)
        self.fl1 = self.create_publisher(Float64, "/fl1/cmd_pos", 10)
        self.fl2 = self.create_publisher(Float64, "/fl2/cmd_pos", 10)
        self.fr0 = self.create_publisher(Float64, "/fr0/cmd_pos", 10)
        self.fr1 = self.create_publisher(Float64, "/fr1/cmd_pos", 10)
        self.fr2 = self.create_publisher(Float64, "/fr2/cmd_pos", 10)
        self.bl0 = self.create_publisher(Float64, "/bl0/cmd_pos", 10)
        self.bl1 = self.create_publisher(Float64, "/bl1/cmd_pos", 10)
        self.bl2 = self.create_publisher(Float64, "/bl2/cmd_pos", 10)
        self.br0 = self.create_publisher(Float64, "/br0/cmd_pos", 10)
        self.br1 = self.create_publisher(Float64, "/br1/cmd_pos", 10)
        self.br2 = self.create_publisher(Float64, "/br2/cmd_pos", 10)
        
        self.joint_publishers = [
            self.fl0, self.fl1, self.fl2,
            self.fr0, self.fr1, self.fr2,
            self.bl0, self.bl1, self.bl2,
            self.br0, self.br1, self.br2
        ]
        
    def callback_publish_position(self, positions: Positions):
        for i, pub in enumerate(self.joint_publishers):
            msg = Float64()
            msg.data = positions.data[i]
            pub.publish(msg)
        
def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__=="__main__":
    main()    
