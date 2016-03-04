from setuptools import setup, find_packages

setup(
    name='flask_example_app',
    packages=find_packages(),
    version='1.0',
    description='Flask Example app',
    author='Adam Feuer', author_email='adam@adamfeuer.com',
    url='http://adamfeuer.com/',
    install_requires=['flask', 'requests']
)

