from setuptools import setup, find_packages

setup(
    name='snugbug',
    version='1.4',
    author= 'istakshaydilip',
    description= 'A CLI based app for Coders and students alike.',
    long_description=open('README.md').read(),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'snugbug=snugbug.main:main',
        ],
    },
)
