import os
import pathlib


root_dir = pathlib.Path(__file__).resolve().parent.parent
onnx_path = os.path.join(root_dir, 'geeked', 'models', 'geetest_v4_icon.onnx')
charsets_path = os.path.join(root_dir, 'geeked', 'models', 'charsets.json')


class DdddService:
    def __init__(self):
        import ddddocr
        self.det = ddddocr.DdddOcr(det=True, show_ad=False)
        self.cnn = ddddocr.DdddOcr(det=False, ocr=False,
                                   show_ad=False,
                                   import_onnx_path=onnx_path,
                                   charsets_path=charsets_path)

    def detection(self, img):
        return self.det.detection(img)

    def classification(self, img):
        return self.cnn.classification(img)


# Lazy-loaded singleton instance for icon.py to import
_dddd_service_instance = None

def _get_dddd_service():
    global _dddd_service_instance
    if _dddd_service_instance is None:
        _dddd_service_instance = DdddService()
    return _dddd_service_instance

class _LazyDdddService:
    """Proxy that lazily initializes DdddService on first use."""
    def __getattr__(self, name):
        return getattr(_get_dddd_service(), name)

dddd_service = _LazyDdddService()
