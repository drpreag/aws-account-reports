# Purpose: in all accouts, all regions search for all VPCs
# and report if VPC has no compute resources (dummy, orphan vpc)
#
# Author Predrag Vlajkovic, 2023

from __future__ import print_function
import boto3, sys, botocore
import yaml, getopt
from uuid import uuid4

global_cfg_ini_file="config.yaml"
global_config = []

def parse_config_file():
    with open(global_cfg_ini_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def get_vpc_info (session, region):
    ec2 = session.client('ec2', region_name=region)
    response = ec2.describe_vpcs(Filters=[{'Name':'isDefault','Values': ['false']},])
    return response['Vpcs']

def get_number_of_ec2s (session, region, vpc_id):
    count=0
    ec2 = session.client('ec2', region_name=region)
    response = ec2.describe_instances(Filters=[{'Name':'vpc-id','Values': [vpc_id]},])
    if response:
        if response['Reservations']:
            for instance in response['Reservations'][0]['Instances']:
                count=count+1
    return count

def get_number_of_rdss (session, region, vpc_id):
    count=0
    rds = session.client('rds', region_name=region)
    response = rds.describe_db_instances()
    if response:
        if response['DBInstances']:
            for rds in response['DBInstances']:
                if rds['DBSubnetGroup']['VpcId'] == vpc_id:
                    count=count+1
    return count

def get_number_of_lambdas (session, region, vpc_id):
    count=0
    l = session.client('lambda', region_name=region)
    response = l.list_functions()
    if response:
        if response['Functions']:
            for f in response['Functions']:
                if 'VpcConfig' in f:
                    if f['VpcConfig']['VpcId'] == vpc_id:
                        count=count+1
    return count

def get_number_of_ngws (session, region, vpc_id):
    count=0
    ngws = session.client('ec2', region_name=region)
    response = ngws.describe_nat_gateways(Filters=[{'Name':'vpc-id','Values': [vpc_id]},])
    if response:
        if response['NatGateways']:
            for f in response['NatGateways']:
                count=count+1
    return count

def get_name_tag(tags):
    vpc_name = "-"
    if len(tags) == 0:
        return vpc_name
    for tag in tags:
        if (len(tag)>0):
            if tag['Key'] == 'Name':
                return tag['Value']
    return vpc_name

def get_enabled_regions(boto3_session: boto3.Session, service: str):
    regions = boto3_session.get_available_regions(service)
    enabled_regions = set()
    for region in regions:
        sts_client = boto3_session.client('sts', region_name=region)
        try:
            sts_client.get_caller_identity()
            enabled_regions.add(region)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "InvalidClientTokenId":
                pass
            else:
                raise
    return enabled_regions

# process command line arguments and return list of key pair values
def process_cli_arguments (argv):
    parameters = ["0"]
    try:
        opts, args = getopt.getopt(argv,"t:h",["target=","--help"])
    except getopt.GetoptError:
        print ("Invalid parameters, to see parameter map use:")
        print ("   vpc-empty-report.py -h")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("h", "--help"):
            print ("Usage: vpc-empty-report.py --target <target> --help")
            print ("   or: vpc-empty-report.py -t <target> -h")
            sys.exit()
        elif opt in ("-t", "--target"):
            parameters[0]=arg
        else:
            assert False, "unhandled option"
    return parameters

def main(argv=None):
    global_config = parse_config_file()
    parameters = process_cli_arguments(argv)
    target=int(parameters[0])
    count = 1

    print ("\nV P C   R E P O R T\n")
    print (f"List of VPC-s that have EC2/RDS or Lambdas combined less or equal then {target}.")
    print ("")

    for profile in global_config['profiles']:
        session = boto3.Session(profile_name=profile)
        available_regions = get_enabled_regions (session, "ec2")
        for region in available_regions:
            vpcs = get_vpc_info (session, region)
            if vpcs:
                for vpc in vpcs:
                    ec2s = rdss = lams = 0
                    vpc_name = "-"
                    if 'Tags' in vpc:
                        vpc_name = get_name_tag (vpc['Tags'])
                    if vpc_name == "aws-controltower-VPC":
                        continue
                    ec2s = get_number_of_ec2s(session, region, vpc['VpcId'])
                    rdss = get_number_of_rdss(session, region, vpc['VpcId'])
                    lams = get_number_of_lambdas(session, region, vpc['VpcId'])
                    if ec2s+rdss+lams <= target:
                        ngws = get_number_of_ngws(session, region, vpc['VpcId'])
                        print (f"   {count:3d} - Profile: {profile:14}  Region: {region:16}  Vpc: {vpc['VpcId']:23}  CIDR: {vpc['CidrBlock']:18}  Name: {vpc_name}")
                        if ec2s+rdss+lams+ngws > 0:
                            print (f"            ec2: {ec2s:2}    rds: {rdss:2}    lambda: {lams:2}     ngws: {ngws}")
                        count+=1
    print ("\nEnd of report.")

if __name__ == '__main__':
    main(sys.argv[1:])