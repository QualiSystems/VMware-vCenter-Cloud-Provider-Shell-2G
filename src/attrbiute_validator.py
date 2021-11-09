import json

from cloudshell.cp.vcenter.common.utilites.command_result import set_command_result


class ValidateAttributesRequest:
    def __init__(self, action_id, deployment_path, attributes):
        self.action_id = action_id
        self.deployment_path = deployment_path
        self.attributes = attributes


class ValidateAttributesResponse:
    def __init__(self, action_id, success=True, message=""):
        self.success = success
        self.action_id = action_id
        self.message = message


class ValidatorAttributes:
    def __init__(self):
        self.action_id = None

    def parse_request(self, request):
        parsed_request = json.loads(request)
        deployment_path = parsed_request.get("DeploymentPath")
        self.action_id = parsed_request.get("ActionId")
        _attributes = parsed_request.get("Attributes")
        attributes = {attr.get("AttributeName"): attr.get("Value") for attr in _attributes}
        return ValidateAttributesRequest(self.action_id, deployment_path, attributes)

    def get_response(self, validate_request):
        res = ValidateAttributesResponse(validate_request.action_id, message=validate_request.attributes)
        return set_command_result(result=res, unpicklable=False)
