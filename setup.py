from setuptools import setup

DESCRIPTION = "A simple Route53 API for Python 2.7/3.x, powered by requests."

LONG_DESCRIPTION = open('README.rst').read()

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='route53',
    version='1.0.1',
    packages=[
        'route53',
        'route53.xml_parsers',
        'route53.xml_generators',
    ],
    author='Gregory Taylor',
    author_email='gtaylor@gc-taylor.com',
    url='https://github.com/gtaylor/python-route53',
    license='BSD',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    install_requires=['requests', 'lxml', 'pytz'],
)
