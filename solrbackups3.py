#!/usr/bin/python

import argparse
import glob
import os
import tarfile
import urllib2
import time
import json
import sys
import shutil
from subprocess import check_call

parser = argparse.ArgumentParser(description='Backup Solr to S3')
parser.add_argument('--host', dest='host', default='localhost')
parser.add_argument('--port', dest='port', default='8983')
parser.add_argument('--location', dest='location', default='/tmp')
parser.add_argument('--bucket', dest='bucket', default='h24-backup-solr')

args = parser.parse_args()

snapshot_directory = "%s/snapshot.%s" % (args.location, time.time())
os.mkdir(snapshot_directory)
print 'Snapshot directory created: %s' % snapshot_directory

print 'Backup start...'
check_call(["python", "src/solrbackup/solrbackup/solrbackup.py", "http://%s:%s/solr" % (args.host, args.port), snapshot_directory])

archive_name = '%s/solr.%s.tgz' % (args.location, time.strftime("%Y%m%d.%H%M%S"))
print 'Archiving to %s' % archive_name

with tarfile.open(archive_name, "w:gz") as tar:
    # tar.add(snapshot_directory)
    for dirname, dirnames, filenames in os.walk(snapshot_directory):
        for subdirname in dirnames:
            tar.add(os.path.join(dirname, subdirname), arcname=subdirname)
            print(subdirname)

print 'Uploading to AWS'
check_call(["aws", "s3", "cp", archive_name, "s3://" + args.bucket])

print 'Removing snapshot directory.'
shutil.rmtree(snapshot_directory)

print 'Removing backup archvie'
os.remove(archive_name)

print '+++ done'
