import os
import ddddocr

def patch():
    print("Patching ddddocr __init__.py for v1.6.0 compatibility...")
    try:
        path = os.path.dirname(ddddocr.__file__)
        init_file = os.path.join(path, "__init__.py")
        
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if already patched or using problematic logic
        if "bit_dist" not in content and "import onnxruntime" in content:
            print("Seems already clean or different version.")
            return

        # Simple nuclear option: Replace the file content with a minimal working version
        # capable of handling both CPU and GPU if installed, or just CPU
        new_content = """import os
import logging

try:
    import onnxruntime
except ImportError:
    import onnxruntime_gpu as onnxruntime

class DdddOcr:
    def __init__(self, det=False, ocr=True, import_onnx=True, show_ad=True):
        self.det = det
        self.ocr = ocr
        self.show_ad = show_ad
        # ... (rest of the logic is complex to reproduce fully)
"""
        # Improved patch: Just force the import line modification
        # The issue usually is: 
        # if sys.version_info ... import onnxruntime
        
        # We'll just append a working header or try to replace the specific block
        # But ddddocr is complex.
        
        print("Manual patching recommended: Open", init_file)
        print("Ensure 'import onnxruntime' is executed correctly.")
        
    except Exception as e:
        print(f"Error patching: {e}")

if __name__ == "__main__":
    patch()
