![Image][1]

# **VMware vCenter Cloud Provider Shell 2G**

Release date: November 2020

`Shell version: 1.0.0`

`Document version: 1.0`

# In This Guide

* [Overview](#overview)
* [Downloading the Shell](#downloading-the-shell)
* [Importing and Configuring the Shell](#importing-and-configuring-the-shell)
* [Updating Python Dependencies for Shells](#updating-python-dependencies-for-shells)
* [Typical Workflows](#typical-workflows)
* [References](#references)
* [Release Notes](#release-notes)


# Overview
A shell integrates a device model, application or other technology with CloudShell. A shell consists of a data model that defines how the device and its properties are modeled in CloudShell, along with automation that enables interaction with the device via CloudShell.

### Cloud Provider Shells
CloudShell Cloud Providers shells provide L2 or L3 connectivity between resources and/or Apps.

### VMware vCenter Cloud Provider Shell 2G
VMware vCenter Cloud Provider Shell 2G provides you with apps deployment and management capabilities. 

For more information on the device, see the vendor's official product documentation.

### Standard version
VMware vCenter Cloud Provider Shell 2G is based on the Cloud Provider Standard version **1.0.0**.

For detailed information about the shell’s structure and attributes, see the [Cloud Provider Standard](https://github.com/QualiSystems/cloudshell-standards/blob/master/Documentation/cloud_provider_standard.md) in GitHub.

### Requirements

Release: VMware vCenter Cloud Provider Shell 2G

▪ CloudShell version **9.3 and above**

**Note:** If your CloudShell version does not support this shell, you should consider upgrading to a later version of CloudShell or contact customer support. 

### Data Model

The shell's data model includes all shell metadata, families, and attributes.

#### **VMware vCenter Cloud Provider Shell 2G Attributes**

The attribute names and types are listed in the following section of the Cloud Provider Shell Standard:

[Common Cloud Provider Attributes](https://github.com/QualiSystems/cloudshell-standards/blob/master/Documentation/cloud_provider_standard.md#attributes)

The following table describes attributes that are unique to this shell and are not documented in the Shell Standard: 


|Attribute Name|Data Type|Description|
|:---|:---|:---|
|User|String||
|Password|Password||
|Default dvSwitch|String|The default vCenter dvSwitch that will be used when configuring VM connectivity. Should be under the Default Datacenter|
|Holding Network|String|The default network that will be configured when disconnecting from another network. Should be under the Default Datacenter|
|VM Cluster|String|The vCenter cluster or host that will be used when deploying a VM. Should be under the Default Datacenter|
|VM Resource Pool|String|The vCenter Resource Pool in which the VM will be created. Should be under the defined VM Cluster (optional)|
|VM Storage|String|The vCenter storage in which the VMs will be created. The storage can be either a datastore or a datastore cluster. For example: datastore1 (To use a specific datastore inside a cluster, specify the cluster name and the datastore name. For example: clustername/datastore1)|
|Saved Sandbox Storage|String|The vCenter storage in which the content of saved sandboxes will be created. The storage can be either a datastore or a datastore cluster. For example: datastore1  or clustername/datastore1 (for datastore inside a cluster)|
|Behavior during save|String|Determines the VM behavior when the sandbox is saved. If Power off is selected, and the VM was powered on before the save, then the VM will shut down for the duration of the save, and then be powered on at the end|
|VM Location|String|The full path to the folder within vCenter in which the VM will be created. (e.g vms/quali)|
|Shutdown Method|String|The shutdown method that will be used when powering off the VM. Possible options are 'Hard' and 'Soft' shutdown|
|OVF Tool Path|String|The path for the OVF tool installation. Use the same path for all execution servers|
|Reserved Networks|String|Reserved networks separated by Semicolon(;), vNICs configured to those networks won't be used for VM connectivity|
|Promiscuous Mode|Boolean|If enabled the port groups on the virtual switch will be configured to allow promiscuous mode|

### Automation
This section describes the automation (driver) associated with the data model. The shell’s driver is provided as part of the shell package. There are two types of automation processes, Autoload and Resource. Autoload is executed when creating the resource in the **Inventory** dashboard.

For detailed information on each available commands, see the following section of the Cloud Provider Standard:

[Common Cloud Provider Commands](https://github.com/QualiSystems/cloudshell-standards/blob/master/Documentation/cloud_provider_standard.md#commands)


# Downloading the Shell
The VMware vCenter Cloud Provider Shell 2G shell is available from the [Quali Community Integrations](https://community.quali.com/integrations) page. 

Download the files into a temporary location on your local machine. 

The shell comprises:

|File name|Description|
|:---|:---|
|VMware vCenter Cloud Provider Shell 2G.zip|Device shell package|
|cloudshell-vcenter-dependencies-package-1.0.x.zip|Shell Python dependencies (for offline deployments only)|

# Importing and Configuring the Shell
This section describes how to import the VMware vCenter Cloud Provider Shell 2G shell and configure and modify the shell’s devices.

### Importing the shell into CloudShell

**To import the shell into CloudShell:**
  1. Make sure you have the shell’s zip package. If not, download the shell from the [Quali Community's Integrations](https://community.quali.com/integrations) page.
  
  2. In CloudShell Portal, as Global administrator, open the **Manage – Shells** page.
  
  3. Click **Import**.
  
  4. In the dialog box, navigate to the shell's zip package, select it and click **Open**. <br><br>The shell is displayed in the **Shells** page and can be used by domain administrators in all CloudShell domains to create new inventory resources, as explained in [Adding Inventory Resources](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/INVN/Add-Rsrc-Tmplt.htm?Highlight=adding%20inventory%20resources). 

### Offline installation of a shell

**Note:** Offline installation instructions are relevant only if CloudShell Execution Server has no access to PyPi. You can skip this section if your execution server has access to PyPi. For additional information, see the online help topic on offline dependencies.

In offline mode, import the shell into CloudShell and place any dependencies in the appropriate dependencies folder. The dependencies folder may differ, depending on the CloudShell version you are using:

* For CloudShell version 8.3 and above, see [Adding Shell and script packages to the local PyPi Server repository](#adding-shell-and-script-packages-to-the-local-pypi-server-repository).

* For CloudShell version 8.2, perform the appropriate procedure: [Adding Shell and script packages to the local PyPi Server repository](#adding-shell-and-script-packages-to-the-local-pypi-server-repository) or [Setting the Python pythonOfflineRepositoryPath configuration key](#setting-the-python-pythonofflinerepositorypath-configuration-key).

* For CloudShell versions prior to 8.2, see [Setting the Python pythonOfflineRepositoryPath configuration key](#setting-the-python-pythonofflinerepositorypath-configuration-key).

### Adding shell and script packages to the local PyPi Server repository
If your Quali Server and/or execution servers work offline, you will need to copy all required Python packages, including the out-of-the-box ones, to the PyPi Server's repository on the Quali Server computer (by default *C:\Program Files (x86)\QualiSystems\CloudShell\Server\Config\Pypi Server Repository*).

For more information, see [Configuring CloudShell to Execute Python Commands in Offline Mode](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=Configuring%20CloudShell%20to%20Execute%20Python%20Commands%20in%20Offline%20Mode).

**To add Python packages to the local PyPi Server repository:**
  1. If you haven't created and configured the local PyPi Server repository to work with the execution server, perform the steps in [Add Python packages to the local PyPi Server repository (offline mode)](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=offline%20dependencies#Add). 
  
  2. For each shell or script you add into CloudShell, do one of the following (from an online computer):
      * Connect to the Internet and download each dependency specified in the *requirements.txt* file with the following command: 
`pip download -r requirements.txt`. 
     The shell or script's requirements are downloaded as zip files.

      * In the [Quali Community's Integrations](https://community.quali.com/integrations) page, locate the shell and click the shell's **Download** link. In the page that is displayed, from the Downloads area, extract the dependencies package zip file.

3. Place these zip files in the local PyPi Server repository.
 
### Configuring a new resource
This section explains how to create a new resource from the shell.

In CloudShell, the component that models the device is called a resource. It is based on the shell that models the device and allows the CloudShell user and API to remotely control the device from CloudShell.

You can also modify existing resources, see [Managing Resources in the Inventory](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/INVN/Mng-Rsrc-in-Invnt.htm?Highlight=managing%20resources).

**To create a resource for the device:**  
  1. In the CloudShell Portal, in the **Inventory** dashboard, click **Add New**.
     ![Image][2]
     
  3. From the list, select **VMware vCenter Cloud Provider Shell 2G**.
  
  4. Click **Create**.
  
  5. In the **Resource** dialog box, enter the following attributes with data from step 1:
        - **User** - Paste here your vCenter User
        - **Password** - Paste here your vCenter User Password
        - **Default Datacenter** - Paste here default Datacenter
        - **Default dvSwitch** - Paste here default dvSwitch which will be used for the connectivity
        - **Holding Network** - Paste here default network that will be configured when disconnecting from another network
        - **VM Cluster** - Paste here vCenter cluster or host that will be used when deploying a VM
        - **VM Storage** - Paste here vCenter storage in which the VMs will be created
        - **VM Location** - Paste here the full path to the folder within vCenter in which the VM will be created
  
  6. Click **Continue**.

CloudShell validates provided settings and creates the new resource.

_**VMware vCenter Cloud Provider Shell 2G requires you to create an appropriate App template, which would be deployed as part of the sandbox reservation. For details, see the following CloudShell Help article: [Applications' Typical Workflow](https://help.quali.com/Online%20Help/0.0/Portal/Content/CSP/MNG/Mng-Apps.htm?Highlight=App#Adding)**_

# Updating Python Dependencies for Shells
This section explains how to update your Python dependencies folder. This is required when you upgrade a shell that uses new/updated dependencies. It applies to both online and offline dependencies.
### Updating offline Python dependencies
**To update offline Python dependencies:**
1. Download the latest Python dependencies package zip file locally.

2. Extract the zip file to the suitable offline package folder(s). 

3. Terminate the shell’s instance, as explained [here](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Exctn-Srv-Exct.htm#Terminat). 

### Updating online Python dependencies
In online mode, the execution server automatically downloads and extracts the appropriate dependencies file to the online Python dependencies repository every time a new instance of the driver or script is created.

**To update online Python dependencies:**
* If there is a live instance of the shell's driver or script, terminate the shell’s instance, as explained [here](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Exctn-Srv-Exct.htm#Terminat). If an instance does not exist, the execution server will download the Python dependencies the next time a command of the driver or script runs.

# Typical Workflows

**Workflow 1 - _Create App Template_** 
1. Log into CloudShell Portal as administrator.

2. Click __Manage > Apps__ and add a new App template.

3. Select the appropriate deployment type.<br><br>Note that this shell's deployment types all end with "2G" to indicate that they belong to a 2nd Gen shell. For example: "vCenter VM From Template 2G".

4. Sepecify a __Name__ and click __Create__.

6. In the __General__ tab, select the appropriate domain categories.<br><br>A domain category is a service category that is used to expose the App to specific CloudShell domains. By default, the __Applications__ category is associated to the Global domain. You can optionally create additional service categories for other domains or add the desired domains to the __Applications__ category. Service categories are managed in the __Manage>Categories>Service Categories__ page.

7. Configure the App's __Deployment Path__ - select the cloud provider resource and fill in the settings.

8. In the __Configuration Management__ tab, specify the configuration management script or Ansible playbook to run on the VM.

9. In the __App Resource__ tab, optionally select the shell that defines the deployed App's behavior in CloudShell (e.g. which automation commands it includes). <br><br>You can also specify the deployed App's __Username__ and __Password__. CloudShell will set these credentials during the VM's deployment.

10. You can add additional deployment paths by clicking the link in the bottom left corner of the dialog box.

11. Click __Done__.

# References
To download and share integrations, see [Quali Community's Integrations](https://community.quali.com/integrations). 

For instructional training and documentation, see [Quali University](https://www.quali.com/university/).

To suggest an idea for the product, see [Quali's Idea box](https://community.quali.com/ideabox). 

To connect with Quali users and experts from around the world, ask questions and discuss issues, see [Quali's Community forums](https://community.quali.com/forums). 

# Release Notes 

### What's New

For release updates, see the shell's [GitHub releases page](https://github.com/QualiSystems/VMware-vCenter-Cloud-Provider-Shell-2G/releases).


[1]: https://github.com/QualiSystems/cloudshell-shells-documentaion-templates/blob/master/cloudshell_logo.png
[2]: https://github.com/QualiSystems/cloudshell-shells-documentaion-templates/blob/master/create_a_resource_device.png
