# Test script to verify if all required packages can be imported correctly
try:
    print("Testing imports...")
    
    # Standard libraries
    import os
    import json
    from datetime import datetime
    print("✓ Standard libraries imported successfully")
    
    # Flask and related
    import flask
    from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
    from werkzeug.utils import secure_filename
    print("✓ Flask and related packages imported successfully")
    
    # Environment variables
    from dotenv import load_dotenv
    print("✓ python-dotenv imported successfully")
    
    # OpenCV
    import cv2
    print("✓ OpenCV (cv2) imported successfully")
    
    # Supervision
    import supervision as sv
    print("✓ Supervision imported successfully")
    
    # Roboflow
    from roboflow import Roboflow
    from roboflow.adapters.rfapi import RoboflowError
    print("✓ Roboflow imported successfully")
    
    # Gunicorn (optional, might not be importable on Windows)
    try:
        import gunicorn
        print("✓ Gunicorn imported successfully")
    except ImportError:
        print("⚠ Gunicorn import failed (expected on Windows)")
    
    print("\nAll imports successful! The packages are installed correctly.")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print(f"Package that failed to import: {e.__class__.__module__}")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")