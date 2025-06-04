import datetime
import logging
from bs4 import BeautifulSoup

from global_db.countries.functions import get_abbreviation_by_country


def merge_invoice_outputs(invoice_outputs):
    if not invoice_outputs:
        return {}

    # Take header and footer base from first invoice
    merged_output = {
        "header": invoice_outputs[0]["header"],
        "customs_no": invoice_outputs[0]["customs_no"],
        "items": [],
        "footer": {
            "incoterm": None,
            "currency": None,
            "total": 0.0,
            "transport": 0.0
        }
    }

    total_sum = 0.0
    transport_sum = 0.0
    currency_set = set()

    for i, invoice in enumerate(invoice_outputs):
        # Merge items
        merged_output["items"].extend(invoice.get("items", []))

        # Get footer info
        footer = invoice.get("footer", {})
        total = footer.get("total", 0)
        transport = footer.get("transport", 0)
        currency = footer.get("currency")

        if i == 0:
            merged_output["footer"]["incoterm"] = footer.get("incoterm")
            merged_output["footer"]["currency"] = currency

        if total:
            try:
                total_sum += float(total)
            except:
                pass
            
        if transport:
            try:
                transport_sum += float(transport)
            except:
                pass

        if currency:
            currency_set.add(currency)

    merged_output["footer"]["total"] = round(total_sum, 2)
    merged_output["footer"]["transport"] = round(transport_sum, 2)

    return merged_output

def safe_float_conversion(value):
    try:
        return float(value)
    except ValueError:
        return 0

def safe_int_conversion(value):
    try:
        return int(value)
    except ValueError:
        return 0
    
def clean_invoice_items(combined_result):
    cleaned_items = []
    TotalNetWeight = 0
    TotalSurface = 0
    TotalQuantity = 0
    
    headerdata = combined_result.get("header", [])
    date = headerdata.get("date", [])
    
    # change the invoice date to date format
    if date:
            formats = ["%d.%m.%Y", "%d/%m/%Y"]  # Supported date formats
            for date_format in formats:
                try:
                    date = datetime.datetime.strptime(date, date_format).date()
                except ValueError:
                    logging.error(f"Invalid date format: {date}")

    for item in combined_result.get("items", []):
        try:
            TotalNetWeight += safe_float_conversion(item.get("net_weight", "0").replace("KG", "").strip())
            TotalSurface += safe_float_conversion(item.get("surface", "0").replace("M2", "").strip())   
            TotalQuantity += safe_int_conversion(safe_float_conversion(item.get("quantity", "0").strip()))
            
            cleaned_item = {
                "product_code": item.get("product_code", "").strip(),
                "product_name": item.get("product_name", "").strip(),
                "order_number": item.get("order_number", "").strip(),
                "reference": item.get("reference", "").strip(),
                "customs_tariff": item.get("customs_tariff", "").strip(),
                "origin": get_abbreviation_by_country(item.get("origin", "").strip()),

                # Strip and convert
                "net_weight": safe_float_conversion(item.get("net_weight", "0").replace("KG", "").strip()),
                "surface": safe_float_conversion(item.get("surface", "0").replace("M2", "").strip()),
                "quantity": safe_int_conversion(safe_float_conversion(item.get("quantity", "0").strip())),
                "unit": item.get("unit", "").strip(),

                "unit_price": safe_float_conversion(item.get("unit_price", "0").replace("EUR", "").strip()),
                "amount": safe_float_conversion(item.get("amount", "0").replace("EUR", "").replace(",", "").strip()),
                
                "document_number": item.get("document_number", "").strip(),
                "date": date,
            }

            cleaned_items.append(cleaned_item)

        except Exception as e:
            logging.error(f"Error processing item {item}: {e}")

    # Replace items with cleaned version
    combined_result["items"] = cleaned_items
    return [combined_result, TotalNetWeight, TotalSurface, TotalQuantity]

def extract_email_body(html_content):
    """
    Extracts the visible body text from an Outlook HTML email.
    
    Args:
        html_content (str): The raw HTML content of the email.
    
    Returns:
        str: Cleaned plain-text body of the email.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Optionally: remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Find the <body> tag content if it exists
    body = soup.find("body")
    text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Clean extra spaces and lines
    clean_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

    return clean_text
    