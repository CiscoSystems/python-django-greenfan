from setuptools import setup, find_packages

setup(
    name='django-greenfan',
    version='0.1.0',
    description='OpenStack Continuous Integration',
    author='Soren Hansen',
    author_email='sorhanse@cisco.com',
    url='http://github.com/sorenh/python-django-greenfan',
    packages=find_packages(),
    include_package_data=True,
    license='Apache 2.0',
    keywords='django openstack ci',
    test_suite='tests.main',
    install_requires=[
        'django',
    ],
    classifiers=[
      'Development Status :: 2 - Pre-Alpha',
      'Environment :: Web Environment',
      'Framework :: Django',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Operating System :: POSIX :: Linux',
      'Programming Language :: Python',
      'Topic :: Software Development',
     ]
)
