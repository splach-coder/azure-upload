import json

def process_container_data(data_json):

    json_response = []

    for data in data_json :
        # Initialize totals
        total_gross_weight = 0.0
        total_net_weight = 0.0
        total_packages = 0.0

        newItems = []

        # Process items and calculate totals
        items = data.get("items", [])
        for item in items:
            total_gross_weight += float(item.get("Gross Weight", 0))
            total_net_weight += float(item.get("Net Weight", 0))
            total_packages += int(item.get("Packages", 0))

        for item in items:
            item_number = ''.join([i for i in str(item.get("item", "")) if i.isdigit()]).zfill(4)  # Use .get() for safety
            packages = int(item.get("Packages", 0))
            description = item.get("Description", "")  # Use .get() to avoid KeyError
            gross_weight = float(item.get("Gross Weight", 0))
            net_weight = float(item.get("Net Weight", 0))

            item_data = {
                "ArrivalNotice1": f"1{data['Stay']}{data['LoydsNumber']}*{str(data['Article']).zfill(4)}",
                "ArrivalNotice2": f"maersk*{item_number}*{data['BL number']}",
                "Container": data["container"],
                "Packages": packages,
                "Description": description,
                "Gross Weight": gross_weight,
                "Net Weight": net_weight
            }

            # Construct transformed data for each item in each container
            newItems.append(item_data)

        Quay = ""

        if data["Quay"] == 1742: 
            Quay = "BEANRAZ03318002"
        if data["Quay"] == 1700: 
            Quay = "BEANRAZ03318002"
        if data["Quay"] == 913: 
            Quay = "BEANRAZ03318002"     

        # Reconstruct the processed entry
        processed_entry = {
            "container": data["container"],
            "vissel": data["vissel"],
            "dispatch_country": data["dispatch_country"].strip().upper(),
            "Quay": Quay,
            "items": newItems,
            "totals": {
                "Gross Weight": total_gross_weight,
                "Net Weight": total_net_weight,
                "Packages": total_packages
            }
        }

        json_response.append(processed_entry)

    return json.dumps(json_response, indent=4)
