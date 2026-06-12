import cv2
from insightface.app import FaceAnalysis
import json
import time
import numpy as np
import os

app = FaceAnalysis(name="buffalo_l", allowed_modules=['detection', 'recognition'])
app.prepare(ctx_id=-1, det_size=(320, 320))

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

base_color = (255, 255, 255)
check_color = (0, 255, 0)

user_name = input("Enter the name of the user: ")
user_name = user_name.strip().lower()

heading = "Registering New User"
heading_font = cv2.FONT_HERSHEY_COMPLEX
heading_scale = 0.75
heading_thickness = 2
(heading_width, heading_height), _ = cv2.getTextSize(heading, heading_font, heading_scale, heading_thickness)

front_captured = False
front_profile = "Look Straight"
front_profile_embedding = None
right_captured = False
right_profile = "Turn Your Head Left"
right_profile_embedding = None
left_captured = False
left_profile = "Turn Your Head Right"
left_profile_embedding = None

left_arrow = "<-"
right_arrow = "->"
arrow_font = cv2.FONT_HERSHEY_COMPLEX
arrow_scale = 1.5
arrow_thickness = 4
(arrow_width, arrow_height), _ = cv2.getTextSize(left_arrow, arrow_font, arrow_scale, arrow_thickness)

start_time = 0
countdown_start_time = 0

def detect_face(frame):
    faces = app.get(frame)
    if len(faces) > 0:
        face = max(faces, key=lambda f: ((f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])))
        embedding = face.embedding
        return embedding
    return None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_height, frame_width = frame.shape[:2]

    current_time = time.time()

    if start_time == 0:
        start_time = current_time
    
    arrow_x = (frame_width - arrow_width) // 8
    arrow_y = frame_height // 2

    if current_time - start_time > 12:
        break
    elif current_time - start_time > 9:
        footer = "Capturing..."
        if not left_captured:
            left_profile_embedding = detect_face(frame)
            left_captured = True
        cv2.putText(frame, right_arrow, (7*arrow_x, arrow_y), arrow_font, arrow_scale, check_color, arrow_thickness)
        cv2.putText(frame, left_arrow, (arrow_x, arrow_y), arrow_font, arrow_scale, check_color, arrow_thickness)
        cv2.ellipse(frame, (frame_width//2, frame_height//2), (110, 150), 0, 0, 360, check_color, 2)
    elif current_time - start_time > 6:
        footer = left_profile
        if not right_captured:
            right_profile_embedding = detect_face(frame)
            right_captured = True
        cv2.putText(frame, right_arrow, (7*arrow_x, arrow_y), arrow_font, arrow_scale, check_color, arrow_thickness)
        cv2.putText(frame, left_arrow, (arrow_x, arrow_y), arrow_font, arrow_scale, base_color, arrow_thickness)
        cv2.ellipse(frame, (frame_width//2, frame_height//2), (110, 150), 0, 0, 360, base_color, 2)
    elif current_time - start_time > 3:
        footer = right_profile
        if not front_captured:
            front_profile_embedding = detect_face(frame)
            front_captured = True
        cv2.putText(frame, right_arrow, (7*arrow_x, arrow_y), arrow_font, arrow_scale, base_color, arrow_thickness)
        cv2.putText(frame, left_arrow, (arrow_x, arrow_y), arrow_font, arrow_scale, check_color, arrow_thickness)
        cv2.ellipse(frame, (frame_width//2, frame_height//2), (110, 150), 0, 0, 360, base_color, 2)
    else:
        footer = front_profile
        cv2.putText(frame, right_arrow, (7*arrow_x, arrow_y), arrow_font, arrow_scale, base_color, arrow_thickness)
        cv2.putText(frame, left_arrow, (arrow_x, arrow_y), arrow_font, arrow_scale, base_color, arrow_thickness)
        cv2.ellipse(frame, (frame_width//2, frame_height//2), (110, 150), 0, 0, 360, check_color, 2)

    heading_x = (frame_width - heading_width) // 2
    heading_y = 35
    cv2.putText(frame, heading, (heading_x, heading_y), heading_font, heading_scale, base_color, heading_thickness)

    if countdown_start_time == 0:
        countdown_start_time = current_time

    timer = f"{3 - int(current_time - countdown_start_time)}"
    timer_font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    timer_scale = 1.5
    timer_thickness = 2
    (timer_width, timer_height), _ = cv2.getTextSize(timer, timer_font, timer_scale, timer_thickness)
    timer_x = (frame_width - timer_width) // 2
    timer_y = frame_height // 2
    cv2.putText(frame, timer, (timer_x, timer_y), timer_font, timer_scale, check_color, timer_thickness)

    if 3 - int(current_time - countdown_start_time) == 0:
        countdown_start_time = 0

    footer_font = cv2.FONT_HERSHEY_COMPLEX
    footer_scale = 0.75
    footer_thickness = 2
    (footer_width, footer_height), _ = cv2.getTextSize(footer, footer_font, footer_scale, footer_thickness)
    footer_x = (frame_width - footer_width) // 2
    footer_y = frame_height - 25
    cv2.putText(frame, footer, (footer_x, footer_y), footer_font, footer_scale, base_color, footer_thickness)

    cv2.imshow("SCRFD Output", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

os.makedirs("faces_database", exist_ok=True)

# need to increase imbeddings for each face to make the system better!

if front_profile_embedding is not None and left_profile_embedding is not None and right_profile_embedding is not None:
    np.save(f"faces_database/{user_name}_front_profile.npy", front_profile_embedding)
    np.save(f"faces_database/{user_name}_left_profile.npy", left_profile_embedding)
    np.save(f"faces_database/{user_name}_right_profile.npy", right_profile_embedding)

    if not os.path.exists("faces_database/faces.json"):
        with open("faces_database/faces.json", "w") as file:
            json.dump([], file)

    with open("faces_database/faces.json", 'r') as file:
        faces_database = json.load(file)

    user = {
        "name": user_name,
        "embeddings": [
            f"{user_name}_front_profile.npy",
            f"{user_name}_left_profile.npy",
            f"{user_name}_right_profile.npy"
        ]
    }
    faces_database.append(user)

    with open("faces_database/faces.json", 'w') as file:
        json.dump(faces_database, file, indent=4)
else:
    print("Failed!")
