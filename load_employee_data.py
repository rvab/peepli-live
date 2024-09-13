import pandas as pd

def load_employee_data():
    file_path= 'employee_masterdata.xlsx'
    df = pd.read_excel(file_path)
    return df

