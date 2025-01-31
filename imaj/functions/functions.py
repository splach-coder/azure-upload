import xml.etree.ElementTree as ET

def transform_data(input_data):
    # Extract static fields
    static_fields = {
        "BL Number": input_data.get("BL Number", ""),
        "LLoyds/Stay": input_data.get("LLoyds/Stay", ""),
        "Quay": input_data.get("Quay", ""),
        "PortOfLoading": input_data.get("PortOfLoading", ""),
        "Agent Code": input_data.get("Agent Code", ""),
        "Description": input_data.get("Description", ""),
    }
    
    # Generate the dynamic objects
    transformed_data = []
    for item in input_data.get("data", []):
        # Combine static fields with dynamic fields from the data list
        combined_object = {**static_fields, **item}
        transformed_data.append(combined_object)
    
    return transformed_data

def clean_data_to_structure(input_data):
    cleaned_data = []
    
    for item in input_data:
        cleaned_item = {
            "Container": item.get("Container"),
            "BL Number": item.get("BL Number").split('COSU')[-1],  # Remove prefix like "COSU" from BL Number
            "Stay": item.get("LLoyds/Stay").split('/')[1],  # Extract Stay from "LLoyds/Stay"
            "LLoyds": item.get("LLoyds/Stay").split('/')[0],  # Extract Lloyds from "LLoyds/Stay"
            "Quay": item.get("Quay"),
            "PortOfLoading": item.get("PortOfLoading"),
            "Agent Code": item.get("Agent Code"),
            "Description": item.get("Description"),
            "GrossWeight": item.get("GrossWeight"),
            "Pckgs": item.get("Pckgs"),
            "Article": item.get("Article")
        }
        cleaned_data.append(cleaned_item)
    
    return cleaned_data

def transform_data2(input_data, ports):
    transformed_data = []

    for idx, item in enumerate(input_data, start=1):
        transformed_item = {
            "ArrivalNotice1": f"1{item.get('Stay')}L{item.get('LLoyds')}*{item.get('Article').zfill(4)}",
            "ArrivalNotice2": f"{item.get('Agent Code')}*1*{item.get('BL Number')}",
            "Container": item.get("Container"),
            "Packages": item.get("Pckgs"),
            "Description": item.get("Description"),
            "Gross Weight": item.get("GrossWeight"),
            "Quay": item.get("Quay"),
            "origin": "",
        }
        
        for port in ports:
            if port["Port"].lower() == item.get("PortOfLoading").lower():  # Case-insensitive comparison
                transformed_item["origin"] =  port["Country Code"]
        
        transformed_data.append(transformed_item)
    
    return transformed_data

def create_xml_with_dynamic_values(data):
    # Create the root element with attributes
    root = ET.Element("PldaSswDeclaration", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "V:\\PCIL9\\Bin\\DevMcf\\000\\Interfaces\\Definition\\Customs\\PLDA Standaard\\PLDASSW.xsd"
    })

    # Add static elements
    ET.SubElement(root, "typeDeclaration").text = "PI"
    ET.SubElement(root, "version").text = "058"

    # Add CustomsStreamliner
    cs = ET.SubElement(root, "CustomsStreamliner")
    ET.SubElement(cs, "template").text = "WORLDEX IM7"
    ET.SubElement(cs, "company").text = "DKM"
    ET.SubElement(cs, "printLocation").text = "DKM-DEFAULT PRINTERGROEP"
    ET.SubElement(cs, "createDeclaration").text = "F"
    ET.SubElement(cs, "procedureType").text = "J"

    # IntegratedLogisticStreamliner
    ils = ET.SubElement(cs, "IntegratedLogisticStreamliner")
    ET.SubElement(ils, "createDossier").text = "F"
    ET.SubElement(ils, "dossierNumberERP").text = data.get("Container", "TTNU1152536")
    ils_dossier = ET.SubElement(ils, "IlsDossier")
    ET.SubElement(ils_dossier, "company").text = "DKM"

    # ControlValues
    cv = ET.SubElement(cs, "ControlValues")
    ET.SubElement(cv, "totalPrice").text = "0.00"
    ET.SubElement(cv, "totalGrossmass").text = str(data.get("Gross Weight", "0.00"))
    ET.SubElement(cv, "totalNetmass").text = str(data.get("Net Weight", "0.00"))
    ET.SubElement(cv, "totalPackages").text = str(data.get("Packages", "0.00"))

    # MessageBody
    mb = ET.SubElement(root, "MessageBody")
    sad_import = ET.SubElement(mb, "SADImport")
    ET.SubElement(sad_import, "functionCode").text = "9"
    ET.SubElement(sad_import, "languageCode").text = "NL"

    # GoodsDeclaration
    goods_declaration = ET.SubElement(sad_import, "GoodsDeclaration")
    customs = ET.SubElement(goods_declaration, "Customs")
    goods_location = ET.SubElement(customs, "GoodsLocation")
    ET.SubElement(goods_location, "precise").text = "BEZEEA00120"
    ET.SubElement(customs, "validationOffice").text = "BEZEE216010"

    # Add GoodsItem(s)
    goods_item = ET.SubElement(sad_import, "GoodsItem")
    ET.SubElement(goods_item, "sequence").text = str('1')
    ET.SubElement(goods_item, "netMass").text = str(data.get("Net Weight", "0.00"))
    ET.SubElement(goods_item, "grossMass").text = str(data.get("Gross Weight", "0.00"))
    ET.SubElement(goods_item, "goodsDescription").text = data.get("Description", "")
    packaging = ET.SubElement(goods_item, "Packaging")
    ET.SubElement(packaging, "marksNumber").text = data.get("marksNumber", "Imaj")
    ET.SubElement(packaging, "packages").text = str(data.get("Packages", ""))
    ET.SubElement(packaging, "packageType").text = "PK"
    ET.SubElement(goods_item, "containerIdentifier").text = data.get("Container", "")
    ET.SubElement(goods_item, "originCountry").text = data.get("origin", "")

    # Convert to string
    xml_str = ET.tostring(root, encoding="iso-8859-1", xml_declaration=True)
    return xml_str.decode("iso-8859-1")
