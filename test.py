import openpyxl

def search_excel(file_path, search_value):
    # Load the Excel workbook
    workbook = openpyxl.load_workbook(file_path)
    
    # Select the first sheet (or specify the sheet by name)
    sheet = workbook.active
    
    # Iterate through column A to find the matching value
    for row in sheet.iter_rows(min_row=1, max_col=3, values_only=True):
        col_a_value, col_b_value, col_c_value  = row
        
        # If a match is found in column A, return the corresponding value in column B
        if col_a_value == search_value:
            return col_c_value
    
    # If no match is found, return a message
    return "Value not found"

# Example usage
file_path = "./msc/files/ports_countries_updated.xlsx"
search_value = "MUNDRA"
result = search_excel(file_path, search_value)
print(result)
