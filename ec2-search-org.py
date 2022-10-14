# Purpose: search for ec2 instances organization wide (multiple accounts)
# by name, aws account, region, status or a tag value.
# Search criterias can be combined.
#
# Organization must be set, otherwise error will be raised.
#
# Author Predrag Vlajkovic, 2019

from __future__ import print_function
import boto3, sys, getopt, configparser
from uuid import uuid4

configLocation = "./config.txt"
mainAccount = ""
mainAccountId = ""
mainAccountProfile = ""

def parseConfig ():
    global mainAccountId, mainAccountProfile
    config = configparser.RawConfigParser()
    config.read(configLocation)
    mainAccountId = config.get('aws', 'main_account_id')
    mainAccountProfile = config.get('aws', 'main_account_profile')

def get_aws_accounts(account_name):
    active_accounts = []

    client = boto3.client('account')
    print (client)
    # organizations_client = boto3.client('organizations')

    # if (not organizations_client.list_accounts()["Accounts"]):
    #     return active_accounts

    # for account in  organizations_client.list_accounts()["Accounts"]:
    #     if (account['Status'] == 'ACTIVE'):
    #         if (account_name == "*"):
    #             active_accounts.append(account)
    #         else:
    #             if (account_name in account["Name"].lower()):
    #                 active_accounts.append(account)
    return active_accounts

def get_aws_session(account_id):
    if (account_id == mainAccount):
        return boto3.Session()
    else:
        role_to_assume_arn = ('arn:aws:iam::{}:role/OrganizationAccountAccessRole'.format(account_id))
        sts_default_provider_chain = boto3.client('sts')
        response = sts_default_provider_chain.assume_role(
            RoleArn=role_to_assume_arn,
            RoleSessionName=str(uuid4())
        )
        creds = response['Credentials']
        return boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken']
                )

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
    parameters = ["*", "*", "*", "*", "*"]
    try:
        opts, args = getopt.getopt(argv,"a:r:n:s:t:h",["account=","region=","name=","status=","tag=","--help"])
    except getopt.GetoptError:
        print ("Invalid parameters, to see parameter map use:")
        print ("   ec2_search.py -h")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ("Usage: ec2_search.py --name <ec2_name> --account <account> --region <region> --status <status> --tag <tag value> --help")
            print ("   or: ec2_search.py -n <ec2_name> -a <account> -r <region> -s <status> -t <tag value> -h")
            print ("   Assumed * for ec2_name, account, region and status if not specified")
            print ("   Note: for sandbox account use like this: --account dave")
            sys.exit()
        elif opt in ("-n", "--name"):
            parameters[0]=arg
        elif opt in ("-a", "--account"):
            parameters[1]=arg
        elif opt in ("-r", "--region"):
            parameters[2]=arg
        elif opt in ("-s", "--status"):
            parameters[3]=arg
        elif opt in ("-t", "--tag"):
            parameters[4]=arg
        else:
            assert False, "unhandled option"

    return parameters

def main(argv=None):
    parameters = process_cli_arguments(argv)
    ec2_name=parameters[0]
    account_name=parameters[1]
    region_name=parameters[2]
    status=parameters[3]
    tag_value=parameters[4]

    parseConfig ()

    count = 0
    print (f"Searching for ec2 instances named like {ec2_name}, in account {account_name}, in region {region_name}, with tag value {tag_value}, with status {status}")
    for account in get_aws_accounts(account_name):
        session = get_aws_session(account["Id"])
        print(f"Account: '{account['Name']}' Id: {account['Id']}")

        for region in session.client('ec2').describe_regions()['Regions']:
            if (region_name=="*" or region_name==region["RegionName"]):
                instances = get_instances(session, ec2_name, region, status)
                if (instances):
                    print(f"  Region: {region['RegionName']}")
                for instance in instances:
                    if (is_tag_value_matching (instance, tag_value)):
                        count += 1
                        if (len(get_ec2_tag(instance,'SaltEnv'))<2):
                            print (f"    Instance: #{count:3d};  name: {get_ec2_tag(instance,'Name')};  id: {instance['InstanceId']};  status: {instance['State']['Name']}")
                        else:
                            print (f"    Instance: #{count:3d};  name: {get_ec2_tag(instance,'Name')};  id: {instance['InstanceId']};  status: {instance['State']['Name']};  saltenv: {get_ec2_tag(instance,'SaltEnv')}")

    if (count > 0):
        print (f"Total {count} instances found")
    else:
        print ("Sorry, no instances found, maybe filter is not good")
    print (" ")

if __name__ == '__main__':
    main(sys.argv[1:])
