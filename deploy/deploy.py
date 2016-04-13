import yaml
import json
import os
import subprocess
import sys

class Executor(object):

    def exec_output(self, args):
        """Execute the arguments in args, return stdout as a string"""
        return subprocess.check_output(args)
        
    def call(self, args):
        """Execute the arguments in args, return an integer return code"""
        FNULL = open(os.devnull, 'w')
        return subprocess.call(args, stdout=FNULL, stderr=subprocess.STDOUT)
        
class Configuration(object):

    def __init__(self, config_file):
        """Parse the configuration file and put it in conf"""
        self.conf = Configuration.parse_file(config_file)

    @staticmethod
    def parse_file(config_file):
        """Read the configuration file as a string, call parse_str to return a configuration dictionary"""
        with open(config_file) as f: conf = Configuration.parse_str(f)
        return conf
        
    @staticmethod
    def parse_str(str):
        """Read the configuration file as a YAML string, return a configuration dictionary. Validate along the way"""
        c = yaml.load(str)
        if c == None:
            raise ValueError("Configuration is empty")
        
        if not 'snowplow' in c:
            raise ValueError("Configuration is missing 'snowplow' fields")
        if c['snowplow'] == None or not 'collector' in c['snowplow']:
            raise ValueError("Configuration is missing 'collector' field under 'snowplow'")
        if c['snowplow']['collector'] == None:
            raise ValueError("Configuration does not have a valid collector url set")
        if 'app_id' not in c['snowplow'] or c['snowplow']['app_id'] == None:
            raise ValueError("Configuration does not have a valid app id set")
        
        if not 's3' in c:
            raise ValueError("Configuration is missing 's3' fields")
        if c['s3'] == None or not 'buckets' in c['s3']:
            raise ValueError("Configuration is missing 'buckets' field under 's3'")
        
        if c['s3']['buckets'] == None:
            raise ValueError("No buckets specified in config!") 
        
        buckets = c['s3']['buckets']
                
        c['s3']['buckets'] = [x for x in buckets if x is not None]   
        
        if len(c['s3']['buckets']) == 0:
            raise ValueError("No buckets specified in config!")
            
        return c
                      
class Shell(object):  

    @staticmethod  
    def contains_aws_cli(executor=Executor()): 
        """Check that AWS-CLI is on the path using which, return True if it is (false if not)"""
        try: 
            executor.call(['which', 'aws-cli'])
            return True
        except subprocess.CalledProcessError:
            return False

class S3(object):
    
    def __init__(self, executor=Executor()):
        """Load the available buckets using into available_buckets using AWS-CLI"""
        self.available_buckets = S3.get_buckets_from_list(S3.get_bucket_list(executor))
    
    @staticmethod
    def get_buckets_from_list(json_str):
        """Parses a json list of available buckets without any prefix (no s3://) into a list of buckets"""
        buckets=json.loads(json_str)
        return buckets         

    @staticmethod
    def get_bucket_list(executor=Executor()):
        """Uses aws s3api to get a list of available buckets as JSON"""
        avail_buckets = executor.exec_output(['aws', 's3api', 'list-buckets', '--query', 'Buckets[].Name']) 
        return avail_buckets
        
    @staticmethod
    def add_bucket_notifications(lambda_function_name, lambda_arn, s3_bucket_names, source_account_number, executor=Executor()):
        """Add a notification to each bucket in s3_bucket_names such that the lambda_arn will be invoked for S3 get and S3 put events
        Uses AWS s3api to perform this action
        """
        if len(s3_bucket_names) == 0:
            raise ValueError("cannot add bucket notifications: 0 buckets requested")

        notification_config="{\"CloudFunctionConfiguration\":{\"CloudFunction\":\"" + lambda_arn + "\",\"Events\":[\"s3:ObjectCreated:*\",\"s3:ObjectRemoved:*\"]}}"
        
        for idx,bucket in enumerate(s3_bucket_names):
            executor.call(['aws', 'lambda', 'add-permission', '--function-name', lambda_function_name, '--action', 'lambda:InvokeFunction', 
                            '--principal', 's3.amazonaws.com', '--source-arn', 'arn:aws:s3:::' + bucket, '--source-account', source_account_number, '--statement-id', 'Id-' + str(idx+1) ]) 
            executor.call(['aws', 's3api', 'put-bucket-notification', '--bucket', bucket, '--notification', notification_config])
    
