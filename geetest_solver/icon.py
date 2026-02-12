import cv2
import numpy as np
import requests
import random
import os
import time
from typing import List


class IconSolver:
    """
    GeeTest V4 Icon Captcha Solver (Hybrid).
    
    Uses ddddocr (YOLO) for robust icon detection, and OpenCV ORB feature matching
    to match question icons (rotated/scaled) against detected crops.
    """

    DEBUG = os.environ.get("GEEKED_DEBUG", "0") == "1"

    def __init__(self, imgs: str, ques: List[str]):
        self.captcha_bytes = self.load_image(f'https://static.geetest.com/{imgs}')
        self.captcha_img = cv2.imdecode(
            np.frombuffer(self.captcha_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        self.ques_urls = [f'https://static.geetest.com/{q}' for q in ques]
        self.ques_imgs = [self._load_icon(url) for url in self.ques_urls]
        
        if self.DEBUG:
            # Save raw inputs for diagnosis
            ts = int(time.time())
            cv2.imwrite(f"debug_captcha_{ts}.jpg", self.captcha_img)
            for i, qimg in enumerate(self.ques_imgs):
                cv2.imwrite(f"debug_ques_{ts}_{i}.png", qimg)

    @staticmethod
    def _log(msg: str):
        if IconSolver.DEBUG:
            print(f"  [IconSolver] {msg}")

    @staticmethod
    def load_image(url: str) -> bytes:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content

    def _load_icon(self, url: str) -> np.ndarray:
        """Load a question icon from URL and return as grayscale image."""
        content = self.load_image(url)
        img = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        
        # Handle PNG with alpha channel
        if img is not None and len(img.shape) == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3] / 255.0
            rgb = img[:, :, :3]
            # Composite onto white background
            white_bg = np.ones_like(rgb) * 255
            composited = (rgb * alpha[:, :, np.newaxis] + white_bg * (1 - alpha[:, :, np.newaxis])).astype(np.uint8)
            img = composited
        
        if img is not None and len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Invert the question icon to match crop polarity (light-on-dark)
            # Question is black-on-transparent -> black-on-white -> invert -> white-on-black
            img = cv2.bitwise_not(img)
            
        return img

    def _match_score(self, icon: np.ndarray, crop: np.ndarray) -> float:
        """
        Compare two images using ORB feature matching.
        Returns a similarity score (higher is better).
        """
        try:
            orb = cv2.ORB_create(nfeatures=500, edgeThreshold=5)
            kp1, des1 = orb.detectAndCompute(icon, None)
            kp2, des2 = orb.detectAndCompute(crop, None)

            if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
                return 0.0

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            
            if not matches:
                return 0.0
                
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Simple heuristic: count good matches
            # Filter matches with distance < 25 (very strict) or relative check
            good_matches = [m for m in matches if m.distance < 64]
            
            if not good_matches:
                return 0.0
                
            score = len(good_matches)
            return float(score)
            
        except Exception as e:
            self._log(f"Match error: {e}")
            return 0.0

    def find_icon_position(self) -> List[List[float]]:
        """
        Find positions of question icons in the captcha image.
        """
        from .dddd_server import dddd_service
        
        # 1. Detect all icons in the captcha image using ddddocr
        self._log(f"Running detection on {len(self.captcha_bytes)} bytes...")
        bboxes = dddd_service.detection(self.captcha_bytes)
        
        h_captcha, w_captcha = self.captcha_img.shape[:2]
        self._log(f"Captcha image: {w_captcha}x{h_captcha}")
        self._log(f"Detected {len(bboxes)} bounding boxes: {bboxes}")

        captcha_gray = cv2.cvtColor(self.captcha_img, cv2.COLOR_BGR2GRAY)
        
        # Extract crops for each bbox
        crops = []
        for i, bbox in enumerate(bboxes):
            x1, y1, x2, y2 = bbox
            # Add small padding
            pad = 2
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w_captcha, x2 + pad)
            y2 = min(h_captcha, y2 + pad) # Fixed y2
            
            crop = captcha_gray[y1:y2, x1:x2]
            crops.append({'id': i, 'bbox': bbox, 'img': crop, 'center': [(x1+x2)/2, (y1+y2)/2]})
            
            if self.DEBUG:
                ts = int(time.time())
                cv2.imwrite(f"debug_crop_{ts}_{i}.png", crop)

        results = []
        used_indices = set()

        # 2. Match each question icon to the best available crop
        for q_idx, q_img in enumerate(self.ques_imgs):
            best_score = -1.0
            best_idx = -1
            
            self._log(f"Matching question {q_idx+1}/{len(self.ques_imgs)} ({q_img.shape}px)...")
            
            for c_idx, crop_data in enumerate(crops):
                if c_idx in used_indices:
                    continue
                
                # Preprocess crop with CLAHE for better contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                crop_enhanced = clahe.apply(crop_data['img'])
                    
                score = self._match_score(q_img, crop_enhanced)
                self._log(f"  vs crop {c_idx} ({crop_data['img'].shape}px): score={score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_idx = c_idx
            
            # Require minimum score? For now accept best > 0.
            if best_idx != -1 and best_score > 0:
                self._log(f"  => Match! Crop {best_idx} (score={best_score:.2f})")
                used_indices.add(best_idx)
                # Convert to GeeTest coords
                cx, cy = crops[best_idx]['center']
                gx = cx * (10000 / w_captcha)
                gy = cy * (10000 / h_captcha)
                results.append([gx, gy])
            else:
                self._log(f"  => No match found! Using random fallback.")
                # Fallback: random unused box or random point
                if len(used_indices) < len(crops):
                    # Pick random unused crop
                    remaining = [i for i in range(len(crops)) if i not in used_indices]
                    fb_idx = random.choice(remaining)
                    used_indices.add(fb_idx)
                    cx, cy = crops[fb_idx]['center']
                    gx = cx * (10000 / w_captcha)
                    gy = cy * (10000 / h_captcha)
                    results.append([gx, gy])
                else:
                    # Random point
                    rx = random.randint(50, w_captcha - 50)
                    ry = random.randint(50, h_captcha - 50)
                    results.append([rx * 10000/w_captcha, ry * 10000/h_captcha])

        return results

    @staticmethod
    def test() -> None:
        print("Use test_solver.py instead.")

if __name__ == '__main__':
    IconSolver.test()
