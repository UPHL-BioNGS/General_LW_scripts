import pandas as pd
import logging

def find_header_line(file_path, header_signal):
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file):
            if header_signal in line.lower():
                logging.debug(f"The line number in {file_path} was {line_number}")
                return line_number
    raise ValueError("Header line not found in file")

def read_miseq_sample_sheet(sample_sheet, header_signal):
    # Find the number of lines to skip because it's sometimes variable
    lines_to_skip = find_header_line(sample_sheet, header_signal)

    # Read the CSV file into a DataFrame, skipping the appropriate number of lines
    df = pd.read_csv(sample_sheet, skiprows=lines_to_skip)
    return df
