#!/usr/bin/env python3


from __future__ import absolute_import
from __future__ import print_function
import re
from datetime import datetime
import csv
import argparse
import time
import os

today = datetime.now()

try:
    import boto3
    # import botocore
except ImportError as e:
    print('This script require Boto3 to be installed and configured.')
    exit()
from botocore.exceptions import ClientError

def get_account_list():
    # generate a list of AWS accounts based on the credentials file
    local_account_list = []
    try:
        credentials = open(os.path.expanduser('~/.aws/credentials'), 'r')
        for line in credentials:
            account = re.search('\[([\w\d\-\_]*)\]', line)
            if account is not None:
                local_account_list.insert(0, account.group(1))
    except:
        print("Script expects ~/.aws/credentials. Make sure this file exists")
        exit()
    return local_account_list

def get_aws_accounts_in_scope():
    # read the csv file of AWS accounts into dictionary
    accounts_local = {}
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    f = (os.path.join(__location__, 'AWS-account-list.csv'))
    with open(f, 'r') as file:
        for line in file:
            data = line.split(",")
            key = data[0]
            val = data[1]
            flag = data[2]
            if flag.upper()=="Y":
                accounts_local[key] = val
    return accounts_local

def validate_credentials(accounts_dictionary, accounts_credentials, *profile):
    # validate that the local credentials file has an entry for each account in scope and use only
    # the credentials for the accounts in scope.
    in_scope_acct_alias_list = []
    for acct in accounts_credentials:
        if (acct in accounts_dictionary.values()):
            in_scope_acct_alias_list.append(acct)
        else:
            print("****INFORMATION: %s was not found in list of accounts in scope." % acct)
    for key, value in accounts_dictionary.items():
        if value not in in_scope_acct_alias_list:
            print("****WARNING: %s does not have a corresponding entry in the local credentials file." % value)
            print("****WARNING: The %s account will not be audited" % value)
    return in_scope_acct_alias_list

def get_client(account, local_region):
    # Sets up a boto3 session
    local_profile = account
    try:
        current_session = boto3.Session(profile_name = local_profile, region_name=local_region)
        local_client = current_session.client("ec2")
        return local_client
    except:
        print(local_region)
        print('\'{}\' is not a configured account.'.format(account))
        exit()

def date_on_filename(filename, file_extension):
    from datetime import datetime
    date = str(datetime.now().date())
    return filename + "-" + date + "." + file_extension

def get_regions(lcl_account):
    #get the current list of regions to iterate through
    lcl_region = "us-east-1"
    client = get_client(lcl_account, lcl_region)
    aws_region_data = client.describe_regions()
    aws_regions = aws_region_data['Regions']
    lcl_regions = [region['RegionName'] for region in aws_regions]
    return lcl_regions

def main():
    report_filename = date_on_filename("ec2_inventory", "csv")
    # Get the List of AWS Accounts in Scope
    accounts = get_aws_accounts_in_scope()
    # Get the List of Accounts in the user's local credential file
    account_list = get_account_list()
    # Ensure the user's local credential is complete, remove out of scope accounts
    validated_accounts = validate_credentials(accounts, account_list)
    file = open(report_filename, 'w+')
    print_string_hdr = "account,owner_id,region,reservation_id,instance_id,state,image_id,platform,instance_type,vpc_id," \
    + "launch_time,age,network_interfaces,subnet_id,private_ip,private_dns_name,public_dns_name,name,keep_until,managed_by,tag_qty\n"
    file.write(print_string_hdr)
    regions = get_regions(validated_accounts[0])
    for account in validated_accounts:
        print("*********************************************************")
        count_total = count_old = oldest = 0
        for region in regions:
            client = get_client(account, region)
            #aws_regions = client.describe_regions()
            #print('Regions:', aws_regions['Regions'])
            response = client.describe_instances()
            print(account, " -- ", region)
            owner_id = reservation_id = instance_id = state = image_id = instance_type = network_interfaces = ""
            vpc_id = launch_time = private_ip = private_dns_name = platform = public_dns_name = subnet_id = ""
            name = keep_until = managed_by = tag_qty = age = ""
            for key1, value1 in response.items():
                if key1 == "Reservations":
                    for object_a in value1:
                        for key2, value2 in object_a.items():
                            if key2 == "OwnerId":
                                owner_id = value2
                            if key2 == "ReservationId":
                                reservation_id = value2
                            if key2 == "Instances":
                                instances = value2
                                for object_b in instances:
                                    for key3, value3 in object_b.items():
                                        if key3 == "State":
                                            state = value3['Name']
                                        if key3 == "NetworkInterfaces":
                                            network_interfaces = str(len(value3))
                                        if key3 == "ImageId":
                                            image_id = value3
                                        if key3 == "InstanceType":
                                            instance_type = value3
                                        if key3 == "VpcId":
                                            vpc_id = value3
                                        if key3 == "InstanceId":
                                            instance_id = value3
                                        if key3 == "LaunchTime":
                                            launch_time = str(value3)
                                            launch_time_date = datetime.strptime(launch_time, "%Y-%m-%d %H:%M:%S+00:00")
                                            delta = today - launch_time_date
                                            print(delta)
                                            agestring = str(delta).split(" ")
                                            age = str(agestring[0])
                                            if len(agestring) != 3:  #fix for ages less than 24 hours
                                                age = str(0)
                                            count_total += 1
                                            if int(age) > 30:
                                                count_old += 1
                                            if int(age) > oldest:
                                                oldest = int(age)
                                        if key3 == "SubnetId":
                                            subnet_id = value3
                                        if key3 == "PrivateIpAddress":
                                            private_ip = value3
                                        if key3 == "PrivateDnsName":
                                            private_dns_name = value3
                                        if key3 == "PublicDnsName":
                                            public_dns_name = value3
                                        if key3 == "Platform":
                                            platform = value3
                                        if key3 == "Tags":
                                            name = keep_until = managed_by = tag_qty = ""
                                            for dictionary in value3:
                                                key4 = dictionary['Key']
                                                value4 = dictionary['Value']
                                                if key4 == 'Name':
                                                    name = '"' + value4 + '"'
                                                if key4 == 'KeepUntil':
                                                    keep_until = '"' + value4 + '"'
                                                if key4 == 'ManagedBy':
                                                    managed_by = '"' + value4 + '"'
                                            tag_qty = str(len(value3))

                        print_string = account + ",'" + owner_id + "'," + region + "'," + reservation_id + "," + instance_id + "," + \
                            state + "," + image_id + "," + platform + "," + instance_type + "," + vpc_id + "," + launch_time + "," + \
                            age + "," + network_interfaces + "," + subnet_id + "," + private_ip + "," + private_dns_name + "," + \
                            public_dns_name + "," + name + "," + keep_until + "," + managed_by + "," + tag_qty
                        print(print_string)
                        file.write(print_string + "\n")
    file.close()
    return
main()
