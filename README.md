# ec2_inventory.py
A simple script that uses uses the Amazon Web Services Boto3 python module to
generate a CSV file of all EC2 Instances.

## Prerequisites
This script assumes that you have Python3 and [Boto3](https://boto3.readthedocs.io/en/latest/)
installed as well as the other modules listed at the top of the script.

It is also assumed that you have the AWS Command Line Interface installed and have
run the configure command to [configure the AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
for each of the AWS accounts to be inventoried.

## Instructions
Use [git clone](https://git-scm.com/docs/git-clone) to download this repository to
the system that will run the script.

Next, edit the AWS-account-list.csv to include only the AWS accounts associated
with your organization.  Use a "Y" in the "In-Audit-Scope" column to indicate whether
to include that account in the EC2 Inventory.  The fourth column, "Comments-Purpose"
is completely optional.  

## Description
This script iterates through all AWS accounts listed in the
[AWS-account-list.csv](../master/AWS-account-list.csv) and then iterates through all regions making the
[DescribeInstances](http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
API call each time.

The resulting output will look something like [ec2_inventory-2017-11-05.csv](../master/ec2_inventory-2017-11-05.csv).
