from setuptools import setup

setup(
    name='sparrowmail',
    version='0.1',
    packages=['sparrowmail'],
    scripts=['init_sparrowmail.py']

    include_package_data=True,

    install_requires=[
        'sparrowmail',
        'email_validator',
        'flask',
    ],
    )
