from setuptools import setup, find_packages

setup(
    name='solango',
    version='0.0.2',
    description='Django module for integrating Solr search',
    author='Sean Creeley,',
    author_email='sean@screeley.com',
    url='http://code.google.com/p/django-solr-search/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
)