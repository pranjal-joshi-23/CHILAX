#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from chilax_interfaces.msg import Positions
import numpy as np
from math import *
from geometry_msgs.msg import Twist

class MyNode(Node):
    def __init__(self):
        super().__init__("movement_node")
        
        self.declare_parameter("thigh", 8)
        self.declare_parameter("lower_leg", 9)
        # these are in format front left-right, back left-right
        self.declare_parameter("hip_offset", [10.5, 5.0, 0.0, 10.5, -5.0, 0.0, -10.5, 5.0, 0.0, -10.5, -5.0, 0.0])
        
        self.declare_parameter("standing", [10.5, 9.5, -11.0, 10.5, -9.5, -11.0, -10.5, 9.5, -13.0, -10.5, -9.5, -13.0])
        
        self.declare_parameter("start", [7.5, 9.5, -11.0, 7.5, -9.5, -11.0, -13.5, 9.5, -13.0, -13.5, -9.5, -13.0])
        self.declare_parameter("middle", [10.5, 9.5, -5.0, 10.5, -9.5, -5.0, -10.5, 9.5, -10.0, -10.5, -9.5, -10.0])
        self.declare_parameter("end", [13.5, 9.5, -11.0, 13.5, -9.5, -11.0, -7.5, 9.5, -13.0, -7.5, -9.5, -13.0])
        
        # wont require these in the way they currently are but it technically works like this
        # think there is a better approach for velocity scaling
        self.thigh = self.get_parameter("thigh").value
        self.lower_leg = self.get_parameter("lower_leg").value
        self.hip_offset = self.get_parameter("hip_offset").value
        self.standing = self.get_parameter("standing").value
        self.start = self.get_parameter("start").value
        self.middle = self.get_parameter("middle").value
        self.end = self.get_parameter("end").value
        
        self.theta0 = []
        
        for i in range(4):
            foot = self.standing[i*3:i*3+3]
            hip = self.hip_offset[i*3:i*3+3]
            
            local = self.to_local(foot, hip)
            self.theta0.append(self.side_angle(local))
        
        # velocity
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        
        # Starting Position
        self.standing_position = [*self.calc(self.to_local(self.standing[0:3], self.hip_offset[0:3])),
                                  *self.calc(self.to_local(self.standing[3:6], self.hip_offset[3:6])),
                                  *self.calc(self.to_local(self.standing[6:9], self.hip_offset[6:9])),
                                  *self.calc(self.to_local(self.standing[9:12], self.hip_offset[9:12]))]
        
        # Current Position
        self.current_positions = self.standing_position.copy()
        
        # t is for bezier curve
        self.t = 0
        self.base_dt = 0.03
        
        # keeps track of steps of single movement(1 single movement consists of 2 steps)
        self.step = 1
        
        # a subscriber that listens to the topic with linear and angular velocity and adjusts the walking speed as per 
        self.get_velocity = self.create_subscription(Twist, "velocity_control", self.callback_velocity_changed, 10)
        
        self.publish_positions = self.create_publisher(Positions, "joint_positions", 10)
        
        # Calling for starting position
        # self.startup_timer = self.create_timer(5.0, self.publish_intital_pose)
        self.is_standing = True
        
        # Now keep calling
        self.timer = self.create_timer(0.04, self.call_calculate_joint_position)
        
    def side_angle(self, position):
        x, y, z = position
        return atan2(y, -z)
        
    def calc(self, position):
        x, y, z = position

        # 1. Hip yaw (sideways)
        if y >= 0:
            leg_index = 0   # left side uses FL offset
        else:
            leg_index = 1   # right side uses FR offset

        theta_raw = self.side_angle(position)
        theta = theta_raw - self.theta0[leg_index]

        # mirror right side if needed
        if y < 0:
            theta = -theta

        # 2. Reduce to 2D
        zp = z*cos(theta) - y*sin(theta)
        # r = sqrt(y*y + z*z)
        
        # leg_height
        d = sqrt(x*x + zp*zp)

        # 3. Knee
        c2 = (self.thigh**2 + self.lower_leg**2 - d**2) / (2*self.thigh*self.lower_leg)
        c2 = max(-1, min(1, c2))
        beta = acos(c2)

        # 4. Hip pitch
        c3 = (self.thigh**2 + d**2 - self.lower_leg**2) / (2*self.thigh*d)
        c3 = max(-1, min(1, c3))
        alpha = acos(c3)

        base = atan2(-zp, x)
        hip_pitch = base + alpha

        return (theta, pi - hip_pitch, pi - beta)
    
    # for converting global coordinates to local coordinates
    def to_local(self, global_pos, hip_offset):
        return [g - h for g, h in zip(global_pos, hip_offset)]
    
    # for going forward and coming back in a straight line
    def linear_bezier(self, start, end, t):
        # return np.array(start) + t * (np.array(end) - np.array(start))
        return ((1 - t) * np.array(start)) + (t * np.array(end))

    # for going forward and coming back in a curved line
    def quadratic_bezier(self, start, middle, end, t):
        return (1-t)**2 * np.array(start) + 2 * (1-t) * t * np.array(middle) + t**2 * np.array(end)

    def call_calculate_joint_position(self):
        speed = abs(self.linear_velocity)

        if speed < 0.01:
            dt = self.base_dt
        else:
            speed = max(5.0, min(speed, 8.0))
            dt = self.base_dt * speed

        t = min(self.t, 1.0)
        self.t += dt
        finished_cycle = self.t >= 1.0

        def leg_slice(i):
            return slice(i * 3, i * 3 + 3)

        def local(arr, i):
            s = leg_slice(i)
            return self.to_local(arr[s], self.hip_offset[s])

        def set_leg(i, pos):
            self.current_positions[leg_slice(i)] = self.calc(pos)

        if self.linear_velocity == 0.0 and self.angular_velocity == 0.0 and not self.is_standing:

            if self.step % 2 == 0:
                # FL BR were at end
                set_leg(0, self.linear_bezier(local(self.end, 0), self.to_local(self.standing[0:3], self.hip_offset[0:3]), t))
                set_leg(3, self.linear_bezier(local(self.end, 3), self.to_local(self.standing[9:12], self.hip_offset[9:12]), t))

                # FR BL were at start
                set_leg(1, self.linear_bezier(local(self.start, 1), self.to_local(self.standing[3:6], self.hip_offset[3:6]), t))
                set_leg(2, self.linear_bezier(local(self.start, 2), self.to_local(self.standing[6:9], self.hip_offset[6:9]), t))

            else:
                # FL BR were at start
                set_leg(0, self.linear_bezier(local(self.start, 0), self.to_local(self.standing[0:3], self.hip_offset[0:3]), t))
                set_leg(3, self.linear_bezier(local(self.start, 3), self.to_local(self.standing[9:12], self.hip_offset[9:12]), t))

                # FR BL were at end
                set_leg(1, self.linear_bezier(local(self.end, 1), self.to_local(self.standing[3:6], self.hip_offset[3:6]), t))
                set_leg(2, self.linear_bezier(local(self.end, 2), self.to_local(self.standing[6:9], self.hip_offset[6:9]), t))

            if finished_cycle:
                self.is_standing = True

        elif self.linear_velocity != 0.0:
            
            if self.linear_velocity > 0:
            
                if self.is_standing:
                    set_leg(0, self.linear_bezier(local(self.standing, 0), local(self.start, 0), t))
                    set_leg(3, self.linear_bezier(local(self.standing, 3), local(self.start, 3), t))

                    set_leg(1, self.linear_bezier(local(self.standing, 1), local(self.end, 1), t))
                    set_leg(2, self.linear_bezier(local(self.standing, 2), local(self.end, 2), t))

                    if finished_cycle:
                        self.is_standing = False

                else:
                    if self.step % 2 == 0:
                        set_leg(0, self.linear_bezier(local(self.end, 0), local(self.start, 0), t))
                        set_leg(3, self.linear_bezier(local(self.end, 3), local(self.start, 3), t))

                        set_leg(1, self.quadratic_bezier(local(self.start, 1), local(self.middle, 1), local(self.end, 1), t))
                        set_leg(2, self.quadratic_bezier(local(self.start, 2), local(self.middle, 2), local(self.end, 2), t))

                    else:
                        set_leg(1, self.linear_bezier(local(self.end, 1), local(self.start, 1), t))
                        set_leg(2, self.linear_bezier(local(self.end, 2), local(self.start, 2), t))

                        set_leg(0, self.quadratic_bezier(local(self.start, 0), local(self.middle, 0), local(self.end, 0), t))
                        set_leg(3, self.quadratic_bezier(local(self.start, 3), local(self.middle, 3), local(self.end, 3), t))

                    if finished_cycle:
                        self.step += 1
                        
            else:
                
                if self.is_standing:
                    set_leg(0, self.linear_bezier(local(self.standing, 0), local(self.end, 0), t))
                    set_leg(3, self.linear_bezier(local(self.standing, 3), local(self.end, 3), t))

                    set_leg(1, self.linear_bezier(local(self.standing, 1), local(self.start, 1), t))
                    set_leg(2, self.linear_bezier(local(self.standing, 2), local(self.start, 2), t))

                    if finished_cycle:
                        self.is_standing = False

                else:
                    if self.step % 2 == 0:
                        set_leg(0, self.linear_bezier(local(self.start, 0), local(self.end, 0), t))
                        set_leg(3, self.linear_bezier(local(self.start, 3), local(self.end, 3), t))

                        set_leg(1, self.quadratic_bezier(local(self.end, 1), local(self.middle, 1), local(self.start, 1), t))
                        set_leg(2, self.quadratic_bezier(local(self.end, 2), local(self.middle, 2), local(self.start, 2), t))

                    else:
                        set_leg(1, self.linear_bezier(local(self.start, 1), local(self.end, 1), t))
                        set_leg(2, self.linear_bezier(local(self.start, 2), local(self.end, 2), t))

                        set_leg(0, self.quadratic_bezier(local(self.end, 0), local(self.middle, 0), local(self.start, 0), t))
                        set_leg(3, self.quadratic_bezier(local(self.end, 3), local(self.middle, 3), local(self.start, 3), t))

                    if finished_cycle:
                        self.step += 1
                        
        elif self.angular_velocity != 0.0:
            
            if self.angular_velocity > 0:
            
                if self.is_standing:
                    set_leg(0, self.linear_bezier(local(self.standing, 0), local(self.end, 0), t))
                    set_leg(3, self.linear_bezier(local(self.standing, 3), local(self.start, 3), t))

                    set_leg(1, self.linear_bezier(local(self.standing, 1), local(self.start, 1), t))
                    set_leg(2, self.linear_bezier(local(self.standing, 2), local(self.end, 2), t))

                    if finished_cycle:
                        self.is_standing = False

                else:
                    if self.step % 2 == 0:
                        set_leg(0, self.linear_bezier(local(self.start, 0), local(self.end, 0), t))
                        set_leg(3, self.linear_bezier(local(self.end, 3), local(self.start, 3), t))

                        set_leg(1, self.quadratic_bezier(local(self.start, 1), local(self.middle, 1), local(self.end, 1), t))
                        set_leg(2, self.quadratic_bezier(local(self.end, 2), local(self.middle, 2), local(self.start, 2), t))

                    else:
                        set_leg(1, self.linear_bezier(local(self.end, 1), local(self.start, 1), t))
                        set_leg(2, self.linear_bezier(local(self.start, 2), local(self.end, 2), t))

                        set_leg(0, self.quadratic_bezier(local(self.end, 0), local(self.middle, 0), local(self.start, 0), t))
                        set_leg(3, self.quadratic_bezier(local(self.start, 3), local(self.middle, 3), local(self.end, 3), t))

                    if finished_cycle:
                        self.step += 1
                        
            else:
                
                if self.is_standing:
                    set_leg(0, self.linear_bezier(local(self.standing, 0), local(self.end, 0), t))
                    set_leg(3, self.linear_bezier(local(self.standing, 3), local(self.start, 3), t))

                    set_leg(1, self.linear_bezier(local(self.standing, 1), local(self.start, 1), t))
                    set_leg(2, self.linear_bezier(local(self.standing, 2), local(self.end, 2), t))

                    if finished_cycle:
                        self.is_standing = False

                else:
                    if self.step % 2 == 0:
                        set_leg(0, self.linear_bezier(local(self.end, 0), local(self.start, 0), t))
                        set_leg(3, self.linear_bezier(local(self.start, 3), local(self.end, 3), t))

                        set_leg(1, self.quadratic_bezier(local(self.end, 1), local(self.middle, 1), local(self.start, 1), t))
                        set_leg(2, self.quadratic_bezier(local(self.start, 2), local(self.middle, 2), local(self.end, 2), t))

                    else:
                        set_leg(1, self.linear_bezier(local(self.end, 1), local(self.start, 1), t))
                        set_leg(2, self.linear_bezier(local(self.start, 2), local(self.end, 2), t))

                        set_leg(0, self.quadratic_bezier(local(self.start, 0), local(self.middle, 0), local(self.end, 0), t))
                        set_leg(3, self.quadratic_bezier(local(self.end, 3), local(self.middle, 3), local(self.start, 3), t))

                    if finished_cycle:
                        self.step += 1

        self.call_publish_positions(self.current_positions)

        if finished_cycle:
            self.t = 0.0
            
    def callback_velocity_changed(self, data: Twist):
        self.linear_velocity = data.linear.x
        self.angular_velocity = data.angular.z
    
    def call_publish_positions(self, positions):
        msg = Positions()
        msg.data = positions
        self.publish_positions.publish(msg)
        
def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__=="__main__":
    main()
