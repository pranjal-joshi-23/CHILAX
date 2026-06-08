import cv2
from insightface.app import FaceAnalysis
import random
import json
import os
import numpy as np
from numpy.linalg import norm

app = FaceAnalysis(name="buffalo_l", allowed_modules=['detection', 'recognition'])
app.prepare(ctx_id=-1, det_size=(320, 320))

with open("faces_database/faces.json", 'r') as file:
    faces_database = json.load(file)

for info in faces_database:
    print(info)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

COLORS = [
    (118, 117, 56), (198, 195, 80), (71, 181, 85), 
    (174, 158, 69), (161, 196, 106)
]
random_color = random.randint(0, 4)

last_known_face = []
current_frame = 5
frame_interval = 5

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    
    current_frame += 1
    if current_frame >= frame_interval:
        faces = app.get(frame)
        if len(faces) > 0:
            last_known_face = max(faces, key=lambda f: ((f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])))
        else:
            last_known_face = []
        current_frame = 0

    if len(last_known_face)>0:
        embedding = last_known_face.embedding
        bbox = last_known_face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        
        confidence = last_known_face.det_score
        if confidence < 0.5:
            continue
            
        color = COLORS[random_color]
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        label = "Unkown User!"

        for user in faces_database:
            front_profile_embedding = np.load(f"faces_database/{user['embeddings'][0]}")
            right_profile_embedding = np.load(f"faces_database/{user['embeddings'][1]}")
            left_profile_embedding = np.load(f"faces_database/{user['embeddings'][2]}")
            front_embedding_score = cosine_similarity(front_profile_embedding, embedding)
            right_embedding_score = cosine_similarity(right_profile_embedding, embedding)
            left_embedding_score = cosine_similarity(left_profile_embedding, embedding)

            if front_embedding_score >= 0.55 or right_embedding_score >= 0.55 or left_embedding_score >= 0.55:
                label = user["name"].capitalize()
        
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("SCRFD Output", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
