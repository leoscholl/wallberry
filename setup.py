from setuptools import find_packages, setup

setup(
    name='wallberry',
    version='1.2.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'python-forecastio',
        'matplotlib'
    ],
)
