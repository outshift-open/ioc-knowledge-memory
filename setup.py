# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages
import os

# Read README from knowledge_memory directory
readme_path = os.path.join(os.path.dirname(__file__), "src", "knowledge_memory", "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    long_description = f.read()

# Find all packages and namespace server under knowledge_memory
def get_packages():
    """Find packages and map server.* to knowledge_memory.server.*"""
    packages = []

    # Add knowledge_memory package
    km_packages = find_packages(where="src/knowledge_memory", exclude=["*.tests", "*.tests.*", "tests.*", "tests"])
    packages.append("knowledge_memory")
    for pkg in km_packages:
        packages.append(f"knowledge_memory.{pkg}")

    # Add server packages under knowledge_memory.server namespace
    server_packages = find_packages(where="src/server", exclude=["*.tests", "*.tests.*", "tests.*", "tests"])
    packages.append("knowledge_memory.server")
    for pkg in server_packages:
        packages.append(f"knowledge_memory.server.{pkg}")

    # Add app_logging if needed
    app_logging_packages = find_packages(where="src/app_logging", exclude=["*.tests", "*.tests.*", "tests.*", "tests"])
    if app_logging_packages or os.path.exists("src/app_logging/__init__.py"):
        packages.append("knowledge_memory.app_logging")
        for pkg in app_logging_packages:
            packages.append(f"knowledge_memory.app_logging.{pkg}")

    return packages

# Create package_dir mapping
package_dir = {
    "knowledge_memory": "src/knowledge_memory",
    "knowledge_memory.server": "src/server",
    "knowledge_memory.app_logging": "src/app_logging",
}

setup(
    name="knowledge-memory",
    description="Direct Python library interface for knowledge memory operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Organization",
    package_dir=package_dir,
    packages=get_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.5.0",
        "agensgraph-python>=1.0.2",
        "psycopg2-binary>=2.9.11",
        "sqlalchemy>=2.0.23",
        "pgvector>=0.4.2",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.1",
        "requests>=2.31.0",
        "prometheus-fastapi-instrumentator>=6.1.0",
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
