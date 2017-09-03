from setuptools import setup

setup(
    name='sparrowmail',
    packages=['sparrowmail'],
    include_package_data=True,
    install_requires=[
        'sparrowmail',
        'email_validator',
        'flask',
    ],
    )
