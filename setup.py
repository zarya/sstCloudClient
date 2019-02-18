
from setuptools import setup

setup(
	name = 'sstCloudClient',
	version = '0.0.1',
	description = 'Python client for connecting to the SST Cloud webservice',
        url = 'https://github.com/zarya/sstCloudClient',
	author = 'Rudy H (Zarya)',
	author_email = 'sstcloudclient@gigafreak.net',
	license = 'MIT',
	classifiers = [
                'Programming Language :: Python :: 3',
                "License :: OSI Approved :: MIT License",
		'Development Status :: 3 - Alpha',
	],
	keywords = ['sst-cloud','sstcloud'],
	packages = ['sstCloud'],
	install_requires = ['requests']
)
