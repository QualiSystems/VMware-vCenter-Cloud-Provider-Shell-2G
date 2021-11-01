from __future__ import annotations

import time
from typing import TYPE_CHECKING

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.request_actions import DeployedVMActions, DeployVMRequestActions
from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.cp.vcenter.api_client import VCenterAPIClient
from cloudshell.cp.vcenter.commands.command_orchestrator import CommandOrchestrator
from cloudshell.cp.vcenter.flows.autoload import VCenterAutoloadFlow
from cloudshell.cp.vcenter.flows.deploy_vm import get_deploy_flow
from cloudshell.cp.vcenter.flows.power_flow import VCenterPowerFlow
from cloudshell.cp.vcenter.models import deploy_app, deployed_app
from cloudshell.cp.vcenter.resource_config import VCenterResourceConfig

if TYPE_CHECKING:
    from cloudshell.shell.core.driver_context import (
        AutoLoadCommandContext,
        AutoLoadDetails,
        CancellationContext,
        InitCommandContext,
        ResourceCommandContext,
        ResourceRemoteCommandContext,
    )


class VMwarevCenterCloudProviderShell2GDriver(ResourceDriverInterface):
    def cleanup(self):
        pass

    def __init__(self):
        self.command_orchestrator = CommandOrchestrator()  # type: CommandOrchestrator
        for deploy_app_cls in (
            deploy_app.VMFromVMDeployApp,
            deploy_app.VMFromTemplateDeployApp,
            deploy_app.VMFromLinkedCloneDeployApp,
            deploy_app.VMFromImageDeployApp,
        ):
            DeployVMRequestActions.register_deployment_path(deploy_app_cls)

        for deployed_app_cls in (
            deployed_app.VMFromVMDeployApp,
            deployed_app.VMFromTemplateDeployApp,
            deployed_app.VMFromLinkedCloneDeployApp,
            deployed_app.VMFromImageDeployApp,
        ):
            DeployedVMActions.register_deployment_path(deployed_app_cls)

    def initialize(self, context: InitCommandContext):
        pass

    def get_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
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

    def Deploy(
        self,
        context: ResourceCommandContext,
        request: str,
        cancellation_context: CancellationContext,
    ) -> str:
        """Called when reserving a sandbox during setup.

        Method creates the compute resource in the cloud provider - VM instance or
        container. If App deployment fails, return a "success false" action result.
        :param request: A JSON string with the list of requested deployment actions
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Deploy command...")
            logger.debug(f"Request: {request}")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)

            cancellation_manager = CancellationContextManager(cancellation_context)
            reservation_info = ReservationInfo.from_resource_context(context)
            vcenter_client = VCenterAPIClient(
                host=resource_config.address,
                user=resource_config.user,
                password=resource_config.password,
                logger=logger,
            )

            request_actions = DeployVMRequestActions.from_request(request, api)
            deploy_flow_class = get_deploy_flow(request_actions)
            deploy_flow = deploy_flow_class(
                resource_config=resource_config,
                reservation_info=reservation_info,
                vcenter_client=vcenter_client,
                cs_api=api,
                cancellation_manager=cancellation_manager,
                logger=logger,
            )
            return deploy_flow.deploy(request_actions=request_actions)

    def PowerOn(self, context: ResourceRemoteCommandContext, ports: list[str]):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by
        the sandbox end-user from the deployed App's commands pane.
        Method spins up the VM If the operation fails, method should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power On command...")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            vcenter_client = VCenterAPIClient(
                host=resource_config.address,
                user=resource_config.user,
                password=resource_config.password,
                logger=logger,
            )
            resource = context.remote_endpoints[0]
            actions = DeployedVMActions.from_remote_resource(resource, api)
            return VCenterPowerFlow(
                vcenter_client, actions.deployed_app, resource_config, logger
            ).power_on()

    def PowerOff(self, context: ResourceRemoteCommandContext, ports: list[str]):
        """Called during sandbox's teardown.

        Can also be run manually by the sandbox end-user from the deployed
        App's commands pane. Method shuts down (or powers off) the VM instance.
        If the operation fails, method should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Off command...")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            vcenter_client = VCenterAPIClient(
                host=resource_config.address,
                user=resource_config.user,
                password=resource_config.password,
                logger=logger,
            )
            resource = context.remote_endpoints[0]
            actions = DeployedVMActions.from_remote_resource(resource, api)
            return VCenterPowerFlow(
                vcenter_client, actions.deployed_app, resource_config, logger
            ).power_off()

    def PowerCycle(
        self, context: ResourceRemoteCommandContext, ports: list[str], delay
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Cycle command...")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            vcenter_client = VCenterAPIClient(
                host=resource_config.address,
                user=resource_config.user,
                password=resource_config.password,
                logger=logger,
            )
            resource = context.remote_endpoints[0]
            actions = DeployedVMActions.from_remote_resource(resource, api)
            power_flow = VCenterPowerFlow(
                vcenter_client, actions.deployed_app, resource_config, logger
            )
            power_flow.power_off()
            time.sleep(float(delay))
            power_flow.power_on()

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
