from __future__ import annotations

import time
from typing import TYPE_CHECKING

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.request_actions.save_restore_app import (
    SaveRestoreRequestActions,
)
from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.shell.flows.connectivity.parse_request_service import (
    ParseConnectivityRequestService,
)

from cloudshell.cp.vcenter.flows import (
    SnapshotFlow,
    VCenterAutoloadFlow,
    VCenterPowerFlow,
    delete_instance,
    get_cluster_usage,
    get_deploy_flow,
    get_hints,
    get_vm_uuid_by_name,
    get_vm_web_console,
    reconfigure_vm,
    refresh_ip,
    validate_attributes,
)
from cloudshell.cp.vcenter.flows.affinity_rules_flow import AffinityRulesFlow
from cloudshell.cp.vcenter.flows.connectivity_flow import VCenterConnectivityFlow
from cloudshell.cp.vcenter.flows.customize_guest_os import customize_guest_os
from cloudshell.cp.vcenter.flows.save_restore_app import SaveRestoreAppFlow
from cloudshell.cp.vcenter.flows.vm_details import VCenterGetVMDetailsFlow
from cloudshell.cp.vcenter.models.connectivity_action_model import (
    VcenterConnectivityActionModel,
)
from cloudshell.cp.vcenter.models.deploy_app import (
    VCenterDeployVMRequestActions,
    VMFromImageDeployApp,
    VMFromLinkedCloneDeployApp,
    VMFromTemplateDeployApp,
    VMFromVMDeployApp,
)
from cloudshell.cp.vcenter.models.deployed_app import (
    StaticVCenterDeployedApp,
    VCenterDeployedVMActions,
    VCenterGetVMDetailsRequestActions,
    VMFromImageDeployedApp,
    VMFromLinkedCloneDeployedApp,
    VMFromTemplateDeployedApp,
    VMFromVMDeployedApp,
)
from cloudshell.cp.vcenter.resource_config import VCenterResourceConfig

if TYPE_CHECKING:
    from cloudshell.shell.core.driver_context import (
        AutoLoadCommandContext,
        AutoLoadDetails,
        CancellationContext,
        InitCommandContext,
        ResourceCommandContext,
        ResourceRemoteCommandContext,
        UnreservedResourceCommandContext,
    )


