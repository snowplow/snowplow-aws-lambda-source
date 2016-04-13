import deploy
import unittest
import json
import re
import subprocess
import os.path
import json

class MockExecutor(deploy.Executor):
   
    def __init__(self, return_code=0, so=""):
        self._stdout = so
        self._return_code = return_code
        self._exec_calls = []
        
    def exec_output(self, args):
        self._exec_calls.append(args)
        if (self._return_code != 0):
            raise subprocess.CalledProcessError('potato', 'banana', 'swift')
        return self._stdout

    def call(self, args):
        self._exec_calls.append(args)
        if (self._return_code != 0):
            raise subprocess.CalledProcessError('man', 'bear', 'pig')
        return self._return_code

    def get_call(self, index):
        return self._exec_calls[index]
        
    def get_call_count(self):
        return len(self._exec_calls)
        
class TestConfiguration(unittest.TestCase):
        
    def test_file_does_not_exist(self):
        with self.assertRaises(IOError) as m: deploy.Configuration("asdfasfdaf,afsdfa").conf
        
    def test_empty_str(self):
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str('')
        
    def test_missing_snowplow(self):
        co = """
s3:
    buckets:
        - abc
        - 123
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
    def test_missing_snowplow_collector(self):
        co = """
snowplow:
    #collector: http://helloworld.com
    app_id: com.lambda
s3:
    buckets:
        - abc
        - 123
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
      
    def test_empty_snowplow_collector(self):
        co = """
snowplow:
    collector:
    app_id: com.lambda
s3:
    buckets:
        - abc
        - 123
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
    def test_missing_s3(self):
        co = """
snowplow:
    collector: http://helloworld.com
    app_id: com.lambda
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
    def test_missing_s3_buckets(self):
        co = """
snowplow:
    collector: http://helloworld.com
    app_id: com.lambda
s3:
    hello: world
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
    def test_no_s3_buckets(self):
        co = """
snowplow:
    collector: http://helloworld.com
    app_id: com.lambda
s3:
    buckets:
"""
        with self.assertRaises(ValueError) as m: deploy.Configuration.parse_str(co)
        
    def test_empty_s3_buckets(self):
        co = """
snowplow:
    collector: http://helloworld.com
    app_id: com.lambda
s3:
    buckets:
        -
        -
"""
        with self.assertRaises(ValueError) as m: print str(deploy.Configuration.parse_str(co))
        
        
    def test_no_appid(self):
        co = """
snowplow:
    collector: http://helloworld.com
s3:
    buckets:
        - hello
        - world
"""
        with self.assertRaises(ValueError) as m: print str(deploy.Configuration.parse_str(co))
        
    def test_blank_appid(self):
        co = """
snowplow:
    collector: http://helloworld.com
    app_id: 
s3:
    buckets:
        - hello
        - world
