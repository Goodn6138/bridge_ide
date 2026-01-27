"""Test package configuration"""
import pytest
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variables
os.environ['GITHUB_CLIENT_ID'] = 'test_client_id'
os.environ['GITHUB_CLIENT_SECRET'] = 'test_client_secret'
os.environ['JUDGE0_API_KEY'] = 'test_judge0_key'
os.environ['APP_ENV'] = 'test'
