#!/usr/bin/env python3
"""
Syntax validation test for YouTube MCP server.
Checks Python syntax without importing dependencies.
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(filepath):
    """Validate Python syntax of a file"""
    print(f"Validating syntax of: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            source_code = f.read()
        
        # Try to parse the file as an AST
        ast.parse(source_code)
        print("✓ Syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error found:")
        print(f"  Line {e.lineno}: {e.msg}")
        print(f"  {e.text}")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

def analyze_structure(filepath):
    """Analyze the structure of the Python file"""
    print(f"\nAnalyzing structure of: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            source_code = f.read()
        
        tree = ast.parse(source_code)
        
        # Find function definitions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        print(f"✓ Found {len(classes)} class(es): {', '.join(classes)}")
        print(f"✓ Found {len(functions)} function(s)")
        
        # Find specific tool functions
        tool_functions = [f for f in functions if f in [
            'download_video', 
            'get_video_metadata', 
            'list_playlists',
            'list_playlist_videos',
            'download_playlist_videos'
        ]]
        
        print(f"✓ Found {len(tool_functions)} MCP tool function(s): {', '.join(tool_functions)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error analyzing structure: {e}")
        return False

def main():
    """Run syntax validation"""
    print("=" * 60)
    print("YouTube Download MCP Server - Syntax Validation")
    print("=" * 60)
    print()
    
    filepath = Path(__file__).parent / "youtube_download_mcp.py"
    
    if not filepath.exists():
        print(f"✗ File not found: {filepath}")
        return 1
    
    # Validate syntax
    syntax_valid = validate_python_syntax(filepath)
    
    if not syntax_valid:
        return 1
    
    # Analyze structure
    structure_valid = analyze_structure(filepath)
    
    if not structure_valid:
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All syntax validation checks passed!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
