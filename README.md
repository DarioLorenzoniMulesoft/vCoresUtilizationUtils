# MuleSoft vCore Usage Reporter

This Python script retrieves and displays vCore usage within a MuleSoft Anypoint Platform organization. It interacts with the Anypoint Platform's APIs to fetch deployment information, calculate vCore consumption, and present it in a user-friendly table format.

## Prerequisites

* Python 3.6 or higher
* Client ID and Client Secret with appropriate permissions for API access

## Installation

1.  Clone the repository:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the Python script:

    ```bash
    python utils.py
    ```

2.  Follow the interactive prompts:

    * Select the control plane (EU or US).
    * Enter your Client ID and Client Secret.
    * Select the target organization/sub-organization.
    * Select the target environments.
    * Choose whether to view detailed or summary data.

3.  The script will display a table in the console showing the vCore usage.


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bug fixes or feature requests.