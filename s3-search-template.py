# Purpose: in all accouts search for s3 buckets
# that do not meet CIS AWS 1.4.0 compliance
#
# Author Predrag Vlajkovic, 2023

from __future__ import print_function
import boto3, sys, botocore
import yaml
from uuid import uuid4

global_cfg_ini_file="config.yaml"
global_config = []

def parse_config_file():
    with open(global_cfg_ini_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def main(argv=None):
    global_config = parse_config_file()
    count = 1

    print ("\nS 3   R E P O R T\n")
    print ("List of S3 buckets that do not meet security policies (CIS AWS 1.4.0 compliance).")
    print ("")

    for profile in global_config['profiles']:
        session = boto3.Session(profile_name=profile)
        s3 = session.client('s3')
        buckets = s3.list_buckets()['Buckets']
        for bucket in buckets:
            versioning = bpa = bp = "-"
            try:
                response = s3.get_bucket_versioning(Bucket=bucket['Name'])
                if 'Status' in response:
                    versioning = response['Status']
            except botocore.exceptions.ClientError as e:
                pass
            try:
                bpa = s3.get_public_access_block(Bucket=bucket['Name'])['PublicAccessBlockConfiguration']
            except botocore.exceptions.ClientError as e:
                pass
            try:
                bp = s3.get_bucket_policy(Bucket=bucket['Name'])['Policy']
            except botocore.exceptions.ClientError as e:
                pass

            print (f"{count:2} - Bucket: {bucket['Name']};  Versioning: {versioning}; BPS: {bpa};  Policy: {bp}")
            count+=1

    print ("\nEnd of report.")

if __name__ == '__main__':
    main(sys.argv[1:])