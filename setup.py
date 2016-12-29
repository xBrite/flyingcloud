from __future__ import absolute_import

from setuptools import setup, find_packages

setup(
    name='flyingcloud',
    version='0.3.16',
    description='Build Docker images using SaltStack',
    author='MetaBrite, Inc.',
    author_email='flyingcloud-admin@metabrite.com',
    license='Apache Software License 2.0',
    url='https://github.com/cookbrite/flyingcloud',
    packages=find_packages(exclude='tests'),
    install_requires=[
        'docker-py',
        'psutil',
        'pyyaml',
        'requests!=2.12.2',
        'sh>=1.12.2',
        'six',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
    ],
    long_description=open('README.rst').read(),
    keywords="docker saltstack devops automation",
    scripts=[
        'flyingcloud/flyingcloud',
    ],
    entry_points={
        'console_scripts': [
            'fc_pkg_build = flyingcloud.utils.package_build:build_package',
        ]
    },
)