"""
        with self.assertRaises(ValueError) as m: print str(deploy.Configuration.parse_str(co))
    
class TestShell(unittest.TestCase):
        
    def test_is_aws_cli(self):
        self.assertTrue(deploy.Shell.contains_aws_cli(MockExecutor(0)))
        self.assertFalse(deploy.Shell.contains_aws_cli(MockExecutor(1)))
        mock_executor = MockExecutor(0)
        deploy.Shell.contains_aws_cli(mock_executor)
        self.assertEquals(mock_executor.get_call(0), ['which', 'aws-cli'])

class TestS3Operations(unittest.TestCase):

   def test_get_bucket_list(self):
        executor = MockExecutor(0, '["hello", "world"]')
        buckets_json = deploy.S3.get_bucket_list(executor)
        self.assertEquals(executor.get_call(0), ['aws', 's3api', 'list-buckets', '--query', 'Buckets[].Name'])
                    
   def test_get_buckets(self):
        sample_bucket_list = """
          [
            "zero2hadoop", 
            "hadoopy-ed", 
            "leaky" 
          ]
        """
        mock_executor = MockExecutor(0, sample_bucket_list)
        b = deploy.S3.get_bucket_list(mock_executor)
        self.assertTrue(len(b)>0)
        buckets = deploy.S3.get_buckets_from_list(b)
        self.assertEquals(len(buckets), 3)  
    
   def test_available_buckets(self):
        sample_bucket_list = """
          [
            "zero2hadoop", 
            "hadoopy-ed", 
            "leaky" 
          ]
        """
        mock_executor = MockExecutor(0, sample_bucket_list)
        op = deploy.S3(mock_executor)
        self.assertEquals(op.available_buckets, ['zero2hadoop', 'hadoopy-ed', 'leaky'])               
                
   def test_attach_buckets(self):
        with self.assertRaises(ValueError) as cm: deploy.S3.add_bucket_notifications('abc', '1323', list(), 'hello')         
        
   def test_add_bucket_notifications(self):
        executor = MockExecutor(0)
        buckets = ['apple','orange']
        r = deploy.S3.add_bucket_notifications('lambda-func', 'arn123', buckets, '1234', executor)
        self.assertEquals(r, None)
        self.assertEquals(executor.get_call_count(), len(buckets)*2)
        expected_notification_conf = '{"CloudFunctionConfiguration":{"CloudFunction":"arn123","Events":["s3:ObjectCreated:*","s3:ObjectRemoved:*"]}}'
        self.assertFalse(None == json.loads(expected_notification_conf))
        
        expected_first_call = ['aws', 'lambda', 'add-permission', '--function-name', 'lambda-func', '--action', 'lambda:InvokeFunction', 
                               '--principal', 's3.amazonaws.com', '--source-arn', 'arn:aws:s3:::apple', '--source-account', '1234', '--statement-id', 'Id-1']
        expected_second_call = ['aws', 's3api', 'put-bucket-notification', '--bucket', 'apple', '--notification', expected_notification_conf]
        
        expected_third_call = ['aws', 'lambda', 'add-permission', '--function-name', 'lambda-func', '--action', 'lambda:InvokeFunction', 
                               '--principal', 's3.amazonaws.com', '--source-arn', 'arn:aws:s3:::orange', '--source-account', '1234', '--statement-id', 'Id-2']
        expected_fourth_call = ['aws', 's3api', 'put-bucket-notification', '--bucket', 'orange', '--notification', expected_notification_conf]
        
        self.assertEquals(executor.get_call(0), expected_first_call)
        self.assertEquals(executor.get_call(1), expected_second_call)
        self.assertEquals(executor.get_call(2), expected_third_call)
        self.assertEquals(executor.get_call(3), expected_fourth_call)
        
class TestAWSUtils(unittest.TestCase):
              
    def test_get_aws_account_id(self):
        executor = MockExecutor(0, "12345\n")
        id = deploy.AWS.get_account_id(executor)
        self.assertEquals(executor.get_call(0), ['aws', 'ec2', 'describe-security-groups', '--group-names', 'Default', '--query', 'SecurityGroups[0].OwnerId', '--output', 'text']) 
        self.assertEquals('12345', id)
        with self.assertRaises(subprocess.CalledProcessError) as m: deploy.AWS.get_account_id(MockExecutor(1))                              

class TestIAM(unittest.TestCase):

    def test_get_arn_from_policy(self):
        pol = """
                {
                    "Policy": {
                        "PolicyName": "***", 
                        "CreateDate": "2016-05-19T09:14:56.204Z", 
                        "AttachmentCount": 0, 
                        "IsAttachable": true, 
                        "PolicyId": "***", 
                        "DefaultVersionId": "v1", 
                        "Path": "/", 
                        "Arn": "arn:aws:iam::123:policy/snowplow-s3-source", 
                        "UpdateDate": "2016-05-19T09:14:56.204Z"
                    }
                } 
              """
        arn = deploy.IAM.get_arn_from_policy(pol)
        self.assertEquals(arn, 'arn:aws:iam::123:policy/snowplow-s3-source')
        
    def test_get_arn_from_role(self):
        pol = """
           {
                "Role": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17", 
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole", 
                                "Principal": {
                                    "Service": "lambda.amazonaws.com"
                                }, 
                                "Effect": "Allow", 
                                "Sid": ""
                            }
                        ]
                    }, 
                    "RoleId": "***", 
                    "CreateDate": "2016-05-19T09:26:07.305Z", 
                    "RoleName": "snowplow-s3-source", 
                    "Path": "/", 
                    "Arn": "arn:aws:iam::123:role/snowplow-s3-source"
                }
            }        
        """
        arn = deploy.IAM.get_arn_from_role(pol)
        self.assertEquals(arn, 'arn:aws:iam::123:role/snowplow-s3-source')
               
    def test_create_lambda_policy(self):
        sample_json = '{"hello":"world"}'
        executor = MockExecutor(0, sample_json)
        r = deploy.IAM.create_lambda_policy('lambda.json',executor)
        self.assertEquals(executor.get_call(0), ['aws', 'iam', 'create-policy', '--policy-name', 'snowplow-s3-source', '--policy-document', 'file://lambda.json'])
        self.assertEquals(r, sample_json)
        
    def test_create_lambda_role(self):
        sample_json = '{"hello":"world"}'
        executor = MockExecutor(0, sample_json)
        r = deploy.IAM.create_lambda_role('sp-s3','tp.json', executor)
        self.assertEquals(executor.get_call(0), ['aws', 'iam', 'create-role', '--role-name', 'sp-s3', '--assume-role-policy-document', 'file://tp.json'])
        self.assertEquals(r, sample_json)
    
    def test_attach_policy_to_role(self):
        sample_json = '{"hello":"world"}'
        executor = MockExecutor(0, sample_json)
        r = deploy.IAM.attach_policy_to_role('hello', 'world', executor)
        self.assertEquals(executor.get_call(0), ['aws', 'iam', 'attach-role-policy','--role-name=hello', '--policy-arn', 'world'])
        self.assertEquals(r, None)

class TestLambda(unittest.TestCase):    
           
    def test_get_lambda_arn_from_lambda(self):
        res = """
            {
                "CodeSha256": "G4L8Rcdlc0vLY69GUOwzujApBge9ViRkHoxtMuii9Tg=", 
                "FunctionName": "snowplow-aws-lambda", 
                "CodeSize": 38563260, 
                "MemorySize": 128, 
                "FunctionArn": "arn:aws:lambda:eu-west-1:123:function:snowplow-aws-lambda", 
                "Version": "$LATEST", 
                "Role": "arn:aws:iam::123:role/snowplow-s3-source", 
                "Timeout": 120, 
                "LastModified": "2016-05-19T09:55:08.102+0000", 
                "Handler": "com.snowplowanalytics.sources.awslambda.Main::handleRequest", 
                "Runtime": "java8", 
                "Description": " "
            }
            """
        arn = deploy.Lambda.get_lambda_function_arn(res)
        self.assertEquals(arn, 'arn:aws:lambda:eu-west-1:123:function:snowplow-aws-lambda')
        
    def test_create_lambda_function(self):
        expected = ['aws', 'lambda', 'create-function', '--function-name', 'lambda-name', '--runtime',
                    'java8', '--role', 'role-arn-123', '--handler', 'com.snowplowanalytics.sources.awslambda.Main::handleRequest',
                    '--zip-file', 'fileb://lambda.zip', '--description', ' http://abc.com', '--timeout', '120', '--memory-size', '512']
        executor = MockExecutor(0, "stdout")
        r = deploy.Lambda.create_lambda_function('lambda-name', 'lambda.zip', 'role-arn-123', 'http://abc.com', executor)
        self.assertEquals(executor.get_call(0), expected)
        self.assertEquals(r, "stdout")      
        
        
class MiscTest(unittest.TestCase):

    def test_get_lambda_zip_dir(self):
        try:
            os.utime("test.zip", None)
        except:
            open("test.zip", 'a').close()
            
        self.assertEquals("test.zip", deploy.get_lambda_zip_filename("abc"))
        self.assertEquals("test.zip", deploy.get_lambda_zip_filename(["abc", "test.zip"]))

        os.remove("test.zip")
        
        with self.assertRaises(ValueError) as m: deploy.get_lambda_zip_filename(["abc", "deploy.py"])
        with self.assertRaises(ValueError) as m: deploy.get_lambda_zip_filename(["abc", "abc.zip"]) 
        with self.assertRaises(ValueError) as m: deploy.get_lambda_zip_filename(["abc"])        
        
    def test_make_lambda_config_desc(self):
        r = deploy.make_lambda_config_desc("collector_url", "app_id")
        self.assertEquals("""{"collector_url":"collector_url","app_id":"app_id"}""", r)
        json.loads(r)
        with self.assertRaises(ValueError) as m: deploy.make_lambda_config_desc(None, "abc")
        with self.assertRaises(ValueError) as m: deploy.make_lambda_config_desc("abc", None) 
        with self.assertRaises(ValueError) as m: deploy.make_lambda_config_desc(None, None)
                
if __name__ == '__main__':
    unittest.main()
    