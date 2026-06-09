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

known_users = []

for user in faces_database:
    embeddings = [np.load(f"faces_database/{profile}") for profile in user['embeddings']]

    known_users.append({
        "name": user['name'],
        "embeddings": embeddings
    })

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

COLORS = [
    (118, 117, 56), (198, 195, 80), (71, 181, 85), 
    (174, 158, 69), (161, 196, 106)
]
random_color = random.randint(0, 4)

last_known_face = None
current_frame = 5
frame_interval = 5

user_label = "Unknown User!"

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
            embedding = last_known_face.embedding

            best_score = 0
            best_score_user = "Unknown User!"

            for user in known_users:
                front_profile_embedding = user['embeddings'][0]
                right_profile_embedding = user['embeddings'][1]
                left_profile_embedding = user['embeddings'][2]
                front_embedding_score = cosine_similarity(front_profile_embedding, embedding)
                right_embedding_score = cosine_similarity(right_profile_embedding, embedding)
                left_embedding_score = cosine_similarity(left_profile_embedding, embedding)

                score = max(front_embedding_score, right_embedding_score, left_embedding_score)

                if score >= best_score:
                    best_score = score
                    best_score_user = user["name"].capitalize()
            
            if best_score >= 0.55:
                user_label = best_score_user
            else:
                user_label = "Unknown User!"
        else:
            last_known_face = None
            user_label = "Unknown User!"
        current_frame = 0

    if last_known_face is not None:
        bbox = last_known_face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        
        confidence = last_known_face.det_score
        if confidence < 0.5:
            continue
            
        color = COLORS[random_color]
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(frame, user_label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("SCRFD Output", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
