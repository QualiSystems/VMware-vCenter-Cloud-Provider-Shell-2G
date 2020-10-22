from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.cp.core.request_actions import DeployVMRequestActions, GetVMDetailsRequestActions, DeployedVMActions
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.cp.vcenter.resource_config import VCenterResourceConfig
from cloudshell.cp.vcenter.api.client import VCenterAPIClient
from cloudshell.cp.vcenter.flows.autoload import VCenterAutoloadFlow
from cloudshell.cp.vcenter.flows.deploy_vm.vm_from_vm import VCenterDeployVMfromVMFlow
from cloudshell.cp.vcenter.models import deploy_app


class VMwarevCenterCloudProviderShell2GDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """Called every time a new instance of the driver is created.

        This method can be left unimplemented but this is a good place to load and cache the driver configuration,
        initiate sessions etc. Whatever you choose, do not remove it.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def get_inventory(self, context):
        """Called when the cloud provider resource is created in the inventory.

        Method validates the values of the cloud provider attributes, entered by the user as part of the cloud provider
        resource creation. In addition, this would be the place to assign values programmatically to optional attributes
        that were not given a value by the user. If one of the validations failed, the method should raise an exception
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Autoload command...")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context=context,
                                                                 api=api)

            vcenter_client = VCenterAPIClient(host=resource_config.address,
                                              user=resource_config.user,
                                              password=resource_config.password,
                                              logger=logger)

            autoload_flow = VCenterAutoloadFlow(resource_config=resource_config,
                                                vcenter_client=vcenter_client,
                                                logger=logger)

            return autoload_flow.discover()

    def Deploy(self, context, request, cancellation_context=None):
        """Called when reserving a sandbox during setup, a call for each app in the sandbox.

        Method creates the compute resource in the cloud provider - VM instance or container.
        If App deployment fails, return a "success false" action result.
        :param ResourceCommandContext context:
        :param str request: A JSON string with the list of requested deployment actions
        :param CancellationContext cancellation_context:
        :return:
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Deploy command...")
            logger.debug(f"Request: {request}")
            api = CloudShellSessionContext(context).get_api()
            resource_config = VCenterResourceConfig.from_context(context=context,
                                                                 api=api)

            cancellation_manager = CancellationContextManager(cancellation_context)
            reservation_info = ReservationInfo.from_resource_context(context)
            vcenter_client = VCenterAPIClient(host=resource_config.address,
                                              user=resource_config.user,
                                              password=resource_config.password,
                                              logger=logger)

            for deploy_app_cls in (deploy_app.VMFromVMDeployApp,
                                   deploy_app.VMFromTemplateDeployApp,
                                   deploy_app.VMFromLinkedCloneDeployApp,
                                   deploy_app.VMFromImageDeployApp):

                DeployVMRequestActions.register_deployment_path(deploy_app_cls)

            request_actions = DeployVMRequestActions.from_request(request=request, cs_api=api)

            deploy_flow = VCenterDeployVMfromVMFlow(resource_config=resource_config,
                                                    reservation_info=reservation_info,
                                                    vcenter_client=vcenter_client,
                                                    cs_api=api,
                                                    cancellation_manager=cancellation_manager,
                                                    logger=logger)

            return deploy_flow.deploy(request_actions=request_actions)

    def PowerOn(self, context, ports):
        """Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually by

        the sandbox end-user from the deployed App's commands pane. Method spins up the VM If the operation fails,
        method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power On command...")
            api = CloudShellSessionContext(context).get_api()

    def PowerOff(self, context, ports):
        """Called during sandbox's teardown can also be run manually by the sandbox end-user from the deployed

        App's commands pane. Method shuts down (or powers off) the VM instance. If the operation fails,
        method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Power Off command...")
            api = CloudShellSessionContext(context).get_api()

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        """Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually

        by the sandbox end-user from the deployed App's commands pane. Method retrieves the VM's updated IP address
        from the cloud provider and sets it on the deployed App resource. Both private and public IPs are retrieved,
        as appropriate. If the operation fails, method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Remote Refresh IP command...")
            api = CloudShellSessionContext(context).get_api()

    def GetVmDetails(self, context, requests, cancellation_context):
        """Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually

        by the sandbox end-user from the deployed App's VM Details pane. Method queries cloud provider for instance
        operating system, specifications and networking information and returns that as a json serialized driver
        response containing a list of VmDetailsData. If the operation fails, method should raise an exception.
        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Get VM Details command...")
            logger.debug(f"Requests: {requests}")
            api = CloudShellSessionContext(context).get_api()


    def ApplyConnectivityChanges(self, context, request):
        pass

    def disconnect_all(self, context, ports):
        pass

    def disconnect(self, context, ports, network_name):
        pass

    def SaveApp(self, context, request, cancellation_context=None):
        pass

    def DeleteSavedApps(self, context, request, cancellation_context=None):
        pass

    def remote_save_snapshot(self, context, ports, snapshot_name, save_memory):
        """
        Saves virtual machine to a snapshot
        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between the remote resource and the local resource
        :type ports: list[string]
        :param snapshot_name: snapshot name to save to
        :type snapshot_name: str
        :param save_memory: Snapshot the virtual machine's memory. Lookup, Yes / No
        :type save_memory: str
        :return:
        """
        pass

    def remote_restore_snapshot(self, context, ports, snapshot_name):
        """Restores virtual machine from a snapshot.

        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between the remote resource and the local resource
        :type ports: list[string]
        :param snapshot_name: Snapshot name to restore from
        :type snapshot_name: str
        :return:
        """
        pass

    def remote_get_snapshots(self, context, ports):
        """Returns list of snapshots.

        :param context: resource context of the vCenterShell
        :type context: models.QualiDriverModels.ResourceCommandContext
        :param ports:list[string] ports: the ports of the connection between the remote resource and the local resource
        :type ports: list[string]
        :return: list
        """
        pass

    def orchestration_save(self, context, ports, mode="shallow", custom_params=None):
        pass

    def orchestration_restore(self, context, ports, saved_details):
        pass

    def get_vm_uuid(self, context, vm_name):
        pass

    def DeleteInstance(self, context, ports):
        """Called during sandbox's teardown or when removing a deployed App from the sandbox

        Method deletes the VM from the cloud provider. If the operation fails, method should raise an exception.
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            logger.info("Starting Delete Instance command...")
            api = CloudShellSessionContext(context).get_api()

    def cleanup(self):
        """Destroy the driver session, this function is called every time a driver instance is destroyed

        This is a good place to close any open sessions, finish writing to log files, etc.
        """
        pass
