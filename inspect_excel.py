
import pandas as pd
import glob
import os
import sys

# Force utf-8 for stdout if possible, or use replacement
sys.stdout.reconfigure(encoding='utf-8')

# Find file matching pattern
files = glob.glob("RAPPORT HEBDOMADAIRE*2026.xlsx")

if not files:
    print("No file found matching pattern")
else:
    file_path = files[0]
    print(f"Found file: {file_path}")
    
    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        print(f"Sheet names (raw): {sheet_names}")
        
        for sheet in sheet_names:
            print(f"\n--- Sheet: {sheet} ---")
            try:
                df = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=20)
                # Print parsed to string to avoid console encoding issues if possible
                print(df.head(10).to_string().encode('ascii', 'replace').decode('ascii'))
            except Exception as e:
                print(f"Error reading sheet {sheet}: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
