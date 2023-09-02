from setuptools import setup, find_packages

setup(
    name='snugbug',
    version='0.4',
    author= 'istakshaydilip',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'snugbug=snugbug.main:main',
        ],
    },
)