class AWS(object): 

    @staticmethod
    def get_account_id(executor=Executor()):
        """Get the users current AWS account ID 
        This is collected using the AWS-CLI - by describing the default ec2 security group
        """
        account_id = executor.exec_output(['aws','ec2', 'describe-security-groups', '--group-names', 'Default', '--query', 'SecurityGroups[0].OwnerId', '--output', 'text'])
        return account_id.rstrip()
        
class IAM(object):

    @staticmethod
    def create_lambda_policy(filename, executor=Executor()):
        """Creates an IAM policy using the specified policy file in filename"""
        policy_res = executor.exec_output(['aws', 'iam', 'create-policy', '--policy-name', 'snowplow-s3-source', '--policy-document', 'file://' + filename])
        return policy_res
    
    @staticmethod
    def create_lambda_role(role_name, filename_trust_policy, executor=Executor()):
        """Creates an IAM role as role_name using the filename_trust_policy role policy document"""
        role_result = executor.exec_output(['aws', 'iam', 'create-role', '--role-name', role_name, '--assume-role-policy-document', 'file://' + filename_trust_policy])
        return role_result
    
    @staticmethod
    def get_arn_from_policy(policy):
        """Given the policy JSON returned by AWS-CLI, extract the ARN given to the policy and return it as a string"""
        pol = json.loads(policy)
        arn = pol['Policy']['Arn']
        return arn
        
    @staticmethod
    def get_arn_from_role(role):
        """Given the role JSON returned by AWS-CLI, extract the ARN given to the role and return it as a string"""
        r = json.loads(role)
        arn = r['Role']['Arn']
        return arn    
    
    @staticmethod
    def attach_policy_to_role(role_name, policy_arn, executor=Executor()):
        """Connect an IAM policy to a role using the AWS-CLI"""
        executor.call(['aws', 'iam', 'attach-role-policy','--role-name='+role_name, '--policy-arn', policy_arn])

class Lambda(object):

    @staticmethod
    def create_lambda_function(lambda_name, lambda_zip_filename, role_arn, collector_url, executor=Executor()):
        """Create a lambda function, lambda_name and upload the zip file containing the function.
        Also give the newly created lambda the IAM role given in role_arn, and set the description
        to collector_url
        """
        return executor.exec_output(['aws', 'lambda', 'create-function', '--function-name', lambda_name, '--runtime',
                                     'java8', '--role', role_arn, '--handler', 'com.snowplowanalytics.sources.awslambda.Main::handleRequest',
                                     '--zip-file', 'fileb://' + lambda_zip_filename, '--description', ' ' + collector_url, '--timeout', '120', '--memory-size', '512'])
        
    @staticmethod    
    def get_lambda_function_arn(lambda_json):
        """Given the AWS Lambda result json returned by AWS-CLI, extract the lambda's ARN and return it as a string"""
        r = json.loads(lambda_json)
        function_arn = r['FunctionArn']
        return function_arn

