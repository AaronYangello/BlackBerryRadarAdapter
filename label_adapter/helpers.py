from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from logging import Logger
from pathlib import Path
import logging
import shutil
import glob
import csv
import os
import re

class Helpers:
    def __init__(self, input_dir:Path, output_dir:Path, logger:Logger, log_level_str:str, max_directories:int):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.archive_dir = self.create_archive_dir()
        self.logger = logger
        self.configure_logger(log_level_str)
        self.csv_files = self.get_csv_files(input_dir)
        self.delete_oldest_directory(max_directories)

    def get_csv_files(self, input_dir:Path) -> list:
        self.logger.debug(f'Retrieving CSVs from {str(input_dir)}')
        if not input_dir.is_dir():
            self.logger.error(f"{str(input_dir)} is not a valid directory.")
            exit(1)
        try:
            csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
            self.logger.debug(f'{len(csv_files)} CSV files found')
            return csv_files 
        except PermissionError:
            self.logger.error(f"Permission denied for directory: {input_dir}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
        
    def create_archive_dir(self)->Path:
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_dir = self.output_dir / f"{current_datetime}_csv_reports"
        archive_dir.mkdir(parents=True, exist_ok=True)
        return archive_dir
        
    def archive_csv_files(self, is_test:bool) -> None: 
        self.logger.debug(f'Moving {len(self.csv_files)} CSVs to archive folder {self.archive_dir}')
        try:
            for file in self.csv_files:
                if is_test:
                    shutil.copy(file, self.archive_dir)
                else:
                    shutil.move(file, self.archive_dir)
        except Exception as e:
            self.logger.error(f"Archiving error: {e}")

    def process_csv(self,pathToCsv:str, assetLabelMap: dict, label_bases_processed:set) -> None:
        self.logger.debug(f'Processing {pathToCsv}')
        label = ''
        with open('label_adapter/component_code_whitelist.txt') as file:
            comp_code_whitelist = [line.rstrip().lower() for line in file]
            self.logger.debug(f'Label whitelist {comp_code_whitelist}')
        with open(pathToCsv, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                assetId = row['UNITNUMBER']
                #label = f"{row['DESCRIPTION']} - {determine_severity(row['DUEPERCENT'])}"
                label_base = row['DESCRIPTION']
                due_percent = row['DUEPERCENT']
                comp_code = row['COMPCODE']
                if assetId:
                    if comp_code in comp_code_whitelist:
                        if assetId not in assetLabelMap:
                            assetLabelMap[assetId] = set()
                        full_label = f'{label_base} - {due_percent}'
                        label_bases_processed.add(label_base)
                        self.logger.debug(f'Adding asset {assetId} and label {full_label} to map')
                        assetLabelMap[assetId].add(full_label)
                    else:
                        self.logger.debug(f'Label {label} not in whitelist. Skipping...')
                
    def determine_severity(self, due_percent:str) -> str:
        LOW_THRESH = 110
        MED_THRESH = 180
        self.logger.debug('Determining Severity')
        severity = ''
        if due_percent:
            due_percent_float = float(due_percent.strip('%'))
            if due_percent_float <= LOW_THRESH:
                severity = "LOW"
            elif due_percent_float > LOW_THRESH and due_percent_float <= MED_THRESH:
                severity = "MEDIUM"
            else:
                severity = "HIGH"
        
        self.logger.debug(f'Severity for due percentage {due_percent} was determined to be {severity}')
        return severity

    def configure_logger(self, log_level_str: str) -> None:

        LOG_LEVEL_MAP = {
            'info': logging.INFO,
            'debug': logging.DEBUG,
            'error': logging.ERROR
        }
        new_log_level = LOG_LEVEL_MAP[log_level_str]

        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler = RotatingFileHandler(
            f'{self.archive_dir}/app.log',
            mode='a',
            maxBytes=1000000,
            backupCount=10,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        if new_log_level != self.logger.getEffectiveLevel():
            self.logger.setLevel(new_log_level)
            file_handler.setLevel(new_log_level)

    def extract_timestamp(self, dir_name: str) -> datetime:
        """Extracts the timestamp part from the directory name."""
        # Regular expression to match the default asctime format
        # Adjust if your asctime format is different
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_csv_reports', dir_name)
        if timestamp_match:
            return datetime.strptime(timestamp_match.group(1), '%Y-%m-%d_%H-%M-%S')
        else:
            # Handle the case where the timestamp is not found
            # This could raise an exception or return a specific value indicating failure
            self.logger.warning(f"Warning: Could not extract timestamp from '{dir_name}'")
            return None

    def delete_oldest_directory(self, max_directories:int):
        """Deletes the oldest directory in the specified path if the number of directories exceeds max_directories."""
        try:
            # List all directories in the path
            directories = [name for name in os.listdir(self.output_dir) if os.path.isdir(os.path.join(self.output_dir, name))]
            
            if len(directories) > max_directories:
                # Extract timestamps and store with directory names
                dir_timestamps = {dir_name: self.extract_timestamp(dir_name) for dir_name in directories}
                
                # Filter out directories without a successfully extracted timestamp
                dir_timestamps = {dir_name: ts for dir_name, ts in dir_timestamps.items() if ts is not None}
                
                if dir_timestamps:
                    # Find the oldest directory
                    oldest_dir = min(dir_timestamps, key=dir_timestamps.get)
                    
                    # **FORCE DELETE** the oldest directory (even if not empty)
                    oldest_dir_path = os.path.join(self.output_dir, oldest_dir)
                    try:
                        shutil.rmtree(oldest_dir_path)  # FORCE DELETE (DANGER: Permanent deletion)
                        self.logger.info(f"**FORCED DELETED**: {oldest_dir_path}")
                    except OSError as e:
                        self.logger.error(f"Error forcing deletion of {oldest_dir_path}: {e.strerror}")
                else:
                    self.logger.info("No directories with parseable timestamps found.")
            else:
                self.logger.debug("Number of directories does not exceed the limit.")
        except FileNotFoundError:
            self.logger.error(f"The specified path '{self.output_dir}' does not exist.")
