from setuptools import find_packages, setup

setup(
    name='nbr-detection',
    author='Andrew Ferullo',
    author_email='f3rullo14@gmail.com',
    version='0.1.0',
    description='Evaluate NBR values of a COG.',
    license='MIT',
    packages=find_packages(where='nbrdetect'),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'numpy>=1.23.4',
        'GDAL>=3.4.3',
        'rasterio>=1.2.10'
    ],
)