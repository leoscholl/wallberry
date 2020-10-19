from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='wallberry-uberpotato',
    version='1.3.1',
    author="Leo Scholl",
    author_email="leo.scholl@gmail.com",
    description="Wall clock / weather forecast http server suitable for raspberry pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leoscholl/wallberry",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'python-forecastio',
        'matplotlib'
    ],
)
