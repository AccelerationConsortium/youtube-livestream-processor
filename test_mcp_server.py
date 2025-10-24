#!/usr/bin/env python3
"""
Simple test script to validate the YouTube MCP server implementation.
This script checks that the server can be imported and tools are properly defined.
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_import():
    """Test that the MCP server module can be imported"""
    print("Testing module import...")
    try:
        import youtube_download_mcp
        print("✓ Module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import module: {e}")
        return False

def test_server_structure():
    """Test that the MCP server is properly structured"""
    print("\nTesting server structure...")
    try:
        import youtube_download_mcp
        
        # Check that mcp server exists
        assert hasattr(youtube_download_mcp, 'mcp'), "MCP server not found"
        print("✓ MCP server object exists")
        
        # Check server name
        mcp_server = youtube_download_mcp.mcp
        assert mcp_server.name == "YouTube Downloader", "Incorrect server name"
        print(f"✓ Server name: {mcp_server.name}")
        
        return True
    except Exception as e:
        print(f"✗ Server structure test failed: {e}")
        return False

def test_tools():
    """Test that all expected tools are defined"""
    print("\nTesting tools...")
    expected_tools = [
        'download_video',
        'get_video_metadata',
        'list_playlists',
        'list_playlist_videos',
        'download_playlist_videos'
    ]
    
    try:
        import youtube_download_mcp
        mcp_server = youtube_download_mcp.mcp
        
        # Get list of registered tools
        tools = mcp_server._tools
        tool_names = list(tools.keys())
        
        print(f"Found {len(tool_names)} tools: {', '.join(tool_names)}")
        
        # Check each expected tool
        missing_tools = []
        for tool_name in expected_tools:
            if tool_name not in tool_names:
                missing_tools.append(tool_name)
            else:
                print(f"✓ Tool '{tool_name}' is registered")
        
        if missing_tools:
            print(f"✗ Missing tools: {', '.join(missing_tools)}")
            return False
        
        print(f"✓ All {len(expected_tools)} expected tools are present")
        return True
        
    except Exception as e:
        print(f"✗ Tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_metadata_class():
    """Test the VideoMetadata class"""
    print("\nTesting VideoMetadata class...")
    try:
        import youtube_download_mcp
        
        # Create a test metadata object
        test_data = {
            "id": "test123",
            "title": "Test Video",
            "description": "Test description",
            "duration": 120,
            "uploader": "Test Uploader"
        }
        
        metadata = youtube_download_mcp.VideoMetadata(test_data)
        result = metadata.to_dict()
        
        assert result["id"] == "test123", "ID mismatch"
        assert result["title"] == "Test Video", "Title mismatch"
        print("✓ VideoMetadata class works correctly")
        
        return True
    except Exception as e:
        print(f"✗ VideoMetadata test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("YouTube Download MCP Server - Validation Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_import()))
    
    if results[-1][1]:  # Only continue if import succeeded
        results.append(("Server Structure Test", test_server_structure()))
        results.append(("Tools Test", test_tools()))
        results.append(("VideoMetadata Class Test", test_video_metadata_class()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
