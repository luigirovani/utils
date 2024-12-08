from setuptools import setup, find_packages

setup(
    name="utils",
    version="1.0.1",
    description="Func Utils for python",
    long_description=open("README.rst").read(),
    long_description_content_type="text/markdown",
    author="Luigi Augusto Rovani",
    author_email="luigi3520@gmail.com",
    url="https://github.com/luigirovani/utils",
    license="MIT",
    packages=find_packages(),
    install_requires=open("requirements.txt").readlines(),
    python_requires=">=3.13"
)
