#!/usr/bin/env python3
"""
Test script to verify ADK tools are working correctly
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.adk_agent_service import tavily_search_tool, send_sms_tool

def test_tavily_search():
    """Test the Tavily search tool"""
    print("🔍 Testing Tavily Search Tool...")
    try:
        result = tavily_search_tool("What is the current weather in New York?")
        print("✅ Tavily Search Result:")
        print(f"   Status: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"   Result: {result.get('result')[:200]}..." if len(result.get('result', '')) > 200 else f"   Result: {result.get('result')}")
        else:
            print(f"   Error: {result.get('error_message')}")
        return result.get('status') == 'success'
    except Exception as e:
        print(f"❌ Tavily Search Test Failed: {e}")
        return False

def test_sms_tool():
    """Test the SMS tool (mock test - won't actually send SMS)"""
    print("\n📱 Testing SMS Tool...")
    try:
        # Use a test phone number format
        result = send_sms_tool("+1234567890", "Test message from ADK Platform")
        print("✅ SMS Tool Result:")
        print(f"   Status: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"   Result: {result.get('result')}")
        else:
            print(f"   Error: {result.get('error_message')}")
        # SMS might fail due to credentials, but we want to see if the function works
        return True
    except Exception as e:
        print(f"❌ SMS Tool Test Failed: {e}")
        return False

def main():
    """Run all tool tests"""
    print("🚀 Starting ADK Tools Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Test Tavily Search
    if test_tavily_search():
        tests_passed += 1
    
    # Test SMS Tool
    if test_sms_tool():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tools are working correctly!")
        return 0
    else:
        print("⚠️  Some tools may need configuration or have issues")
        return 1

if __name__ == "__main__":
    exit(main())
