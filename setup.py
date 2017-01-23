import sys
from setuptools import setup, find_packages
from setuptools.command.test import test

V = '0.1.4'

setup_requires = ['setuptools']
install_requires = []
tests_require = ['pytest']


# noinspection PyAttributeOutsideInit
class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = ['tests_leady']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='leady',
    version=V,
    author='Vitek Pliska',
    author_email='vitek@creatiweb.cz',
    url='https://github.com/impercz/leady-python-sdk',
    packages=find_packages(),
    include_package_data=True,
    license='LICENSE',
    description='Leady Analytics Tracking API',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    zip_safe=False,
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={'test': PyTest},
)
