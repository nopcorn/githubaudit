from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="githubaudit",
    version="0.1.2",
    author="nopcorn",
    author_email="",
    description="Uses a Github PAT to assess the security configuration of repositories and provides a report",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nopcorn/githubaudit",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests==2.32.3",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "githubaudit=githubaudit.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security"
    ],
    python_requires=">=3.7",
)