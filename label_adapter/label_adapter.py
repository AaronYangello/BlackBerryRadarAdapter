from datetime import datetime
from pathlib import Path
import argparse
import logging

from blackberry import BlackBerryAPI
from helpers import Helpers

logger = logging.getLogger(__name__)

def main(helper, is_test):    
    # Get label str per asset from email csvs
    bb = BlackBerryAPI('label_adapter/key.pem', logger, is_test)
    new_label_map = {}
    if len(helper.csv_files) <= 0:
        logger.info(f'No CSV reports found in {helper.input_dir}')
        return
    label_bases_processed = set()
    for csv in helper.csv_files:
        helper.process_csv(csv, new_label_map, label_bases_processed)

    # Get current assets
    assets = bb.get_assets()

    for asset_id in assets: 
        asset_identifier = assets[asset_id]
        logger.info(f'Syncing labels for asset {asset_identifier}')
        cur_asset_labels = bb.get_asset_labels(asset_id)
        # Asset id from Blackberry system in report, so skip
        new_asset_labels = []
        if asset_identifier in new_label_map:
            new_asset_labels = new_label_map[asset_identifier]
        
        # Delete old labels
        num_labels_deleted = 0
        for cur_label in cur_asset_labels:
            cur_label_base = cur_label[:cur_label.rfind(' - ')]
            if cur_label_base in label_bases_processed and cur_label not in new_asset_labels:
                # remove it from asset
                num_labels_deleted += 1
                if not is_test:
                    bb.delete_label(asset_id, cur_asset_labels[cur_label])
        if is_test:
            logger.info(f'(TEST) {num_labels_deleted} label(s) would be deleted for asset {asset_identifier}')
        else: 
            logger.info(f'{num_labels_deleted} label(s) deleted for asset {asset_identifier}')
        
        # Add new labels
        num_labels_added = 0
        for new_label in new_asset_labels:
            if is_test and new_label not in cur_asset_labels:
                label_added = True
            else:
                label_added = bb.add_label(asset_id, new_label)
            if label_added: num_labels_added += 1
        
        if is_test:
            logger.info(f'(TEST) {num_labels_added} label(s) would be added for asset {asset_identifier}')
        else:
            logger.info(f'{num_labels_added} label(s) added for asset {asset_identifier}')
    
    #Archive the files
    helper.archive_csv_files(is_test)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pipe labels from Trimble CSV report to the BlackBerry Radar system.')
    parser.add_argument('report_directory', type=Path, help='Path to the directory to scan for CSV report files from Trimble.')
    parser.add_argument('report_archive_directory', type=Path, help='Path to the directory where CSV reports from Trimble should be moved after processing.')
    parser.add_argument('-l', '--log-level', choices=['info', 'debug', 'error'], default='info', help='Set the log level (default: info)')
    parser.add_argument('-t', '--test', action='store_true', help='Indicates whether this is a test run. Will read current assets and CSVs')
    args = parser.parse_args()

    is_test = args.test
    input_dir = args.report_directory.resolve()
    if is_test:
        max_dirs = 5
    else:
        max_dirs = 24
    helper = Helpers(input_dir, args.report_archive_directory.resolve(), logger, args.log_level, max_dirs)

    logger.info(f'--------------------------------------\nUpdating labels from CSVs in {str(input_dir)}. Files will be archived to {str(helper.archive_dir)}.')
    main(helper, is_test)