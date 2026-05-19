# Green Motive - Face Recognition Student System

A Python Flask API for student registration and verification using face recognition.

## Features

- Student registration with face image
- Face detection and encoding
- Student verification by face matching
- RESTful API endpoints
- SQLite database storage

## Project Structure

```
grrenmotive/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── config.py        # Configuration
│   ├── models.py        # Database models
│   ├── routes.py        # API endpoints
│   └── face_utils.py    # Face detection & matching
├── uploads/             # Uploaded images
├── instance/            # Database files
├── requirements.txt     # Python dependencies
└── run.py              # Entry point
```

## Installation

1. Install Python 3.8+

2. Install CMake and Visual Studio Build Tools (required for face-recognition):
   - Download CMake: https://cmake.org/download/
   - Download Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python run.py
```

Server will start at: `http://localhost:5000`

## API Endpoints

### 1. Register Student

**POST** `/api/register`

Form Data:
- `student_id` (required): Unique student ID
- `name` (required): Student name
- `email` (required): Student email
- `phone` (optional): Phone number
- `course` (optional): Course name
- `face_image` (required): Face image file (png, jpg, jpeg)

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/register \
  -F "student_id=STU001" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "phone=1234567890" \
  -F "course=Computer Science" \
  -F "face_image=@path/to/face.jpg"
```

**Example using JavaScript (React):**
```javascript
const formData = new FormData();
formData.append('student_id', 'STU001');
formData.append('name', 'John Doe');
formData.append('email', 'john@example.com');
formData.append('phone', '1234567890');
formData.append('course', 'Computer Science');
formData.append('face_image', faceFile);

const response = await fetch('http://localhost:5000/api/register', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

**Response:**
```json
{
  "success": true,
  "message": "Student registered successfully",
  "data": {
    "id": 1,
    "student_id": "STU001",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "course": "Computer Science",
    "face_image_path": "face_abc123.jpg",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 2. Verify Student (by face only)

**POST** `/api/verify`

Form Data:
- `face_image` (required): Face image to verify

**Example:**
```bash
curl -X POST http://localhost:5000/api/verify \
  -F "face_image=@path/to/verify.jpg"
```

**Response:**
```json
{
  "success": true,
  "verified": true,
  "confidence": 85.5,
  "message": "Student identified successfully",
  "student": {
    "id": 1,
    "student_id": "STU001",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### 3. Verify Student (specific student)

**POST** `/api/verify`

Form Data:
- `face_image` (required): Face image to verify
- `student_id` (required): Student ID to verify against

**Example:**
```bash
curl -X POST http://localhost:5000/api/verify \
  -F "face_image=@path/to/verify.jpg" \
  -F "student_id=STU001"
```

### 4. Get All Students

**GET** `/api/students`

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 5
}
```

### 5. Get Specific Student

**GET** `/api/students/<student_id>`

### 6. Delete Student

**DELETE** `/api/students/<student_id>`

### 7. Health Check

**GET** `/api/health`

## Configuration

Edit `app/config.py` to change:

- `FACE_TOLERANCE`: Face matching strictness (0.6 default, lower = stricter)
- `DETECTION_THRESHOLD`: Confidence threshold
- `MAX_CONTENT_LENGTH`: Max upload size (16MB default)

## React Integration Example

```javascript
// Register student
async function registerStudent(studentData, faceImage) {
  const formData = new FormData();
  formData.append('student_id', studentData.studentId);
  formData.append('name', studentData.name);
  formData.append('email', studentData.email);
  formData.append('phone', studentData.phone);
  formData.append('course', studentData.course);
  formData.append('face_image', faceImage);

  const response = await fetch('http://localhost:5000/api/register', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// Verify student
async function verifyStudent(faceImage, studentId = null) {
  const formData = new FormData();
  formData.append('face_image', faceImage);
  if (studentId) {
    formData.append('student_id', studentId);
  }

  const response = await fetch('http://localhost:5000/api/verify', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}
```

## Troubleshooting

**face-recognition installation fails:**
- Install CMake: `pip install cmake`
- Install Visual Studio Build Tools (Windows)
- Try: `pip install --upgrade pip` then `pip install face-recognition`

**No face detected:**
- Ensure good lighting
- Face should be clearly visible
- Image should be at least 100x100 pixels
- Only one face per image for registration
