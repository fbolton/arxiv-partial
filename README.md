# Partial oracles and Grover's algorithm

This repository provides a sample implementation of the algorithm described in _Beyond the black-box oracle: accelerated quantum search using partial oracles and Grover's algorithm_, which will be made available on [arxiv.org](https://arxiv.org).

## Set-up and installation

### Prerequisites

* Git must be installed, in order to clone the repository.
* Python 3.10 was used to test the code (Qiskit 1.0.x requires a minimum of Python 3.8).
* An account with IBM Cloud (a service instance and a service token are required in order for the code to access a remote IBM quantum backend).

>[!NOTE]
> [IBM Cloud](https://cloud.ibm.com/login) is now the recommended portal for accessing quantum backends from IBM. If you have an older account with [IBM Quantum](https://quantum.ibm.com/login), you would need to modify the code in `src/selector.py` to login to IBM Quantum instead.

### Procedure

After checking the prerequisites, you can set up your Python development environment as follows:

1. If you have not already done so, clone this repository to your local machine using Git. Open a command prompt and enter the following command:
   ```commandline
   git clone https://github.com/fbolton/arxiv-partial.git
   ```
2. At the command prompt, change directory to the newly cloned repo:
   ```commandline
   cd arxiv-partial
   ```
3. Make sure that your default `python3` command is actually at version 3.8 or later:
   ```commandline
   python3 --version
   ```
   If not, you either need to go back and install a later Python 3.x version or figure out how to switch Python versions on your OS.
4. Create a new virtual environment under the `arxiv-partial` directory:
   ```commandline
   python3 -m venv venv
   ```
5. Activate the virtual environment (all of the commands from this point should be entered in the virtual environment):
   ```commandline
   source ./venv/bin/activate
   ```
6. Use `pip` to install the packages from the `requirements.txt` file:
   ```commandline
   pip install -r requirements.txt
   ```

## Running the algorithm

You have a choice between running the code locally or remotely (on IBM Cloud).

### Run the algorithm on a local backend

Assuming you have already followed the steps to set up and install your development environment, you can run the algorithm locally, as follows:

1. If you have not done so already, activate your virtual environment (all of the commands from this point should be entered in the virtual environment):
   ```commandline
   source ./venv/bin/activate
   ```
2. To configure the backend selector (`src/selector.py`), set the following environment variables in your shell:
   ```commandline
   export SUSD_BACKEND="local_qiskit"
   export SUSD_DEVICE="basic_simulator"
   ```
3. Run the mainline:
   ```commandline
   python3 src/main.py
   ```

### Run the algorithm on IBM Cloud

Assuming you have already followed the steps to set up and install your development environment, you can run the algorithm remotely on IBM Cloud, as follows:

1. If you have not done so already, activate your virtual environment (all of the commands from this point should be entered in the virtual environment):
   ```commandline
   source ./venv/bin/activate
   ```
2. Obtain your service instance name on IBM Cloud. Go to your list of [IBM quantum service instances](https://cloud.ibm.com/quantum/instances), click through to the instance you want to use, and from the **Overview** tab, copy the Cloud Resource Name (CRN), which we refer to here as `<YOUR_SERVICE_INSTANCE>`.
3. Obtain the API key for your service instance, which we refer to here as `<YOUR_SERVICE_TOKEN>`. If you already have an API Key for the service instance, you can reuse that existing key. Otherwise. go to the [API Keys](https://cloud.ibm.com/iam/apikeys) page and create a new API key.
3. To configure the backend selector (`src/selector.py`), set the following environment variables in your shell:
   ```commandline
   export SUSD_BACKEND="ibm_cloud"
   export SUSD_DEVICE="simulator_mps"
   export SUSD_IBM_SVC_INSTANCE="<YOUR_SERVICE_INSTANCE>"
   export SUSD_IBM_SVC_TOKEN="<YOUR_SERVICE_TOKEN>"
   ```
4. Run the mainline:
   ```commandline
   python3 src/main.py
   ```
