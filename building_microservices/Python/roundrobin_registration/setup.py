from setuptools import setup, find_packages

distribution_name = 'roundrobin'
setup(
    name=distribution_name,
    version='1.0.0',
    license='Apache Software License 2.0',
    description='Demonstrating Roundrobin registration with the MDStudio broker',
    author='Marc van Dijk - VU University - Amsterdam,' \
           'Paul Visscher - Zefiros Software (www.zefiros.eu),' \
           'Felipe Zapata - eScience Center (https://www.esciencecenter.nl/)',
    author_email='m4.van.dijk@vu.nl, f.zapata@esciencecenter.nl, contact@zefiros.eu',
    url='https://github.com/MD-Studio/MDStudio_examples',
    keywords='MDStudio microservice roundrobin registration',
    platforms=['Any'],
    packages=find_packages(),
    py_modules=[distribution_name],
    install_requires=[],
    test_suite="tests",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: System',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
    ],
)
