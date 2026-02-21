import pandas as pd

def get_tabs(doc_id):
    # Google Sheets allows exporting the entire workbook as excel 
    url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
    try:
        # read_excel with sheet_name=None reads all sheets into a dictionary
        xls = pd.read_excel(url, sheet_name=None)
        tabs = list(xls.keys())
        print("Excel Tabs:", tabs)
        print("Data in first tab:")
        print(xls[tabs[0]].head())
    except Exception as e:
        print("Error:", e)

get_tabs("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
