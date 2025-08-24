from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="streamline-file-uploader",
    version="1.0.0",
    author="Stream-Line AI",
    author_email="support@stream-lineai.com",
    description="Easy-to-use file uploader for Stream-Line file server with folder support and automatic organization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/streamline-ai/file-uploader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
    },
    keywords="file-upload, streamline, upload-service, file-server, python, async",
    project_urls={
        "Bug Reports": "https://github.com/streamline-ai/file-uploader/issues",
        "Source": "https://github.com/streamline-ai/file-uploader",
        "Documentation": "https://github.com/streamline-ai/file-uploader#readme",
    },
)


