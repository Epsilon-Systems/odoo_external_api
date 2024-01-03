import paramiko
import boto3
import os

os.environ['AWS_ACCESS_KEY_ID'] = 'TU_ACCESS_KEY_ID'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'TU_SECRET_ACCESS_KEY'
os.environ['AWS_DEFAULT_REGION'] = 'TU_REGION'

client = boto3.client('ec2')
response = client.describe_instances(InstanceIds=['TU_INSTANCE_ID'])
ip_address = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(ip_address, username='USER', key_filename='PUBLIC_KEY.pem')
sftp = ssh.open_sftp()

local_path = '/ruta/al/local'
remote_path = '/ruta/al/remoto'

sftp.put(local_path, remote_path)

sftp.close()
ssh.close()