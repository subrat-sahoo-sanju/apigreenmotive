import cv2
import numpy as np
import face_recognition
import json
from PIL import Image
import os

def detect_and_encode_face(image_path):
    """
    Detect face in image and return face encoding.
    Returns: (success, encoding_or_error, face_image_path)
    """
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        
        if len(face_locations) == 0:
            return False, "No face detected in the image", None
        
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please upload image with single face", None
        
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if len(face_encodings) == 0:
            return False, "Could not encode face", None
        
        face_encoding = face_encodings[0].tolist()
        
        top, right, bottom, left = face_locations[0]
        face_image = image[top:bottom, left:right]
        face_image_pil = Image.fromarray(face_image)
        
        face_filename = f"face_{os.path.basename(image_path)}"
        face_path = os.path.join(os.path.dirname(image_path), face_filename)
        face_image_pil.save(face_path)
        
        return True, face_encoding, face_path
        
    except Exception as e:
        return False, f"Error processing image: {str(e)}", None

def compare_faces(known_encoding, unknown_image_path, tolerance=0.6):
    """
    Compare a known face encoding with face in unknown image.
    Returns: (match, confidence, error)
    """
    try:
        unknown_image = face_recognition.load_image_file(unknown_image_path)
        unknown_face_locations = face_recognition.face_locations(unknown_image)
        
        if len(unknown_face_locations) == 0:
            return False, 0.0, "No face detected in verification image"
        
        unknown_encodings = face_recognition.face_encodings(unknown_image, unknown_face_locations)
        
        if len(unknown_encodings) == 0:
            return False, 0.0, "Could not encode face in verification image"
        
        known_encoding_np = np.array(known_encoding)
        unknown_encoding = unknown_encodings[0]
        
        face_distance = face_recognition.face_distance([known_encoding_np], unknown_encoding)[0]
        confidence = 1 - face_distance
        
        is_match = face_distance <= tolerance
        
        return is_match, float(confidence), None
        
    except Exception as e:
        return False, 0.0, f"Error comparing faces: {str(e)}"

def compare_faces_with_all(unknown_image_path, all_students, tolerance=0.6):
    """
    Compare unknown face against all registered students.
    Returns: (best_match_student, confidence, error)
    """
    try:
        unknown_image = face_recognition.load_image_file(unknown_image_path)
        unknown_face_locations = face_recognition.face_locations(unknown_image)
        
        if len(unknown_face_locations) == 0:
            return None, 0.0, "No face detected in verification image"
        
        unknown_encodings = face_recognition.face_encodings(unknown_image, unknown_face_locations)
        
        if len(unknown_encodings) == 0:
            return None, 0.0, "Could not encode face in verification image"
        
        unknown_encoding = unknown_encodings[0]
        
        best_match = None
        best_confidence = 0.0
        
        for student in all_students:
            known_encoding = np.array(json.loads(student.face_encoding))
            face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
            confidence = 1 - face_distance
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = student
        
        is_match = best_confidence >= (1 - tolerance)
        
        if is_match:
            return best_match, float(best_confidence), None
        else:
            return None, float(best_confidence), "No matching student found"
        
    except Exception as e:
        return None, 0.0, f"Error comparing faces: {str(e)}"
