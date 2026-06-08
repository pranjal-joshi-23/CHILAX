#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from deepface import DeepFace
import numpy as np

class MyNode(Node):
    def __init__(self):
        super().__init__("vision")
        self.frame_before = self.create_subscription(Image, "/camera/image_raw", self.image_processing, 10)
        self.bridge = CvBridge()
        self.frame_after = self.create_publisher(Image, "/camera/image_edited", 10)
        
    def image_processing(self, data: Image):
        # ros to cv
        frame_raw = self.bridge.imgmsg_to_cv2(data, desired_encoding='bgr8')
        
        # processing here
        cv2.putText(frame_raw, "Processed Frame", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # cv to ros
        frame_modified = self.bridge.cv2_to_imgmsg(frame_raw, encoding='bgr8')
        self.call_image_publisher(frame_modified)
        
    def call_detect_faces(self, frame):
        alg = "cascades/haarcascade_frontalface_default.xml"
        
        haar_cascade = cv2.CascadeClassifier(alg)
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        faces = haar_cascade.detectMultiScale(
            gray_frame, scaleFactor=1.05, minNeighbors=4, minSize=(100, 100)
        )

        i = 0
        for x, y, w, h in faces:
            # crop the image to select only the face
            cropped_image = frame[y : y + h, x : x + w]
            # loading the target image path into target_file_name variable  - replace <INSERT YOUR TARGET IMAGE NAME HERE> with the path to your target image
            target_file_name = 'stored-faces/' + str(i) + '.jpg'
            cv2.imwrite(
                target_file_name,
                cropped_image,
            )
            i = i + 1;

    def call_create_embedding(self, frame):
        embedding_objs = DeepFace.represent(
            img_path=frame, 
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True
        )
        
        embedding_vector = embedding_objs[0]["embedding"]
        
        return embedding_vector
    
    def call_recognize_faces(self, frame, db):
        vec1 = np.array(frame)
        vec2 = np.array(embedding2)
        
        # Formula: (A • B) / (||A|| * ||B||)
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        cosine_similarity = dot_product / (norm_a * norm_b)
        return cosine_similarity
        
    def call_image_publisher(self, frame):
        frame_modified = Image()
        frame_modified.header = frame.header
        self.frame_after.publish(frame_modified)
        
def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    rclpy.shutdown()
    
if __name__=="__main__":
    main()