class VMwarevCenterCloudProviderShell2GDriver(ResourceDriverInterface):
    def cleanup(self):
        pass

    def __init__(self):
        for deploy_app_cls in (
            VMFromVMDeployApp,
            VMFromTemplateDeployApp,
            VMFromLinkedCloneDeployApp,
            VMFromImageDeployApp,
        ):
            VCenterDeployVMRequestActions.register_deployment_path(deploy_app_cls)

        for deployed_app_cls in (
            VMFromVMDeployedApp,
            VMFromTemplateDeployedApp,
            VMFromLinkedCloneDeployedApp,
            VMFromImageDeployedApp,
            StaticVCenterDeployedApp,
        ):
            VCenterDeployedVMActions.register_deployment_path(deployed_app_cls)

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
            logger.info("Starting Autoload command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)

            autoload_flow = VCenterAutoloadFlow(resource_config, logger)
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
            logger.info("Starting Deploy command")
            logger.debug(f"Request: {request}")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)

            cancellation_manager = CancellationContextManager(cancellation_context)
            reservation_info = ReservationInfo.from_resource_context(context)

            request_actions = VCenterDeployVMRequestActions.from_request(request, api)
            deploy_flow_class = get_deploy_flow(request_actions)
            deploy_flow = deploy_flow_class(
                resource_config=resource_config,
                reservation_info=reservation_info,
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
            logger.info("Starting Power On command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return VCenterPowerFlow(
                actions.deployed_app, resource_config, logger
            ).power_on()

    def PowerOff(self, context: ResourceRemoteCommandContext, ports: list[str]):
        """Called during sandbox's teardown.

        Can also be run manually by the sandbox end-user from the deployed
        App's commands pane. Method shuts down (or powers off) the VM instance.
        If the operation fails, method should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Off command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return VCenterPowerFlow(
                actions.deployed_app, resource_config, logger
            ).power_off()

    def PowerCycle(
        self, context: ResourceRemoteCommandContext, ports: list[str], delay
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Cycle command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            power_flow = VCenterPowerFlow(actions.deployed_app, resource_config, logger)
            power_flow.power_off()
            time.sleep(float(delay))
            power_flow.power_on()

    def remote_refresh_ip(
        self,
        context: ResourceRemoteCommandContext,
        cancellation_context: CancellationContext,
        ports: list[str],
    ):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by the sandbox
        end-user from the deployed App's commands pane. Method retrieves the VM's
        updated IP address from the cloud provider and sets it on the deployed App
        resource. Both private and public IPs are retrieved, as appropriate. If the
        operation fails, method should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Refresh IP command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            cancellation_manager = CancellationContextManager(cancellation_context)
            return refresh_ip(
                actions.deployed_app,
                resource_config,
                cancellation_manager,
                logger,
            )

    def GetVmDetails(
        self,
        context: ResourceCommandContext,
        requests: str,
        cancellation_context: CancellationContext,
    ):
        """Called when reserving a sandbox during setup.

        Call for each app in the sandbox can also be run manually by the sandbox
        end-user from the deployed App's VM Details pane. Method queries cloud provider
        for instance operating system, specifications and networking information and
        returns that as a json serialized driver response containing a list of
        VmDetailsData. If the operation fails, method should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get VM Details command")
            logger.debug(f"Requests: {requests}")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            cancellation_manager = CancellationContextManager(cancellation_context)
            actions = VCenterGetVMDetailsRequestActions.from_request(requests, api)
            return VCenterGetVMDetailsFlow(
                resource_config, cancellation_manager, logger
            ).get_vm_details(actions)

    def ApplyConnectivityChanges(self, context: ResourceCommandContext, request: str):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Apply Connectivity Changes command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            reservation_info = ReservationInfo.from_resource_context(context)
            parse_connectivity_req_service = ParseConnectivityRequestService(
                is_vlan_range_supported=True,
                is_multi_vlan_supported=True,
                connectivity_model_cls=VcenterConnectivityActionModel,
            )
            return VCenterConnectivityFlow(
                resource_config,
                reservation_info,
                parse_connectivity_req_service,
                logger,
            ).apply_connectivity(request)

    def DeleteInstance(self, context: ResourceRemoteCommandContext, ports: list[str]):
        """Called when removing a deployed App from the sandbox.

        Method deletes the VM from the cloud provider. If the operation fails, method
        should raise an exception.
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Delete Instance command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            reservation_info = ReservationInfo.from_remote_resource_context(context)
            delete_instance(
                actions.deployed_app, resource_config, reservation_info, logger
            )

    def SaveApp(
        self,
        context: ResourceCommandContext,
        request: str,
        cancellation_context: CancellationContext,
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Save App command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            cancellation_manager = CancellationContextManager(cancellation_context)
            actions = SaveRestoreRequestActions.from_request(request)
            return SaveRestoreAppFlow(
                resource_config, api, cancellation_manager, logger
            ).save_apps(actions.save_app_actions)

    def DeleteSavedApps(
        self,
        context: UnreservedResourceCommandContext,
        request: str,
        cancellation_context: CancellationContext,
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Delete Saved App command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            cancellation_manager = CancellationContextManager(cancellation_context)
            actions = SaveRestoreRequestActions.from_request(request)
            return SaveRestoreAppFlow(
                resource_config, api, cancellation_manager, logger
            ).delete_saved_apps(actions.delete_saved_app_actions)

    def remote_save_snapshot(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        snapshot_name: str,
        save_memory: str,
    ) -> str:
        """Saves virtual machine to a snapshot."""
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Save Snapshot command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).save_snapshot(snapshot_name, save_memory)

    def remote_restore_snapshot(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        snapshot_name: str,
    ):
        """Restores virtual machine from a snapshot."""
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Restore Snapshot command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).restore_from_snapshot(api, snapshot_name)

    def remote_get_snapshots(
        self, context: ResourceRemoteCommandContext, ports: list[str]
    ) -> str:
        """Returns list of snapshots."""
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Get Snapshots command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).get_snapshot_paths()

    def remote_remove_snapshot(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        snapshot_name: str,
        remove_child: str,
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Remove Snapshot command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).remove_snapshot(snapshot_name, remove_child)

    def orchestration_save(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        mode: str = "shallow",
        custom_params=None,
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Orchestration Save command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).orchestration_save()

    def orchestration_restore(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        saved_details: str,
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Orchestration Restore command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return SnapshotFlow(
                resource_config,
                actions.deployed_app,
                logger,
            ).orchestration_restore(saved_details, api)

    def get_vm_uuid(self, context: ResourceCommandContext, vm_name: str) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get VM UUID command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            return get_vm_uuid_by_name(resource_config, vm_name, logger)

    def get_cluster_usage(
        self, context: ResourceCommandContext, datastore_name: str
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get Cluster Usage command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            return get_cluster_usage(resource_config, datastore_name, logger)

    def reconfigure_vm(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        cpu: str | None,
        ram: str | None,
        hdd: str | None,
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Reconfigure VM command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            reconfigure_vm(
                resource_config,
                actions.deployed_app,
                cpu,
                ram,
                hdd,
                logger,
            )

    def get_vm_web_console(
        self, context: ResourceRemoteCommandContext, ports: list[str]
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get VM WEB Console command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return get_vm_web_console(resource_config, actions.deployed_app, logger)

    def get_attribute_hints(self, context: ResourceCommandContext, request: str) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get attribute hints command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            return get_hints(resource_config, request, logger)

    def validate_attributes(self, context: ResourceCommandContext, request: str) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Validate attributes command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            return validate_attributes(resource_config, request, logger)

    def customize_guest_os(
        self,
        context: ResourceRemoteCommandContext,
        ports: list[str],
        custom_spec_name: str,
        custom_spec_params: str,
        override_custom_spec: bool,
    ):
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Customize Guest OS command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            resource = context.remote_endpoints[0]
            actions = VCenterDeployedVMActions.from_remote_resource(resource, api)
            return customize_guest_os(
                resource_config,
                actions.deployed_app,
                custom_spec_name,
                custom_spec_params,
                override_custom_spec,
                logger,
            )

    def add_vm_to_affinity_rule(
        self,
        context: ResourceCommandContext,
        vm_paths: str,
        affinity_rule_name: str | None,
    ) -> str:
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Add VMs to Affinity Rule command")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context, api=api)
            reservation_info = ReservationInfo.from_resource_context(context)
            flow = AffinityRulesFlow(
                resource_config, reservation_info.reservation_id, logger
            )
            vm_paths = [path.strip() for path in vm_paths.split(";")]
            return flow.add_vms_to_affinity_rule(vm_paths, affinity_rule_name)
