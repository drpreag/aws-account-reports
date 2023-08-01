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
        session = boto3.Session(profile_name=profile)
        s3 = session.client('s3')
        buckets = s3.list_buckets()['Buckets']
        for bucket in buckets:
            bpab = "-"
            total+=1
            try:
                bpab = s3.get_public_access_block(Bucket=bucket['Name'])
                pabc = bpab['PublicAccessBlockConfiguration']
                if not (pabc['BlockPublicAcls'] and pabc['IgnorePublicAcls'] and pabc['BlockPublicPolicy'] and pabc['RestrictPublicBuckets']):
                    pass
            except botocore.exceptions.ClientError as e:
                try:
                    bucket_policy = s3.get_bucket_policy (Bucket=bucket['Name'])
                    pass
                except botocore.exceptions.ClientError as e:
                    print (f"  {count+1:4} - Profile: {profile:14}  Bucket: {bucket['Name']}    Finding: Missing PAB block and missing bucket policy")
                    count+=1
                    # this bucket can be updated with PAB set to true
                    # if "cf-templates-" in bucket['Name']:
                    #     print (f"         - Updating bucket: {bucket['Name']}")
                    #     response = s3.put_public_access_block(
                    #         Bucket=bucket['Name'],
                    #         PublicAccessBlockConfiguration={
                    #             'BlockPublicAcls': True,
                    #             'IgnorePublicAcls': True,
                    #             'BlockPublicPolicy': True,
                    #             'RestrictPublicBuckets': True
                    #         },
                    #     )


    print (f"\nFound total {total} buckets, and {count} buckets have security issue.")
    print ("\nEnd of report.")

if __name__ == '__main__':
    main(sys.argv[1:])