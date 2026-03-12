from setuptools import setup, find_packages

setup(
    name="knowledge-memory",
    version="0.1.0",
    description="Direct Python library interface for knowledge memory operations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["knowledge_memory", "knowledge_memory.*"]),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.5.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
