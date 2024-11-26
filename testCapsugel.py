import json

inv_keyword_params = {"Country of Origin: " : ((25, 0), 5), "Commodity Code of country of dispatch:" : ((100, 0), 0), "Batches:" : ((100, 0), 0),  "Net Weight:" : ((100, 0), 0), "Total for the line item" : ((150, 10), 350), "Total freight related surcharges for the item:" : ((150, 0), 300), "All in Price" : ((120, 0), 150), "DN Nbr:" : ((40, 0), 5)}
extracted_data = """[
    {
        "Country of Origin: ": "Belgium",
        "Commodity Code of country of dispatch:": "96020000",
        "Batches:": "3664095",
        "Net Weight:": "1.579,872  KG",
        "Total for the line item": "43.379,84 USD",
        "All in Price": "16.457,000",
        "DN Nbr:": "73064698"
    },
    {
        "Batches:": "3663997",
        "DN Nbr:": "73064699"
    },
    {
        "Country of Origin: ": "Belgium",
        "Commodity Code of country of dispatch:": "96020000",
        "Batches:": "3665962",
        "Net Weight:": "67,200  KG",
        "Total for the line item": "1.834,00 USD",
        "All in Price": "700,000",
        "DN Nbr:": "73066653"
    },
    {
        "Country of Origin: ": "Belgium",
        "Commodity Code of country of dispatch:": "96020000",
        "Batches:": "3665963",
        "Net Weight:": "289,256  KG",
        "Total for the line item": "9.971,72 USD",
        "All in Price": "3.806,000",
        "DN Nbr:": "73071795"
    },
    {
        "Net Weight:": "161,040  KG",
        "Total for the line item": "8.851,30 USD",
        "All in Price": "3.355,000"
    },
    {
        "Country of Origin: ": "Belgium",
        "Commodity Code of country of dispatch:": "96020000"
    }
]"""

def merge_incomplete_records_invoice(extracted_data, keyword_params):
    """
    Merges incomplete records with the next record that has the missing data.

    Parameters:
        extracted_data (list): The list of extracted JSON data.
        keyword_params (dict): The keyword parameters to check completeness against.
        
    Returns:
        list: The corrected and merged data.
    """

    extracted_data = json.loads(extracted_data)

    # Iterate through the list of extracted records
    merged_results = []
    incomplete_record = None

    # Loop through all extracted records
    for record in extracted_data:
        # Check if the record is incomplete
        is_record_missing = len(record) < len(keyword_params)

        if is_record_missing:
            if incomplete_record is None:
                # Store the incomplete record for future merging
                incomplete_record = record
            else:
                # Merge with the next incomplete record
                incomplete_record.update(record)
                merged_results.append(incomplete_record)
                incomplete_record = None  # Reset for the next potential merge
        else:
            # Add the complete record directly to results
            merged_results.append(record)    

    # Handle any remaining incomplete record if at the end
    if incomplete_record is not None:
        merged_results.append(incomplete_record)

    return merged_results

print(json.dumps(merge_incomplete_records_invoice(extracted_data, inv_keyword_params), indent=4))