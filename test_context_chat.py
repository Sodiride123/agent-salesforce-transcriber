#!/usr/bin/env python3
"""
Test script for context-aware chat functionality
"""
import requests
import json
import uuid

BASE_URL = "http://localhost:9000"

def test_chat_flow():
    """Test the complete chat flow with context"""
    
    # Generate a test session ID
    session_id = str(uuid.uuid4())
    print(f"Test Session ID: {session_id}\n")
    
    # Test 1: Chat without context (should fail gracefully)
    print("=" * 60)
    print("TEST 1: Chat without uploading audio first")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "session_id": session_id,
            "message": "What did the customer say about pricing?"
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Has Context: {data.get('has_context', False)}")
    print(f"Response: {data.get('message', '')}\n")
    
    # Test 2: Use an existing report to simulate context
    print("=" * 60)
    print("TEST 2: Simulating context with existing report")
    print("=" * 60)
    
    # Get an existing report ID
    reports_response = requests.get(f"{BASE_URL}/api/reports")
    reports = reports_response.json()
    
    if reports:
        report_id = reports[0]['id']
        print(f"Using existing report: {report_id}")
        
        # Manually add report to session (simulating upload)
        # In real scenario, this happens during upload
        # For testing, we'll create a session with context
        
        # We need to upload a file to properly test, but let's test the chat endpoint
        # with a session that has reports
        
        print("\nNote: To fully test, upload an audio file through the UI")
        print("The session will automatically link the report and enable Q&A")
    else:
        print("No existing reports found. Upload an audio file first.")
    
    print("\n" + "=" * 60)
    print("TEST 3: Testing chat endpoint structure")
    print("=" * 60)
    
    # Test with missing session_id
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "Test message"}
    )
    print(f"Without session_id - Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    # Test with empty message
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"session_id": session_id, "message": ""}
    )
    print(f"With empty message - Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    print("\nTo fully test the context-aware chat:")
    print("1. Open the web UI at: https://0011d.app.super.betamyninja.ai")
    print("2. Upload an audio file")
    print("3. Wait for transcription to complete")
    print("4. Ask questions about the call in the chat")
    print("5. The context indicator should show '📄 1 call in context'")

if __name__ == "__main__":
    test_chat_flow()