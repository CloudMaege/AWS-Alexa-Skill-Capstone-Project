# -*- coding: utf-8 -*-

# This is a simple Alexa Skill, built using the implementation
# of the handler classes approach in skill builder.
import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

##################################
###       Custom Skill        ####
###       Built In Intents    ####
##################################

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Initiating Cloud Voice, your voice powered interface for A. W. S."

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "You can ask me about your A. W. S account!"

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
                "Cloud Voice", speech_text))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = (
            "The Cloud Voice skill can't help you with that.  "
            "You can say Cloud Voice!!")
        reprompt = "You can say Cloud Voice!!"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


##################################
###       Custom Skill        ####
###       Gather Servers      ####
##################################

class GatherCostIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("GatherCostIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import json
        import boto3
        import datetime
        client = boto3.client('ce')

        current_month = str(datetime.date.today()) # 2023-01-18
        first_current_month = str(                 # 2023-01-01
            str(datetime.datetime.now().year) + '-' +
            str(datetime.datetime.now().month).zfill(2) + '-' + '01'
        )
    
        response = client.get_cost_and_usage( 
                        TimePeriod={ 
                            'Start': first_current_month, 
                            'End': current_month 
                        },
                        Granularity='MONTHLY',
                        Metrics=['UnblendedCost']
                    )
                    
        bill=response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        speech_text = f"Your AWS cost for this month are {bill[:5]} dollars"
        
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherInstanceCountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherInstanceCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0
        prodCount = 0
        stageCount = 0
        devCount = 0 
        untaggedCount = 0
        
        # Define Instance Filter
        Filter = [{
            'Name': 'instance-state-name',
            'Values': ['running', 'Running']
        }]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            totalCount += 1
            
            # Breakdown the Count by Env
            if instance.tags is not None and 'Env' not in [t['Key'] for t in instance.tags]:
                untaggedCount += 1
            else:
                for tag in instance.tags:
                    if tag.get('Key').lower() == "env" or tag.get('Key').lower() == "environment":
                        if tag.get('Value').lower() == 'prod' or tag.get('Value').lower() == 'production':
                            prodCount += 1
                        elif tag.get('Value').lower() == 'stage' or tag.get('Value').lower() == 'staging':
                            stageCount += 1
                        elif tag.get('Value').lower() == 'dev' or tag.get('Value').lower() == 'development':
                            devCount += 1
            
        # Form response
        if totalCount > 0:
            if totalCount == 1:
                # Determine the single instance env
                instanceEnv = None
                instanceEnv = 'production' if prodCount > 0 else instanceEnv
                instanceEnv = 'stage' if stageCount > 0 else instanceEnv
                instanceEnv = 'dev' if devCount > 0 else instanceEnv
                instanceEnv = 'untagged' if untaggedCount > 0 else instanceEnv
                speech_text = f"There is {totalCount} {instanceEnv} server currently running."
            elif totalCount > 1:
                speech_text = f"There are {totalCount} servers currently running. {prodCount} production, {stageCount} stage instances, {devCount} dev instances, and {untaggedCount} untagged."
        else:
            speech_text = "I could not find any servers that are currently in a running state."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherProdCountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherProdCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0

        # Define Instance Filter
        Filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'Running']
            },
            {
                'Name':'tag:Env',
                'Values':['prod', 'Prod', 'production', 'Production']
            }
        ]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            totalCount += 1
            
        # Form response
        if totalCount > 0:
            if totalCount == 1:
                speech_text = f"There is {totalCount} production server currently running."
            elif totalCount > 1:
                speech_text = f"There are {totalCount} production servers currently running."
        else:
            speech_text = "I could not find any production servers that are currently in a running state."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherStageCountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherStageCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0
        
        # Define Instance Filter
        Filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'Running']
            },
            {
                'Name':'tag:Env',
                'Values':['stage', 'Stage', 'staging', 'Staging']
            }
        ]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            totalCount += 1
            
        # Form response
        if totalCount > 0:
            if totalCount == 1:
                speech_text = f"There is {totalCount} staging server currently running."
            elif totalCount > 1:
                speech_text = f"There are {totalCount} staging servers currently running."
        else:
            speech_text = "I could not find any staging servers that are currently in a running state."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherDevCountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherDevCountIntent")(handler_input)


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0
        
        # Define Instance Filter
        Filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'Running']
            },
            {
                'Name':'tag:Env',
                'Values':['dev', 'Dev', 'development', 'Development']
            }
        ]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            totalCount += 1
            
        # Form response
        if totalCount > 0:
            if totalCount == 1:
                speech_text = f"There is {totalCount} development server currently running."
            elif totalCount > 1:
                speech_text = f"There are {totalCount} development servers currently running."
        else:
            speech_text = "I could not find any staging development that are currently in a running state."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherUntaggedCountIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherUntaggedCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0
        
        # Define Instance Filter
        Filter = [{
            'Name': 'instance-state-name',
            'Values': ['running', 'Running']
        }]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            if instance.tags is not None and 'Env' not in [t['Key'] for t in instance.tags]:
                totalCount += 1
            
        # Form response
        if totalCount > 0:
            if totalCount == 1:
                speech_text = f"There is {totalCount} untagged server currently running."
            elif totalCount > 1:
                speech_text = f"There are {totalCount} untagged servers currently running."
        else:
            speech_text = "I could not find any untagged servers that are currently in a running state."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class StopNonProdInstancesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StopNonProdInstancesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        totalCount = 0
        stopCount = 0
        prodCount = 0
        
        # Define Instance Filter
        Filter = [{
            'Name': 'instance-state-name',
            'Values': ['running', 'Running']
        }]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total Counter
            totalCount += 1

            # Breakdown the Count by Env
            if instance.tags is not None and 'Env' not in [t['Key'] for t in instance.tags]:
                instance.stop()
                stopCount += 1
            else:
                for tag in instance.tags:
                    if tag.get('Key').lower() == "env" or tag.get('Key').lower() == "environment":
                        if tag.get('Value').lower() == 'prod' or tag.get('Value').lower() == 'production':
                            prodCount += 1
                        elif tag.get('Value').lower() == 'stage' or tag.get('Value').lower() == 'staging':
                            instance.stop()
                            stopCount += 1
                        elif tag.get('Value').lower() == 'dev' or tag.get('Value').lower() == 'development':
                            instance.stop()
                            stopCount += 1
        # Form response
        if stopCount > 0:
            speech_text = f"{stopCount} of {totalCount} running servers were non production and have been shutdown. None of the {prodCount} production servers were affected."
        else:
            speech_text = "No running non production servers were found. No actions have been taken"

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class StopProdInstancesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StopProdInstancesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speech_text = "I am not allowed to shutdown production servers at this time, please blame the Cloud Voice development team, but I must warn you, they aren't any fun."

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class StopStageInstancesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StopStageInstancesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        stopCount = 0
        
        # Define Instance Filter
        Filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'Running']
            },
            {
                'Name':'tag:Env',
                'Values':['stage', 'Stage', 'staging', 'Staging']
            }
        ]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            stopCount += 1
            instance.stop()
            
        # Form response
        if stopCount > 0:
            if stopCount == 1:
                speech_text = f"{stopCount} staging server has been shutdown."
            elif stopCount > 1:
                speech_text = f"{stopCount} staging servers have been shutdown."
        else:
            speech_text = "I could not find any staging servers to shutdown, you can go back to sleep and dream of being the frugal rockstar that you are!"

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class StopDevInstancesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StopDevInstancesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        stopCount = 0
        
        # Define Instance Filter
        Filter = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'Running']
            },
            {
                'Name':'tag:Env',
                'Values':['dev', 'Dev', 'development', 'Development']
            }
        ]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            # Increment Total
            stopCount += 1
            instance.stop()
            
        # Form response
        if stopCount > 0:
            if stopCount == 1:
                speech_text = f"{stopCount} development server has been shutdown."
            elif stopCount > 1:
                speech_text = f"{stopCount} development servers have been shutdown."
        else:
            speech_text = "I could not find any development servers to shutdown, you can go back to sleep and dream of being the frugal rockstar that you are!"

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class StopUntaggedInstancesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("StopUntaggedInstanceIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Define Counters
        stopCount = 0
        
        # Define Instance Filter
        Filter = [{
            'Name': 'instance-state-name',
            'Values': ['running', 'Running']
        }]

        # Instantiate EC2 Object
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(Filters=Filter)
        
        # Count all the things
        for instance in instances:
            if instance.tags is not None and 'Env' not in [t['Key'] for t in instance.tags]:
                stopCount += 1
                instance.stop()
            
        # Form response
        if stopCount > 0:
            if stopCount == 1:
                speech_text = f"{stopCount} untagged server has been shutdown."
            elif stopCount > 1:
                speech_text = f"{stopCount} untagged servers have been shutdown."
        else:
            speech_text = "I could not find any untagged servers to shutdown, Tell your manager you team deserves a raise, all of your are properly tagged!"

        # Alexa the speech things
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Cloud Voice", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GatherPublicAccessBucketsHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GatherPublicAccessBucketsIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import botocore
        import json
        import sys

        public_acl_indicator = 'http://acs.amazonaws.com/groups/global/AllUsers'
        permissions_to_check = ['READ', 'WRITE']
        public_buckets = []

        s3client = boto3.client('s3')
    
        list_bucket_response = s3client.list_buckets()

        for bucket_dictionary in list_bucket_response['Buckets']:
            try:        
                bucket_public_access_response = s3client.get_public_access_block(Bucket=bucket_dictionary['Name'])['PublicAccessBlockConfiguration']
            
                if not (bucket_public_access_response['BlockPublicAcls'] and bucket_public_access_response['IgnorePublicAcls'] and bucket_public_access_response['BlockPublicPolicy'] and bucket_public_access_response['RestrictPublicBuckets']):
                    public_buckets.append(bucket_dictionary['Name'])
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    print('No Public Access')
            else:
                print("unexpected error")            

        speech_text = f"I found {len(public_buckets)} buckets with public permissions: "
        
        for bucket_name in public_buckets:
            speech_text += bucket_name + ", "

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class GetECInstanceTypesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GetECInstanceTypesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import botocore
        import json

        AWS_REGION = "us-east-1"
        EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)

        filters = [
            {
                'Name': 'instance-state-name', 
                'Values': ['running']
            }
        ]

        instances = EC2_RESOURCE.instances.filter(Filters=filters)
        myList=[]
        for instance in instances:
            myList.append(instance.instance_type)

        myListoftypes=list(set(myList))
        myNumofinstances=str(len(myList))
        myTypeofinstances=str(len(myListoftypes))
        myBoringstringofinfo=''
        print('Number of instances: ' + myNumofinstances )
        print('Number of different EC2 instance types: ' + myTypeofinstances)
        for type in myListoftypes:
            myNumoftype=myList.count(type)
            mystrType=str(type)
            mystrNumoftype=str(myNumoftype)
            print('Number of ' + mystrType + ': ' + mystrNumoftype)
            if (myNumoftype>1):
                print('greater than 1')
                myBoringstringofinfo=myBoringstringofinfo + ' ' + mystrNumoftype + ' are ' + mystrType + ';'
            elif (myNumoftype>0):
                print('greater 0')
                myBoringstringofinfo=myBoringstringofinfo + ' ' + mystrNumoftype + ' is ' + mystrType + ';'

        speech_text = "There are {} running instances of which {}".format(myNumofinstances,myBoringstringofinfo)
        print(speech_text)

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


class DescribeInstanceIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("DescribeInstanceIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        import boto3
        import json

        # Instantiate Boto Client
        client = boto3.client('ec2')

        # Fetch Instances
        key=event.get('key')
        fetchInstances = client.describe_instances(Filters=[{'Name': 'tag:Name','Values': [key]}])
        
        print(fetchInstances)
        for r in fetchInstances['Reservations']:
            for i in r['Instances']:
                a=i['Placement']
                t=i['InstanceType']
    
        print(t)
        speech_text = f"Instance {[key]}  is a {[t]} , hosted in Availability Zone {a['AvailabilityZone']}."

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)

        # Return response
        return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
sb.add_request_handler(GatherCostIntentHandler())
sb.add_request_handler(GatherInstanceCountIntentHandler())
sb.add_request_handler(GatherProdCountIntentHandler())
sb.add_request_handler(GatherStageCountIntentHandler())
sb.add_request_handler(GatherDevCountIntentHandler())
sb.add_request_handler(GatherUntaggedCountIntentHandler())
sb.add_request_handler(StopNonProdInstancesIntentHandler())
sb.add_request_handler(StopProdInstancesIntentHandler())
sb.add_request_handler(StopStageInstancesIntentHandler())
sb.add_request_handler(StopDevInstancesIntentHandler())
sb.add_request_handler(StopUntaggedInstancesIntentHandler())
sb.add_request_handler(GatherPublicAccessBucketsHandler())
sb.add_request_handler(GetECInstanceTypesIntentHandler())
sb.add_request_handler(DescribeInstanceIntentHandler())

lambda_handler = sb.lambda_handler()
