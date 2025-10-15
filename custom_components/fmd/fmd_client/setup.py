from setuptools import setup, find_packages

setup(
    name="fmd-api-client",
    version="0.1.0",
    author="Devin Slick",
    author_email="fmd_client_github@devinslick.com",
    description="A python client for the FMD server API.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/devinslick/fmd-client",
    py_modules=["fmd_api"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "requests",
        "argon2-cffi",
        "cryptography",
    ],
)
