#!/usr/bin/python

import argparse
import os
import tarfile
import time
import shutil
import subprocess
import sys


def backup(args):
    snapshot_directory = "%s/snapshot.%s" % (args.location, time.time())
    os.mkdir(snapshot_directory)
    print 'Snapshot directory created: %s' % snapshot_directory

    print 'Backup start...'
    subprocess.check_call(["python", "src/solrbackup-master/solrbackup/solrbackup.py", "http://%s:%s/solr" % (args.host, args.port), snapshot_directory])

    archive_name = '%s/solr.%s.tgz' % (args.location, time.strftime("%Y%m%d.%H%M%S"))
    print 'Archiving to %s' % archive_name

    with tarfile.open(archive_name, "w:gz") as tar:
        for dirname, dirnames, filenames in os.walk(snapshot_directory):
            for subdirname in dirnames:
                tar.add(os.path.join(dirname, subdirname), arcname=subdirname)
                print(subdirname)

    print 'Uploading to AWS'
    subprocess.check_call(["aws", "s3", "cp", archive_name, "s3://" + args.bucket])

    print 'Removing snapshot directory.'
    shutil.rmtree(snapshot_directory)

    print 'Removing backup archvie'
    os.remove(archive_name)

    print '+++ done'


def restore(args):
    print 'Downloading backup'
    subprocess.check_call(["aws", "s3", "cp", "s3://%s/%s" % (args.bucket, args.filename), args.location])

    snapshot_directory = "%s/snapshot.%s" % (args.location, time.time())
    os.mkdir(snapshot_directory)

    print 'Extracting files to: %s' % snapshot_directory
    tar = tarfile.open("%s/%s" % (args.location, args.filename))
    tar.extractall(path=snapshot_directory)
    tar.close()

    print 'Stopping Solr'
    subprocess.check_call(["sudo", "service", "solr", "stop"])

    process = os.popen("sudo service solr status | grep uptime").read()
    if process:
        print 'Solr running! terminate...'
        sys.exit()

    for dirname, dirnames, filenames in os.walk(snapshot_directory):
        for subdirname in dirnames:
            print 'Restoring core: %s' % subdirname

            print '--- Removing transaction log'
            for root, dirs, files in os.walk("%s/%s/data/tlog" % (args.solrpath, subdirname)):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))

            print '--- Removing index data'
            for root, dirs, files in os.walk("%s/%s/data/index" % (args.solrpath, subdirname)):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))

            print '--- Restoring index data'
            for root, dirs, files in os.walk(snapshot_directory):
                for f in files:
                    shutil.copy(os.path.join(root, f), "%s/%s/data/index/" % (args.solrpath, subdirname))

    print 'Starting Solr'
    subprocess.check_call(["sudo", "service", "solr", "start"])

    print 'Removing snapshot directory.'
    shutil.rmtree(snapshot_directory)

    print 'Removing backup archvie'
    os.remove("%s/%s" % (args.location, args.filename))

    print '+++ done'

def list(args):
    print 'List of available backups'
    subprocess.check_call(["aws", "s3", "ls", "s3://" + args.bucket])

def main():
    parser = argparse.ArgumentParser(description='Backup Solr to S3', add_help=False)

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_backup = subparsers.add_parser('backup', help='a help')
    parser_backup.add_argument('bucket', help='S3 bucket')
    parser_backup.add_argument('--host', dest='host', default='localhost')
    parser_backup.add_argument('--port', dest='port', default='8983')
    parser_backup.add_argument('--location', dest='location', default='/tmp')
    parser_backup.set_defaults(func=backup)

    parser_restore = subparsers.add_parser('restore', help='a help')
    parser_restore.add_argument('bucket', help='S3 bucket')
    parser_restore.add_argument('filename', help='Remote filename to restore')
    parser_restore.add_argument('--location', dest='location', default='/tmp')
    parser_restore.add_argument('--solrpath', dest='solrpath', default='/var/solr/data')
    parser_restore.set_defaults(func=restore)

    parser_list = subparsers.add_parser('list', help='List available backups')
    parser_list.add_argument('bucket', help='S3 bucket')
    parser_list.set_defaults(func=list)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__': main()
