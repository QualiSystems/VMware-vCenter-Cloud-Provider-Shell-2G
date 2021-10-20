from typing import TYPE_CHECKING

from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.cp.vcenter.api_client import VCenterAPIClient
from cloudshell.cp.vcenter.commands.command_orchestrator import CommandOrchestrator
from cloudshell.cp.vcenter.flows.autoload import VCenterAutoloadFlow
from cloudshell.cp.vcenter.resource_config import VCenterResourceConfig

if TYPE_CHECKING:
    from cloudshell.shell.core.driver_context import (
        AutoLoadCommandContext,
        AutoLoadDetails,
        InitCommandContext,
    )


class VMwarevCenterCloudProviderShell2GDriver(ResourceDriverInterface):
    def cleanup(self):
        pass

    def __init__(self):
        """Init function.

        ctor must be without arguments, it is created with reflection at run time
        """
        self.command_orchestrator = CommandOrchestrator()  # type: CommandOrchestrator
        self.deployments = {}
        self.deployments[
            "VMware vCenter Cloud Provider 2G.vCenter VM From VM 2G"
        ] = self.deploy_clone_from_vm
        self.deployments[
            "VMware vCenter Cloud Provider 2G.vCenter VM From Linked Clone 2G"
        ] = self.deploy_from_linked_clone
        self.deployments[
            "VMware vCenter Cloud Provider 2G.vCenter VM From Template 2G"
        ] = self.deploy_from_template
        self.deployments[
            "VMware vCenter Cloud Provider 2G.vCenter VM From Image 2G"
        ] = self.deploy_from_image

    def initialize(self, context: "InitCommandContext"):
        pass

    def get_inventory(self, context: "AutoLoadCommandContext") -> "AutoLoadDetails":
        """Called when the cloud provider resource is created in the inventory.

        Method validates the values of the cloud provider attributes, entered by
        the user as part of the cloud provider resource creation. In addition,
        this would be the place to assign values programmatically to optional
        attributes that were not given a value by the user. If one of the
        validations failed, the method should raise an exception
        :param context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource
        you can return an AutoLoadDetails object
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Autoload command...")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)

            vcenter_client = VCenterAPIClient(
                host=resource_config.address,
                user=resource_config.user,
                password=resource_config.password,
                logger=logger,
            )

            autoload_flow = VCenterAutoloadFlow(
                resource_config=resource_config,
                vcenter_client=vcenter_client,
                logger=logger,
            )

            return autoload_flow.discover()

    def ApplyConnectivityChanges(self, context, request):
        return self.command_orchestrator.connect_bulk(context, request)

    def disconnect_all(self, context, ports):
        return self.command_orchestrator.disconnect_all(context, ports)

    def disconnect(self, context, ports, network_name):
        return self.command_orchestrator.disconnect(context, ports, network_name)

    def DeleteInstance(self, context, ports):
        return self.command_orchestrator.DeleteInstance(context, ports)

    def remote_refresh_ip(self, context, cancellation_context, ports):
        return self.command_orchestrator.refresh_ip(
            context, cancellation_context, ports
        )

    def PowerOff(self, context, ports):
        return self.command_orchestrator.power_off(context, ports)

    # the name is by the Qualisystems conventions
    def PowerOn(self, context, ports):
        """Powers off the remote vm.

        :param models.QualiDriverModels.ResourceRemoteCommandContext context:
            the context the command runs on
        :param list[string] ports: the ports of the connection between the remote
            resource and the local resource, NOT IN USE!!!
        """
        return self.command_orchestrator.power_on(context, ports)

    # the name is by the Qualisystems conventions
    def PowerCycle(self, context, ports, delay):
        return self.command_orchestrator.power_cycle(context, ports, delay)

    def Deploy(self, context, request=None, cancellation_context=None):
        actions = self.request_parser.convert_driver_request_to_actions(request)
        deploy_action = single(actions, lambda x: isinstance(x, DeployApp))  # noqa
        deployment_name = deploy_action.actionParams.deployment.deploymentPath

        if deployment_name in self.deployments.keys():
            deploy_method = self.deployments[deployment_name]
            deploy_result = deploy_method(context, deploy_action, cancellation_context)
            return DriverResponse([deploy_result]).to_driver_response_json()  # noqa
        else:
            raise Exception("Could not find the deployment")

    def SaveApp(self, context, request, cancellation_context=None):
        actions = self.request_parser.convert_driver_request_to_actions(request)
        save_actions = [x for x in actions if isinstance(x, SaveApp)]  # noqa
        save_app_results = self.command_orchestrator.save_sandbox(
            context, save_actions, cancellation_context
        )
        return DriverResponse(save_app_results).to_driver_response_json()  # noqa

    def DeleteSavedApps(self, context, request, cancellation_context=None):
        actions = self.request_parser.convert_driver_request_to_actions(request)
        delete_actions = [x for x in actions if isinstance(x, DeleteSavedApp)]  # noqa
        save_app_results = self.command_orchestrator.delete_saved_sandbox(
            context, delete_actions, cancellation_context
        )
        return DriverResponse(save_app_results).to_driver_response_json()  # noqa

    def deploy_from_template(self, context, deploy_action, cancellation_context):
        return self.command_orchestrator.deploy_from_template(
            context, deploy_action, cancellation_context
        )

    def deploy_clone_from_vm(self, context, deploy_action, cancellation_context):
        return self.command_orchestrator.deploy_clone_from_vm(
            context, deploy_action, cancellation_context
        )

    def deploy_from_linked_clone(self, context, deploy_action, cancellation_context):
        return self.command_orchestrator.deploy_from_linked_clone(
            context, deploy_action, cancellation_context
        )

    def deploy_from_image(self, context, deploy_action, cancellation_context):
        if cancellation_context is None:
            cancellation_context = CancellationContext()  # noqa: F821
        return self.command_orchestrator.deploy_from_image(
            context, deploy_action, cancellation_context
        )

    def remote_save_snapshot(self, context, ports, snapshot_name, save_memory):
        """Saves virtual machine to a snapshot.

        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between the
        remote resource and the local resource
        :type ports: list[string]
        :param snapshot_name: snapshot name to save to
        :type snapshot_name: str
        :param save_memory: Snapshot the virtual machine's memory. Lookup, Yes / No
        :type save_memory: str
        :return:
        """
        return self.command_orchestrator.save_snapshot(
            context, snapshot_name, save_memory
        )

    def remote_restore_snapshot(self, context, ports, snapshot_name):
        """Restores virtual machine from a snapshot.

        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between
        the remote resource and the local resource
        :type ports: list[string]
        :param snapshot_name: Snapshot name to restore from
        :type snapshot_name: str
        :return:
        """
        return self.command_orchestrator.restore_snapshot(context, snapshot_name)

    def remote_get_snapshots(self, context, ports):
        """Returns list of snapshots.

        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between
        the remote resource and the local resource
        :type ports: list[string]
        :return: list
        """
        return self.command_orchestrator.get_snapshots(context)

    def orchestration_save(self, context, ports, mode="shallow", custom_params=None):
        return self.command_orchestrator.orchestration_save(
            context, mode, custom_params
        )

    def orchestration_restore(self, context, ports, saved_details):
        return self.command_orchestrator.orchestration_restore(context, saved_details)

    def get_vm_uuid(self, context, vm_name):
        return self.command_orchestrator.get_vm_uuid_by_name(context, vm_name)

    def get_cluster_usage(self, context, datastore_name):
        return self.command_orchestrator.get_cluster_usage(context, datastore_name)

    def GetVmDetails(self, context, cancellation_context, requests):
        return self.command_orchestrator.get_vm_details(
            context, cancellation_context, requests
        )

    def reconfigure_vm(self, context, ports, cpu, ram, hdd):
        return self.command_orchestrator.reconfigure_vm(context, cpu, ram, hdd)

    def get_vm_web_console(self, context, ports):
        return self.command_orchestrator.get_vm_web_console(context)
