from datetime import datetime, date

def string_to_date(date_str):
    """
    Converts a date string in d/m/y format to a date object.

    :param date_str: str, date in d/m/y format (e.g., '25/12/23')
    :return: date object or None if input is invalid
    """
    if not date_str:
        print("Error: Input date is empty.")
        return None
    
    try:
        # Parse the string into a datetime object using the format %d/%m/%y
        datetime_obj = datetime.strptime(date_str, "%d/%m/%y")
        
        # Extract only the date part
        date_obj = datetime_obj.date()
        
        return date_obj
    except ValueError:
        print(f"Error: Invalid date format. Expected d/m/y. Got: {date_str}")
        return None

# Example usage
if __name__ == "__main__":
    date_input = "25/12/23"
    date_object = string_to_date(date_input)
    
    if date_object:
        print(f"Original String: {date_input}")
        print(f"Converted Date Object: {date_object}")  # Output as date object
    else:
        print("Conversion failed.")