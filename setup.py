from distutils.core import setup

setup(
    name='django-ebaysync',
    version='0.1.10',
    packages=[
        'ebaysync',
        'ebaysync.management',
        'ebaysync.management.commands',
    ],
    license='LGPL v3',
    long_description=open('pypi.rst').read(),
    author="Anentropic",
    author_email="ego@anentropic.com",
    url="https://github.com/anentropic/django-ebaysync",
    install_requires=[
        "EbaySuds >= 0.3",
    ],
)