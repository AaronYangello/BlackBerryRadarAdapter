**Label Adapter for Trimble CSV Reports and BlackBerry Radar System**
====================================================================

**Overview**
------------

Fleet Management System Integration Adapter, integrating a Trimble truck fleet maintenance management tool with BlackBerry Radar’s asset location tracking, to automate report processing and sync asset maintenance schedules across platforms.

**Installation**
---------------

To use this project, you'll need to have Python installed on your system. You can install the required dependencies using pip:

```bash
pip install requirements.txt
```

**Usage**
-----

To run the script, navigate to the project directory and execute the following command:

```bash
python label_adapter.py [-h] [-w WHITE_LIST_FILE] [-k API_KEY_FILE] [-l {info,debug,error}] [-t {full,read_only,not_test}] report_directory report_archive_directory
```

positional arguments:  
*  report_directory &emsp;&emsp;&emsp;&emsp; Path to the directory to scan for CSV report files from Trimble.  
*  report_archive_directory &ensp; Path to the directory where CSV reports from Trimble should be moved after processing.  
  
options:  
*  -h, --help &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp; Show this help message and exit  
*  -w,  --white-list-file WHITE_LIST_FILE &emsp;&ensp;&nbsp; Path to the file with a list of component codes to look for.  
*  -k, --api-key-file API_KEY_FILE &emsp;&emsp;&emsp;&emsp;&ensp; Path to the Blackberry Api key file.  
*  -l, --log-level {info,debug,error} &emsp;&emsp;&emsp;&ensp;&nbsp; Set the log level (default: info)  
*  -t, --test-level {full, read_only, not_test} &ensp; Indicates what kind of test will be run, if any. not_test will perform real read and write to BlackBerry servers; read_only will simulate just writing; and full will simulate both read and write.

**Example Usage**
----------------

```bash
python label_adapter.py /path/to/reports /path/to/archive -l debug -t
```

## Example Offline Test

- Create output directory: `mkdir -p tests/output`
- Run label adapter from root directory with -t option:  
   ```bash
   python label_adapter/label_adapter.py tests/input tests/output -t
   ```
- Examine output in tests/output/app.log

**Configuration**
----------------

The script uses the following configuration:

*   `key.pem`: The path to the private key file used for authentication with the BlackBerry Radar system. This file should be placed in the `label_adapter` directory.
*   `label_adapter/component_code_whitelist.txt`: A file containing a list of allowed component codes. One code per line.

**Logging**
---------

The script uses the Python `logging` module to log events. The log level can be set using the `-l` command-line option. Log files are written to the archive directory.

**BlackBerry Radar API**
----------------------

The script uses the BlackBerry Radar API to interact with the BlackBerry Radar system. The API endpoints and authentication mechanism are implemented in the `blackberry.py` module.

**Helpers**
------------

The `helpers.py` module provides utility functions for working with the CSV reports and the BlackBerry Radar system. These functions include:

*   `get_csv_files`: Retrieves a list of CSV files from a specified directory.
*   `process_csv`: Processes a single CSV file and extracts the labels.
*   `archive_csv_files`: Archives the CSV files to a specified directory.

**License**
-------

This project is licensed under the MIT License. See the `LICENSE` file for details.
