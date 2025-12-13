import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("=" * 60)
        print("ED Multi Route Navigation (EDMRN) v2.3.0")
        print("=" * 60)
        
        from edmrn.app import EDMRN_App
        
        app = EDMRN_App()
        app.run()
        
    except Exception as e:
        print(f"\n[ERROR] Application could not be started: {e}")
        import traceback
        traceback.print_exc()
        
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()