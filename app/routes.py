from flask import Blueprint, request, jsonify, current_app
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from .models import db, Student
from .validators import (
    validate_register_request,
    validate_verify_request,
    validate_update_request,
    validate_image_content,
    validate_face_quality
)
from .face_utils import detect_and_encode_face, compare_faces, compare_faces_with_all

api = Blueprint('api', __name__)


def _delete_upload_file(filename, upload_path):
    if filename:
        full_path = os.path.join(upload_path, filename)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass


@api.route('/register', methods=['POST'])
def register_student():
    try:
        errors, student_id, name, email, phone, course = validate_register_request(request)

        if errors.has_errors():
            return jsonify(errors.to_response()), 400

        existing_student = Student.query.filter(
            (Student.student_id == student_id) | (Student.email == email)
        ).first()

        if existing_student:
            return jsonify({
                'success': False,
                'message': 'Student already exists',
                'errors': {
                    'student_id': ['Student ID already registered'] if existing_student.student_id == student_id else [],
                    'email': ['Email already registered'] if existing_student.email == email else []
                }
            }), 409

        file = request.files['face_image']
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_path = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_path, unique_filename)

        file.save(file_path)

        content_error = validate_image_content(file_path)
        if content_error:
            _delete_upload_file(unique_filename, upload_path)
            return jsonify({
                'success': False,
                'message': 'Image validation failed',
                'errors': {'face_image': [content_error]}
            }), 400

        face_valid, face_error, face_encoding = validate_face_quality(file_path)

        if not face_valid:
            _delete_upload_file(unique_filename, upload_path)
            return jsonify({
                'success': False,
                'message': 'Face validation failed',
                'errors': {'face_image': [face_error]}
            }), 400

        new_student = Student(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            course=course,
            face_image_path=unique_filename,
            face_encoding=json.dumps(face_encoding)
        )

        db.session.add(new_student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student registered successfully',
            'data': new_student.to_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Student with this ID or email already exists'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error registering student: {str(e)}'
        }), 500


@api.route('/verify', methods=['POST'])
def verify_student():
    try:
        errors, student_id = validate_verify_request(request)

        if errors.has_errors():
            return jsonify(errors.to_response()), 400

        file = request.files['face_image']
        filename = secure_filename(file.filename)
        unique_filename = f"verify_{uuid.uuid4().hex}_{filename}"
        upload_path = current_app.config['UPLOAD_FOLDER']
        verify_path = os.path.join(upload_path, unique_filename)

        file.save(verify_path)

        content_error = validate_image_content(verify_path)
        if content_error:
            _delete_upload_file(unique_filename, upload_path)
            return jsonify({
                'success': False,
                'message': 'Image validation failed',
                'errors': {'face_image': [content_error]}
            }), 400

        face_valid, face_error, _ = validate_face_quality(verify_path)
        if not face_valid:
            _delete_upload_file(unique_filename, upload_path)
            return jsonify({
                'success': False,
                'message': 'Face validation failed',
                'errors': {'face_image': [face_error]}
            }), 400

        tolerance = current_app.config['FACE_TOLERANCE']

        if student_id:
            student = Student.query.filter_by(student_id=student_id, is_active=True).first()

            if not student:
                _delete_upload_file(unique_filename, upload_path)
                return jsonify({
                    'success': False,
                    'message': 'Student not found',
                    'errors': {'student_id': ['Student ID does not exist']}
                }), 404

            is_match, confidence, error = compare_faces(
                json.loads(student.face_encoding),
                verify_path,
                tolerance
            )

            _delete_upload_file(unique_filename, upload_path)

            if error:
                return jsonify({
                    'success': False,
                    'message': error
                }), 400

            return jsonify({
                'success': True,
                'verified': is_match,
                'confidence': round(confidence * 100, 2),
                'message': 'Face verified successfully' if is_match else 'Face does not match',
                'student': student.to_dict() if is_match else None
            }), 200

        else:
            all_students = Student.query.filter_by(is_active=True).all()

            if not all_students:
                _delete_upload_file(unique_filename, upload_path)
                return jsonify({
                    'success': False,
                    'message': 'No registered students found'
                }), 404

            best_match, confidence, error = compare_faces_with_all(
                verify_path,
                all_students,
                tolerance
            )

            _delete_upload_file(unique_filename, upload_path)

            if not best_match:
                return jsonify({
                    'success': True,
                    'verified': False,
                    'confidence': round(confidence * 100, 2),
                    'message': error or 'No matching student found'
                }), 200

            return jsonify({
                'success': True,
                'verified': True,
                'confidence': round(confidence * 100, 2),
                'message': 'Student identified successfully',
                'student': best_match.to_dict()
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error verifying student: {str(e)}'
        }), 500


