from datetime import datetime


def change_date_format(date_str):
    # Convert from dd.mm.yyyy to dd/mm/yyyy
    try:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return date_str