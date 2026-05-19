from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("Green Motive - Face Recognition API")
    print("=" * 50)
    print("Server starting...")
    print("API Endpoints:")
    print("  POST /api/register  - Register student with face")
    print("  POST /api/verify    - Verify student by face")
    print("  GET  /api/students  - Get all students")
    print("  GET  /api/students/<id> - Get specific student")
    print("  DELETE /api/students/<id> - Delete student")
    print("  GET  /api/health    - Health check")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
