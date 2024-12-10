BlackBerryRadarAdapter
========================

Fleet Management System Integration Adapter, integrating a Trimble truck fleet maintenance management tool with BlackBerry Radar’s asset location tracking, to automate report processing and sync asset maintenance schedules across platforms.

## Set up

Run `make init`

## Usage

<blockquote>
usage: label_adapter.py [-h] [-l {info,debug,error}] [-t] report_directory report_archive_directory 
Pipe labels from Trimble CSV report to the BlackBerry Radar system.  
  
positional arguments:  
  report_directory      Path to the directory to scan for CSV report files from Trimble.  
  report_archive_directory  
                        Path to the directory where CSV reports from Trimble should be moved after processing.  
  
options:  
  -h, --help            show this help message and exit  
  -l {info,debug,error}, --log-level {info,debug,error}  
                        Set the log level (default: info)  
  -t, --test            Indicates whether this is a test run. Will read current assets and CSVs
</blockquote>

## Example Offline Test

- Create output directory: `mkdir -p tests/output`
- Run label adapter from root directory with -t option:  
`python label_adapter/label_adapter.py tests/input tests/output -t`
- Examine output in tests/output/app.log
