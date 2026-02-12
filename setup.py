from setuptools import setup, find_packages

setup(
    name="geetest_solver",
    version="0.1.0",
    description="A robust GeeTest v4 captcha solver with hybrid icon matching and retry logic.",
    author="Evil-Bane",
    packages=find_packages(),
    install_requires=[
        "requests",
        "curl_cffi",
        "numpy",
        "opencv-python-headless",
        "pycryptodome",
        "ddddocr>=1.4.11"
    ],
    include_package_data=True,
    package_data={
        "geetest_solver": ["models/*.onnx", "models/*.json"],
    },
    python_requires=">=3.8",
)