@api.route('/students', methods=['GET'])
def get_students():
    try:
        students = Student.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [student.to_dict() for student in students],
            'count': len(students)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching students: {str(e)}'
        }), 500


@api.route('/students/<student_id>', methods=['GET'])
def get_student(student_id):
    try:
        if not student_id or not student_id.strip():
            return jsonify({
                'success': False,
                'message': 'Student ID is required',
                'errors': {'student_id': ['Student ID cannot be empty']}
            }), 400

        student = Student.query.filter_by(student_id=student_id, is_active=True).first()

        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404

        return jsonify({
            'success': True,
            'data': student.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching student: {str(e)}'
        }), 500


@api.route('/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        if not student_id or not student_id.strip():
            return jsonify({
                'success': False,
                'message': 'Student ID is required'
            }), 400

        student = Student.query.filter_by(student_id=student_id, is_active=True).first()

        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404

        errors, name, email, phone, course, has_face = validate_update_request(request)

        if errors.has_errors():
            return jsonify(errors.to_response()), 400

        if not any([name, email, phone, course, has_face]):
            return jsonify({
                'success': False,
                'message': 'No fields provided for update'
            }), 400

        if email and email != student.email:
            existing = Student.query.filter_by(email=email).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Email already in use by another student',
                    'errors': {'email': ['Email already registered']}
                }), 409

        if name:
            student.name = name
        if email:
            student.email = email
        if phone is not None:
            student.phone = phone if phone else student.phone
        if course is not None:
            student.course = course if course else student.course

        if has_face:
            upload_path = current_app.config['UPLOAD_FOLDER']
            file = request.files['face_image']
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_path, unique_filename)
            file.save(file_path)

            content_error = validate_image_content(file_path)
            if content_error:
                _delete_upload_file(unique_filename, upload_path)
                return jsonify({
                    'success': False,
                    'message': 'Image validation failed',
                    'errors': {'face_image': [content_error]}
                }), 400

            face_valid, face_error, face_encoding = validate_face_quality(file_path)
            if not face_valid:
                _delete_upload_file(unique_filename, upload_path)
                return jsonify({
                    'success': False,
                    'message': 'Face validation failed',
                    'errors': {'face_image': [face_error]}
                }), 400

            old_image = student.face_image_path
            student.face_image_path = unique_filename
            student.face_encoding = json.dumps(face_encoding)
            _delete_upload_file(old_image, upload_path)

        student.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student updated successfully',
            'data': student.to_dict()
        }), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Update failed due to a conflict with existing data'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating student: {str(e)}'
        }), 500


@api.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        if not student_id or not student_id.strip():
            return jsonify({
                'success': False,
                'message': 'Student ID is required',
                'errors': {'student_id': ['Student ID cannot be empty']}
            }), 400

        student = Student.query.filter_by(student_id=student_id, is_active=True).first()

        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404

        upload_path = current_app.config['UPLOAD_FOLDER']
        _delete_upload_file(student.face_image_path, upload_path)

        student.is_active = False
        student.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting student: {str(e)}'
        }), 500


@api.route('/health', methods=['GET'])
def health_check():
    try:
        student_count = Student.query.filter_by(is_active=True).count()
        return jsonify({
            'status': 'healthy',
            'message': 'Green Motive Face Recognition API is running',
            'registered_students': student_count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'message': f'API running but database issue: {str(e)}'
        }), 200
