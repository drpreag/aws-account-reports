# Purpose: in single aws profile search for ec2 instances
# by name, aws account/profile, region, status or a tag value.
# Search criterias can be combined.
#
# Author Predrag Vlajkovic, 2019

from __future__ import print_function
import boto3, sys, getopt
from uuid import uuid4

def get_session(profile):
    return boto3.session.Session(profile_name=profile)

def get_ec2_tag(instance, tag_name, default="-"):
    tag_value = default
    if "Tags" in instance:
        for tag in instance["Tags"]:
            if tag["Key"].lower() == tag_name.lower():
                tag_value = tag["Value"]

    return tag_value

def is_tag_value_matching (instance, tag_value):
    if (tag_value == "*"):
        return True
    if "Tags" in instance:
        for tag in instance["Tags"]:
            if (tag_value.lower() in tag["Value"].lower()):
                return True
    return False


def get_instances(session, ec2_name, region, status):
    instances = []
    filter_list = []
    if (status != "*"):
        filter_list.append ({'Name':'instance-state-name', 'Values':["*"+status+"*"]})
    if (ec2_name != "*"):
        filter_list.append ({'Name':'tag:Name', 'Values':["*"+ec2_name+"*"]})

    ec2_client = session.client('ec2', region_name=region["RegionName"])
    response=ec2_client.describe_instances(Filters=filter_list)
    for ec2 in response['Reservations']:
        for instance in ec2['Instances']:
            if (instance):
                instances.append (instance)
    return instances

# process command line arguments and return list of key pair values
def process_cli_arguments (argv):
    parameters = ["*", "*", "*", "*", "default"]
    try:
        opts, args = getopt.getopt(argv,"a:r:n:s:t:p:h",["region=","name=","status=","tag=","profile=","--help"])
    except getopt.GetoptError:
        print ("Invalid parameters, to see parameter map use:")
        print ("   ec2-search.py -h")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ("Usage: ec2-search.py --name <ec2_name> --region <region> --status <status> --tag <tag value> --profile <profile_name> --help")
            print ("   or: ec2-search.py -n <ec2_name> -r <region> -s <status> -t <tag value> -p <profile_name> -h")
            print ("   Assumed * for ec2_name, region and status, and default for profile_name if not specified")
            sys.exit()
        elif opt in ("-n", "--name"):
            parameters[0]=arg
        elif opt in ("-r", "--region"):
            parameters[1]=arg
        elif opt in ("-s", "--status"):
            parameters[2]=arg
        elif opt in ("-t", "--tag"):
            parameters[3]=arg
        elif opt in ("-p", "--profile"):
            parameters[4]=arg
        else:
            assert False, "unhandled option"

    return parameters

def main(argv=None):
    parameters = process_cli_arguments(argv)
    ec2_name=parameters[0]
    region_name=parameters[1]
    status=parameters[2]
    tag_value=parameters[3]
    profile_name=parameters[4]

    count = 0
    print (f"Searching for ec2 instances named like {ec2_name}, in aws account/profile {profile_name}, in region {region_name}, with tag value {tag_value}, with status {status}!")
    session = get_session(profile_name)
    for region in session.client('ec2').describe_regions()['Regions']:
        if (region_name=="*" or region_name==region["RegionName"]):
            instances = get_instances(session, ec2_name, region, status)
            if (instances):
                print(f"  Region: {region['RegionName']}")
            for instance in instances:
                if (is_tag_value_matching (instance, tag_value)):
                    count += 1
                    print (f"    Instance: #{count:3d};  name: {get_ec2_tag(instance,'Name')};  id: {instance['InstanceId']};  status: {instance['State']['Name']}")
    if (count > 0):
        print (f"Total {count} instances found")
    else:
        print ("Sorry, no instances found, maybe filter is not good")
    print (" ")

if __name__ == '__main__':
    main(sys.argv[1:])