def get_lambda_zip_filename(args=[]):
    """Get the best candidate for a lambda zip path
    If there's a path in args[1], use that in preference to the current directory
    If there's nothing in args[1], look for a zip in the current directory (this will be the case in a download bundle)
    Throw an error if a good candidate cannot be found
    """
    if len(args) == 2:
        if os.path.isfile(args[1]):
            if args[1].endswith('.zip'):
                lambda_zip_filename = args[1]
            else: 
                raise ValueError("Lambda zip argument does not end with zip!")
        else:
            raise ValueError("Lambda zip argument does not exist or could not be read!")
    else:   
        zip_files = []

        for file in os.listdir("."):
            if file.endswith(".zip"):
                zip_files.append(file)
                
        if len(zip_files) > 1:
            raise ValueError("Couldn't establish which file is the lambda zip - many zips exist")
        elif len(zip_files) == 0:
            raise ValueError("Couldn't find lambda zip file in current directory")
        else:
            lambda_zip_filename = zip_files[0]
            
    return lambda_zip_filename
 
def make_lambda_config_desc(collector_url, app_id):
    """Make a configuration json for inserting into the lambda's description
    In the form {"collector_url":"abc", "app_id":"an_app_id"}"""
    
    if collector_url == None or app_id == None:
        raise ValueError("collector_url and app_id are required fields!")
    
    return "{\"collector_url\":\"" + collector_url + "\",\"app_id\":\"" + app_id + "\"}"
 
if __name__ == '__main__':
        
    if Shell.contains_aws_cli() == False:
        print "This script requires the AWS CLI to be installed and configured."
        print "See http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-set-up.html for more information"
        exit(1)
    
    lambda_zip_filename = ''
    try:
        lambda_zip_filename = get_lambda_zip_filename(sys.argv)
    except ValueError as e:
        print "Couldn't get lambda zip file: " + str(e)
        exit(1)  
        
    print "Using lambda function zip", lambda_zip_filename
    
    try:
      config = Configuration('config.yaml').conf
    except IOError as (_, strerror):
        print "Couldn't read file 'config.yaml': " + strerror 
        exit(1)
    except ValueError as e:
        print "Configuration file 'config.yaml' is invalid: " + str(e)
        exit(1)
    except Exception as e:
        print "Couldn't read configuration file 'config.yaml': " + str(e)
        exit(1)  

    existing_buckets = S3().available_buckets
    if existing_buckets == None or len(existing_buckets) == 0:
        raise ValueError("No existing buckets?")
        
    for bucket in config['s3']['buckets']:
        if not bucket in existing_buckets:
            print "Bucket '" + bucket + "' in config.yaml does not appear to exist!"
            print "\nAvailable buckets:\n"
            print "\n".join(existing_buckets)
            exit(1)
    
    print "Getting AWS account ID..."
    aws_account_id = AWS.get_account_id()
    print "Success: AWS account ID " + aws_account_id
    
    print "Setting up IAM policy for lambda function..."
    lambda_policy_arn = IAM.get_arn_from_policy(IAM.create_lambda_policy('perms.json'))
    print "Success: created lambda IAM policy as " + lambda_policy_arn
    
    print "Setting up IAM role for lambda function..."
    lambda_role_name = 'snowplow-s3-source'
    lambda_role_arn = IAM.get_arn_from_role(IAM.create_lambda_role(lambda_role_name,'lambda_trust_policy.json'))
    print "Success: created role " + lambda_role_name + " with arn " + lambda_role_arn
    
    print "Linking policy to role..."
    IAM.attach_policy_to_role(lambda_role_name, lambda_policy_arn)
    print "Success"
    
    print "Uploading lambda function..."
    lambda_name = 'snowplow-aws-lambda'

    lambda_desc = make_lambda_config_desc(config['snowplow']['collector'], config['snowplow']['app_id'])
    lambda_function_arn = Lambda.get_lambda_function_arn(Lambda.create_lambda_function(lambda_name, lambda_zip_filename, lambda_role_arn, lambda_desc))
    print "Success: uploaded lambda " + lambda_name + " with arn " + lambda_function_arn
     
    print "Adding notification rules to buckets..."    
    S3.add_bucket_notifications(lambda_name, lambda_function_arn, config['s3']['buckets'], aws_account_id)
    print "Success: buckets " + ",".join(config['s3']['buckets']) + " configured to notify AWS lambda on created/deleted events"
    
    print "Complete!"
    