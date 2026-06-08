#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from chilax_interfaces.srv import CalculatePosition
from math import *
import numpy as np

class MyNode(Node):
    def __init__(self):
        super().__init__("calculate_position_service_node")
        
        self.thigh = 0
        self.lower_leg = 0
        self.start = []
        self.top = []
        self.end = []
        self.bottom = []
        
        self.joint0_forward = []
        self.joint0_backward = []
        self.joint1_forward = []
        self.joint1_backward = []
        self.joint2_forward = []
        self.joint2_backward = []
        
        self.calculate_position = self.create_service(CalculatePosition, "calculate_joint_position", self.callback_calculate_joint_position)

    def calc(self, position):
        x, y, z = position

        z_axis = atan2(z, x)

        # horizontal distance after turning toward target
        r = sqrt(x*x + z*z)

        # distance in movement plane
        leg_height = sqrt(r*r + y*y)

        c = (self.thigh**2 + self.lower_leg**2 - leg_height**2) / (2*self.thigh*self.lower_leg)
        c = max(-1, min(1, c))
        y_axis = acos(c)

        c2 = (self.thigh**2 + leg_height**2 - self.lower_leg**2) / (2*self.thigh*leg_height)
        c2 = max(-1, min(1, c2))
        alpha = acos(c2)

        base = atan2(y, r)

        x_axis = base - alpha

        return (z_axis, x_axis, y_axis)

    def bezier(self, start, middle, end, t):
        return (1-t)**2 * np.array(start) + 2 * (1-t) * t * np.array(middle) + t**2 * np.array(end)

    def callback_calculate_joint_position(self, request: CalculatePosition.Request, response: CalculatePosition.Response):
        self.thigh = request.thigh
        self.lower_leg = request.lower_leg
        self.start = request.start
        self.top = request.top
        self.end = request.end
        self.bottom = request.bottom
        
        for t in np.linspace(0, 1, 10):
            position = self.bezier(self.start, self.top, self.end, t)
            
            movement = self.calc(position)
            
            self.joint0_forward.append(movement[0])
            self.joint1_forward.append(movement[1])
            self.joint2_forward.append(movement[2])
            
        for t in np.linspace(0, 1, 10):
            position = self.bezier(self.end, self.bottom, self.start, t)
            
            movement = self.calc(position)
            
            self.joint0_backward.append(movement[0])
            self.joint1_backward.append(movement[1])
            self.joint2_backward.append(movement[2])
        
        response = CalculatePosition.Response()
        response.joint0_forward = self.joint0_forward
        response.joint0_backward = self.joint0_backward
        response.joint1_forward = self.joint1_forward
        response.joint1_backward = self.joint1_backward
        response.joint2_forward = self.joint2_forward
        response.joint2_backward = self.joint2_backward
        
        return response
        
def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()
    
if __name__ == "__main__":
    main()
