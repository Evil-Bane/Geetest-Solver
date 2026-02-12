# Geetest Solver

A professional, robust, and customized Python solver for GeeTest v4 captchas. This library is an enhanced version of the original GeekedTest repo, featuring significant improvements in reliability, accuracy, and ease of use.

## 🚀 Key Features

*   **Hybrid Icon Solver:** 
    *   Completely rewritten icon captcha solver using a hybrid approach.
    *   **Robust Detection:** Uses `ddddocr` (YOLO) for accurate icon detection.
    *   **Advanced Matching:** Implements **OpenCV ORB feature matching** with **CLAHE preprocessing** and **polarity inversion** to handle rotated, scaled, and low-contrast icons (e.g., GeekedTest's new random icon sets).
    *   High accuracy (>95% on demo site).
*   **Retry Logic:** Built-in retry mechanism that automatically handles `result: fail` responses from GeeTest by refreshing the challenge and retrying (default 5 attempts).
*   **Full Type Support:** Supports `slide`, `icon`, `ai` (invisible), and `gobang` (experimental) captcha types.
*   **Dev Tools:** Includes utilities for extracting demo parameters and updating JS keys (`dev_tools/`).

## 📦 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Evil-Bane/Geetest-Solver.git
    cd Geetest-Solver
    ```

2.  Install dependencies:
    ```bash
    pip install .
    ```
    *Note: Validated with Python 3.8+.*

## 🛠️ Usage

### Basic Example

```python
from geetest_solver import GeetestSolver

# Configuration
CAPTCHA_ID = "54088bb07d2df3c46b79f80300b0abbe" # Demo ID
RISK_TYPE = "slide" # or "icon", "ai"

# Initialize
solver = GeetestSolver(CAPTCHA_ID, RISK_TYPE)

# Solve
result = solver.solve()
print("Result:", result)
```

### Advanced Usage (Debug & Retries)

```python
from geetest_solver import GeetestSolver

solver = GeetestSolver(
    "YOUR_CAPTCHA_ID", 
    "icon", 
    debug=True  # Enable verbose logging
)

try:
    # Retry up to 10 times if server fails
    result = solver.solve(max_retries=10)
    print("SecCode:", result)
except Exception as e:
    print("Failed to solve:", e)
```

## 📂 Project Structure

*   `geetest_solver/`: Core package containing the solver logic.
    *   `solver.py`: Main `GeetestSolver` class.
    *   `icon.py`: Advanced hybrid icon solver.
    *   `slide.py`: Slide captcha solver.
*   `dev_tools/`: Utilities for developers (e.g., `deobfuscate.py`, `extract_demo_ids.py`).
*   `examples/`: Example scripts.
*   `tests/`: Comprehensive test suite.

## 🧪 Testing

Run the included test suite to verify functionality against the official GeeTest demo site:

```bash
# Test all supported types
python tests/test_solver.py --all

# Test specific type with debug logging
python tests/test_solver.py icon --debug
```

## ⚠️ Disclaimer

This project is for educational and research purposes only. Automating CAPTCHAs likely violates the Terms of Service of the provider. Use responsibly.

## 🤝 Credits

Based on and customized from the [GeekedTest](https://github.com/xKiian/GeekedTest) repository.
**Enhancements by Evil-Bane:**
*   Replaced broken ONNX icon classifier with robust OpenCV-based matcher.
*   Added automatic retry logic for network/server failures.
*   Refactored code structure for professional use.
*   Improved documentation and testing tools.
