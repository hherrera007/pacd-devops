import aws_cdk as core
import aws_cdk.assertions as assertions

from pacd_devops.pacd_devops_stack import PacdDevopsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in pacd_devops/pacd_devops_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PacdDevopsStack(app, "pacd-devops")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
