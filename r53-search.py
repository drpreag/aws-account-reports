# Purpose: in single aws profile search for r53 zones and records zones
#
# Author Predrag Vlajkovic, 2023

from __future__ import print_function
import boto3, sys, getopt, yaml
from uuid import uuid4

global_cfg_ini_file="config.yaml"
global_config = []

def parse_config_file():
    with open(global_cfg_ini_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def get_zones(session, zone_name):
    zones = []
    # filter_list = []
    # if (zone_name != "*"):
    #     filter_list.append ({'Name':'tag:Name', 'Values':["*"+zone_name+"*"]})

    r53_client = session.client('route53')
    response=r53_client.list_hosted_zones () # (Filters=filter_list)
    for zone in response['HostedZones']:
        # print (zone["Name"])
        if zone_name+"." == zone["Name"]:
            zones.append (zone)
    return zones

# process command line arguments and return list of key pair values
def process_cli_arguments (argv):
    parameters = ["*", "*", "*"]
    try:
        opts, args = getopt.getopt(argv,"a:r:n:p:h",["region=","name=","profile=","--help"])
    except getopt.GetoptError:
        print ("Invalid parameters, to see parameter map use:")
        print ("   ec2-search.py -h")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ("Usage: ec2-search.py --name <zone_name> --region <region> --profile <profile_name> --help")
            print ("   or: ec2-search.py -n <zone_name> -r <region> -p <profile_name> -h")
            print ("   Assumed * for zone_name and region, default for profile_name if not specified")
            sys.exit()
        elif opt in ("-n", "--name"):
            parameters[0]=arg
        elif opt in ("-r", "--region"):
            parameters[1]=arg
        elif opt in ("-p", "--profile"):
            parameters[2]=arg
        else:
            assert False, "unhandled option"

    return parameters

def main(argv=None):
    global_config = parse_config_file()
    parameters = process_cli_arguments(argv)
    zone_name=parameters[0]
    region_name=parameters[1]
    profile_name=parameters[2]

    count = 0
    print (f"Searching for r53 zones named like {zone_name}, in aws account/profile {profile_name}, in region {region_name}!")
    for profile in global_config['profiles']:
        session = boto3.Session(profile_name=profile)
        # for region in session.client('ec2').describe_regions()['Regions']:
            # if (region_name=="*" or region_name==region["RegionName"]):
        zones = get_zones(session, zone_name)
        if zones:
            print ("Profile: ", profile)
            for zone in zones:
                count += 1
                print ("   ", zone["Name"], zone)
                # print (f" #{count:3d};  name: {get_ec2_tag(instance,'Name')};  profile: {profile};  region: {region['RegionName']};  id: {instance['InstanceId']};")
    if (count > 0):
        print (f"Total {count} zones found")
    else:
        print ("Sorry, no zones found, maybe filter is not good")
    print (" ")

if __name__ == '__main__':
    main(sys.argv[1:])
