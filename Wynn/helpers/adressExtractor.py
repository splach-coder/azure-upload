def parse_address(cells):
    """
    Parse the address cells based on whether it's a 4 or 5-cell address format.
    Returns a JSON-like dictionary with parsed components.
    """
    address_data = {
        "company": None,
        "street": None,
        "city": None,
        "country": None
    }

    # Identify the last cell as the country
    address_data["country"] = cells[-1]

    # Check if we have 4 or 5 cells
    if len(cells) == 4:
        address_data["company"] = cells[0]
        address_data["street"] = cells[1]
        address_data["city"] = cells[2]
    elif len(cells) == 5:
        address_data["company"] = cells[0]
        address_data["street"] = cells[1] + " " + cells[2]
        address_data["city"] = cells[3]
    elif len(cells) == 6:
        address_data["company"] = cells[0]
        address_data["street"] = cells[1] + " " + cells[2] + " " + cells[3]
        address_data["city"] = cells[4]    
    
    return address_data

def find_address_data(sheet):
    """
    This function searches for '8 Geadresseerde' in the sheet, finds the cell 3 columns
    to the right, and then parses the address data starting from that cell.
    """
    # Search for "8 Geadresseerde" in the sheet
    for row in sheet.iter_rows(values_only=False):
        for cell in row:
            if cell.value == "8 Geadresseerde":
                # Find the cell three steps to the right
                target_cell = sheet.cell(row=cell.row, column=cell.column + 3)
                
                # Start extracting cells for address parsing
                address_cells = []
                for i in range(6):  # Capture up to 5 cells
                    current_cell = sheet.cell(row=target_cell.row + i, column=target_cell.column)
                    if current_cell.value:
                        address_cells.append(current_cell.value)
                
                # Determine if we have 4 or 5 cells and parse the address
                if len(address_cells) in [3, 4, 5, 6]:
                    return parse_address(address_cells)
                else:
                    raise ValueError("Unexpected number of cells for address parsing")

    # If "8 Geadresseerde" not found, return None or handle accordingly
    return None