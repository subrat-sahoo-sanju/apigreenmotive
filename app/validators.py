import re
import os
import cv2
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (allows high-res mobile photos)
MIN_FILE_SIZE = 1024  # 1KB
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200
MAX_IMAGE_WIDTH = 10000  # Increased for high-res mobile cameras
MAX_IMAGE_HEIGHT = 10000  # Increased for high-res mobile cameras
MIN_FACE_SIZE = 80  # Minimum face size in pixels

STUDENT_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,50}$')
NAME_PATTERN = re.compile(r'^[A-Za-z\s\.\'-]{2,100}$')
PHONE_PATTERN = re.compile(r'^\+?[0-9\s\-\(\)]{7,20}$')

ALLOWED_PIL_FORMATS = {'JPEG', 'PNG'}


class ValidationError:
    def __init__(self):
        self.errors = {}

    def add(self, field, message):
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)

    def has_errors(self):
        return len(self.errors) > 0

    def to_response(self):
        error_messages = []
        for field, messages in self.errors.items():
            for msg in messages:
                error_messages.append(f"{field}: {msg}")
        return {
            'success': False,
            'message': 'Validation failed',
            'errors': self.errors,
            'error_details': '; '.join(error_messages)
        }


def validate_email(email):
    if not email:
        return 'Email is required'
    email = email.strip()
    if len(email) > 120:
        return 'Email must be less than 120 characters'
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not pattern.match(email):
        return 'Invalid email format'
    return None


def validate_student_id(student_id):
    if not student_id:
        return 'Student ID is required'
    student_id = student_id.strip()
    if not STUDENT_ID_PATTERN.match(student_id):
        return 'Student ID must be 3-50 characters, only letters, numbers, hyphens, underscores'
    return None


def validate_name(name):
    if not name:
        return 'Name is required'
    name = name.strip()
    if len(name) < 2:
        return 'Name must be at least 2 characters'
    if len(name) > 100:
        return 'Name must be less than 100 characters'
    if not NAME_PATTERN.match(name):
        return 'Name contains invalid characters'
    return None


def validate_phone(phone):
    if not phone:
        return None
    phone = phone.strip()
    if not PHONE_PATTERN.match(phone):
        return 'Invalid phone number format'
    return None


def validate_course(course):
    if not course:
        return None
    course = course.strip()
    if len(course) > 100:
        return 'Course must be less than 100 characters'
    return None


def validate_file_extension(filename):
    if not filename:
        return 'File name is missing'
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
    return None


def validate_file_size(file):
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size < MIN_FILE_SIZE:
        return f'File too small. Minimum size: {MIN_FILE_SIZE // 1024}KB'
    if size > MAX_FILE_SIZE:
        return f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
    return None


def validate_image_content(file_path):
    try:
        with Image.open(file_path) as pil_img:
            if pil_img.format not in ALLOWED_PIL_FORMATS:
                return 'File is not a valid image (must be JPEG or PNG)'
    except Exception:
        return 'File is not a valid image or is corrupted'

    img = cv2.imread(file_path)
    if img is None:
        return 'Cannot read image file. File may be corrupted'

    height, width = img.shape[:2]

    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
        return f'Image too small. Minimum: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} pixels. Got: {width}x{height}'

    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        return f'Image too large. Maximum: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} pixels. Got: {width}x{height}'

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()

    if brightness < 40:
        return 'Image too dark. Please use better lighting'
    if brightness > 230:
        return 'Image too bright. Please reduce lighting'

    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 20:
        return 'Image is too blurry. Please upload a clearer image'

    return None


def validate_face_quality(image_path):
    import face_recognition

    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) == 0:
        return False, 'No face detected. Please ensure face is clearly visible', None

    if len(face_locations) > 1:
        return False, 'Multiple faces detected. Upload image with only one face', None

    top, right, bottom, left = face_locations[0]
    face_height = bottom - top
    face_width = right - left

    if face_height < MIN_FACE_SIZE or face_width < MIN_FACE_SIZE:
        return False, 'Face too small in image. Face should be clearly visible', None

    face_image = image[top:bottom, left:right]
    gray_face = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
    face_brightness = gray_face.mean()

    if face_brightness < 50:
        return False, 'Face is too dark. Please improve lighting', None

    face_blur = cv2.Laplacian(gray_face, cv2.CV_64F).var()
    if face_blur < 10:
        return False, 'Face is blurry. Please upload a sharper image', None

    face_encodings = face_recognition.face_encodings(image, face_locations)
    if len(face_encodings) == 0:
        return False, 'Could not extract face features. Try a different image', None

    return True, None, face_encodings[0].tolist()


def validate_register_request(request):
    errors = ValidationError()

    if 'face_image' not in request.files:
        errors.add('face_image', 'No face image provided')
        return errors, None, None, None, None, None

    file = request.files['face_image']

    if file.filename == '':
        errors.add('face_image', 'No file selected')
        return errors, None, None, None, None, None

    ext_error = validate_file_extension(file.filename)
    if ext_error:
        errors.add('face_image', ext_error)

    size_error = validate_file_size(file)
    if size_error:
        errors.add('face_image', size_error)

    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    course = request.form.get('course', '').strip()

    sid_error = validate_student_id(student_id)
    if sid_error:
        errors.add('student_id', sid_error)

    name_error = validate_name(name)
    if name_error:
        errors.add('name', name_error)

    email_error = validate_email(email)
    if email_error:
        errors.add('email', email_error)

    phone_error = validate_phone(phone)
    if phone_error:
        errors.add('phone', phone_error)

    course_error = validate_course(course)
    if course_error:
        errors.add('course', course_error)

    return errors, student_id, name, email, phone, course


def validate_verify_request(request):
    errors = ValidationError()

    if 'face_image' not in request.files:
        errors.add('face_image', 'No face image provided')
        return errors, None

    file = request.files['face_image']

    if file.filename == '':
        errors.add('face_image', 'No file selected')
        return errors, None

    ext_error = validate_file_extension(file.filename)
    if ext_error:
        errors.add('face_image', ext_error)

    size_error = validate_file_size(file)
    if size_error:
        errors.add('face_image', size_error)

    student_id = request.form.get('student_id', '').strip()
    if student_id:
        sid_error = validate_student_id(student_id)
        if sid_error:
            errors.add('student_id', sid_error)

    return errors, student_id


def validate_update_request(request):
    errors = ValidationError()

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    course = request.form.get('course', '').strip()

    if name:
        name_error = validate_name(name)
        if name_error:
            errors.add('name', name_error)

    if email:
        email_error = validate_email(email)
        if email_error:
            errors.add('email', email_error)

    if phone:
        phone_error = validate_phone(phone)
        if phone_error:
            errors.add('phone', phone_error)

    if course:
        course_error = validate_course(course)
        if course_error:
            errors.add('course', course_error)

    has_face = 'face_image' in request.files and request.files['face_image'].filename != ''
    if has_face:
        file = request.files['face_image']
        ext_error = validate_file_extension(file.filename)
        if ext_error:
            errors.add('face_image', ext_error)
        size_error = validate_file_size(file)
        if size_error:
            errors.add('face_image', size_error)

    return errors, name, email, phone, course, has_face
