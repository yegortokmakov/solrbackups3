from setuptools import setup, find_packages

setup(
    name='solrbackups3',
    version='0.4',
    url='https://github.com/yegortokmakov/solrbackups3',
    license='MIT',
    author='yegortokmakov',
    author_email='yegor@tokmakov.biz',
    install_requires=['solrbackup'],
    description='S3 backup solution for Solr',
    scripts=['solrbackups3'],
    packages=find_packages()
)
