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
    count = 0
    total = 0

    print ("\nS 3   R E P O R T\n")
    print ("List of S3 buckets that do not meet security policies (CIS AWS 1.4.0 compliance).")
    print (" - Bucket public access is not blocked -")
    print ("")

    for profile in global_config['profiles']:
        print (f"Profile: {profile}")
        session = boto3.Session(profile_name=profile)
        s3 = session.client('s3')
        buckets = s3.list_buckets()['Buckets']
        for bucket in buckets:
            try:
                bucket_policy = s3.get_bucket_policy (Bucket=bucket['Name'])
                policy = bucket_policy['Policy']
                if not "aws:SecureTransport" in policy:
                    count+=1
                # else:
                #     print (f"  {count+1:4} - Bucket: {bucket['Name']} policy contains aws:SecureTransport;")
            except botocore.exceptions.ClientError as e:
                print (f"  {count+1:4} - Bucket: {bucket['Name']};  missing block http policy;")
                count+=1
                pass
            total+=1

    print (f"\nFound total {total} buckets, and {count} buckets have security issue.")
    print ("\nEnd of report.")

if __name__ == '__main__':
    main(sys.argv[1:])