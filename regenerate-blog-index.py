#!/usr/bin/env python3
"""
Regenerate Blog Index
Simple script to regenerate the blog index from the /blog/ directory.
Use this when you want to update the blog index without running the full GitHub generator.
"""

import subprocess
import sys

def main():
    """Regenerate the blog index."""
    print("Regenerating Blog Index")
    print("=======================")
    
    try:
        # Run the dynamic blog index generator
        result = subprocess.run(['python3', 'dynamic-blog-index.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Blog index regenerated successfully!")
            print("\nThe blog index now reflects all posts in the /blog/ directory.")
        else:
            print(f"\n❌ Error regenerating blog index:")
            print(result.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Error: dynamic-blog-index.py not found")
        print("Make sure you're in the correct directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
