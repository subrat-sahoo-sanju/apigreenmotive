"""
Test script for Green Motive Face Recognition API
Run this after starting the server with: python run.py
"""
import requests
import os

BASE_URL = "http://localhost:5000/api"

def test_health():
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_register(student_id, name, email, phone, course, image_path):
    print(f"\n=== Registering Student: {name} ===")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None
    
    with open(image_path, 'rb') as img:
        data = {
            'student_id': student_id,
            'name': name,
            'email': email,
            'phone': phone,
            'course': course
        }
        files = {
            'face_image': (os.path.basename(image_path), img, 'image/jpeg')
        }
        
        response = requests.post(f"{BASE_URL}/register", data=data, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.json()

def test_verify(image_path, student_id=None):
    print(f"\n=== Verifying Student ===")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None
    
    with open(image_path, 'rb') as img:
        data = {}
        if student_id:
            data['student_id'] = student_id
        
        files = {
            'face_image': (os.path.basename(image_path), img, 'image/jpeg')
        }
        
        response = requests.post(f"{BASE_URL}/verify", data=data, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.json()

def test_get_students():
    print("\n=== Getting All Students ===")
    response = requests.get(f"{BASE_URL}/students")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_student(student_id):
    print(f"\n=== Getting Student: {student_id} ===")
    response = requests.get(f"{BASE_URL}/students/{student_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("Green Motive API Test Script")
    print("=" * 50)
    
    test_health()
    
    image_path = input("\nEnter path to test image (or press Enter to skip): ").strip()
    
    if image_path and os.path.exists(image_path):
        result = test_register(
            student_id="STU001",
            name="Test Student",
            email="test@example.com",
            phone="1234567890",
            course="Computer Science",
            image_path=image_path
        )
        
        if result and result.get('success'):
            print("\nRegistration successful! Testing verification...")
            test_verify(image_path, student_id="STU001")
            
            print("\nTesting verification without student_id...")
            test_verify(image_path)
    
    test_get_students()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
