import re
import json

def process_container_data(data):
    # Validate the container format
    container = data.get("container", "")
    valid_container = extract_valid_container(container)

    if not valid_container:
        return # Skip entries without valid containers

    # Process Incoterm
    incoterm = data.get("Incoterm", "")
    incoterm_array = incoterm.split()  # Split into an array of strings

    # Process Freight
    freight = extract_numeric_value(data.get("Freight", "0 USD"))

    # Process Vat 1 and Vat 2
    vat1 = extract_numeric_value(data.get("Vat 1", "0 USD"))
    vat2 = sum(extract_numeric_value(vat) for vat in data.get("Vat 2", "0 EUR").split("+"))

    # Initialize totals
    total_gross_weight = 0.0
    total_net_weight = 0.0
    total_packages = 0.0
    total_devises = 0.0

    # Process items and calculate totals
    items = data.get("items", [])
    for item in items:
        total_gross_weight += extract_numeric_value(item.get("Gross Weight", "0"))
        total_net_weight += extract_numeric_value(item.get("Net Weight", "0"))
        total_packages += extract_numeric_value(item.get("Packages", "0"))
        total_devises += extract_numeric_value(item.get("VALEUR", "0"))  # Assuming VALEUR is in devises

    # Reconstruct the processed entry
    processed_entry = {
        "container": valid_container,
        "Incoterm": incoterm_array,
        "Freight": freight,
        "Vat 1": vat1,
        "Vat 2": vat2,
        "items": items,
        "totals": {
            "Gross Weight": total_gross_weight,
            "Net Weight": total_net_weight,
            "Packages": total_packages,
            "DEVISES": total_devises
        }
    }

    return processed_entry

def extract_valid_container(container_string):
    container_arr = container_string.split(" ")
    container = None
    for str in container_arr:
        # Check if the container matches the format 4 chars and 7 digits
        pattern = r'^[A-Z]{4}\d{7}$'
        if re.match(pattern, str):
            container =  str

    return container

def extract_numeric_value(value):
    # Extract numeric value from string and convert to float
    match = re.search(r'[\d,.]+', value)
    if match:
        return float(match.group(0).replace(',', '.'))  # Replace comma with dot for float conversion
    return 0.0


# Example usage
input_data = {
            "container": "FICHE D INSTRUCTIONS GCXU6482664",
            "Incoterm": "FOB NINGBO",
            "Freight": "1822 USD",
            "Vat 1": "238 USD",
            "Vat 2": "21 EUR + 54 EUR",
            "items": [
                {
                    "HSCODE": "8516792000",
                    "VALEUR": "5909,48",
                    "DEVISES": "EUR",
                    "Gross Weight": "1310,95",
                    "Net Weight": "780,29",
                    "Packages": "157"
                },
                {
                    "HSCODE": "8516797090",
                    "VALEUR": "35053,74",
                    "DEVISES": "EUR",
                    "Gross Weight": "5910,8",
                    "Net Weight": "3954,85",
                    "Packages": "1194"
                }
            ]
        }


# Process the input data
processed_output = process_container_data(input_data)

import xml.etree.ElementTree as ET
import json

def json_to_xml(data):
    

  xml_template = r'''<?xml version="1.0" encoding="iso-8859-1"?>
<SADImport xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="V:\PCIL9\Bin\DevMcf\000\interfaces\definition\Customs\PLDA Standaard\SAD_DV1 v2.xsd">
  <functionCode>9</functionCode>
  <languageCode>NL</languageCode>
  <GoodsDeclaration>
    <commercialReference>{container}</commercialReference>
    <TransactionNature>
      <transactionNature1>1</transactionNature1>
      <transactionNature2>1</transactionNature2>
    </TransactionNature>
    <Declarant>
      <declarantstatus>2</declarantstatus>
      <authorisedIdentity>0873</authorisedIdentity>
      <OperatorIdentity>
        <country>BE</country>
        <identifier>005</identifier>
        <operatorIdentity>0404555920</operatorIdentity>
      </OperatorIdentity>
      <Operator>
        <operatorName>IDEAL</operatorName>
        <OperatorAddress>
          <postalCode>2060</postalCode>
          <streetAndNumber1>VAN DE WERVESTRAAT 8</streetAndNumber1>
          <city>ANTWERPEN</city>
          <country>BE</country>
        </OperatorAddress>
        <ContactPerson>
          <contactPersonName>LUC</contactPersonName>
          <contactPersonCommunicationNumber>+32 3 205 60 37</contactPersonCommunicationNumber>
          <contactPersonEmail>import@DKM-customs.com</contactPersonEmail>
          <contactPersonFaxNumber>+32 3 205 60 39</contactPersonFaxNumber>
        </ContactPerson>
      </Operator>
    </Declarant>
    <ChargesImport>
      <VATCharges>
        <charges>{vat}</charges>
        <ExchangeRate>
          <exchangeRate>1.0000</exchangeRate>
          <currency>EUR</currency>
        </ExchangeRate>
      </VATCharges>
      <CustomsCharges>
        <transportInsuranceCharges>{freight}</transportInsuranceCharges>
        <ExchangeRate>
          <exchangeRate>1.0000</exchangeRate>
          <currency>EUR</currency>
        </ExchangeRate>
      </CustomsCharges>
    </ChargesImport>
 
    <Customs>
      <GoodsLocation>
        <precise>X-WAIT ARRIVAL NOTICE</precise>
      </GoodsLocation>
      <validationOffice>BEANR216000</validationOffice>
    </Customs>

    <TransportMeans>
      <DeliveryTerms>
        <deliveryTerms>{incoterm1}</deliveryTerms>
        <deliveryTermsPlace>{incoterm2}</deliveryTermsPlace>
      </DeliveryTerms>
      <borderMode>1</borderMode>
      <borderNationality>BE</borderNationality>
      <inlandMode>3</inlandMode>
      <dispatchCountry>{dispatchCountry}</dispatchCountry>
    </TransportMeans>
  </GoodsDeclaration>
  {goodsItems}
</SADImport>
  '''

  formatted_goods_items = []
  itemNumber = 1
  for data_items in data['items'] :
    goods_items = r'''
          <GoodsItem>
    <sequence>{itemNbr}</sequence>
    <commodityCode>{hs}</commodityCode>
    <netMass>{netweight}</netMass>
    <grossMass>{grossweight}</grossMass>
    <Packaging>
      <marksNumber>NO AN</marksNumber>
      <packages>{packages}}</packages>
      <packageType>PA</packageType>
    </Packaging>
    <containerIdentifier>{container}</containerIdentifier>
    <ProducedDocument>
      <Document>
        <documentReference>GROUPESEBFR-161627</documentReference>
        <documentType>4007</documentType>
      </Document>
    </ProducedDocument>
    <ProducedDocument>
      <Document>
        <documentReference>BE0787675929</documentReference>
        <documentType>Y040</documentType>
      </Document>
      <producedDocumentsValidationOffice>GROUPE SEB EXPORT</producedDocumentsValidationOffice>
    </ProducedDocument>
    <ProducedDocument>
      <Document>
        <documentReference>.</documentReference>
        <documentType>N935</documentType>
      </Document>
      <ArchiveInformation>
        <archiveLocationIndicator>1</archiveLocationIndicator>
        <archiveSupport>2</archiveSupport>
      </ArchiveInformation>
    </ProducedDocument>
    <ProducedDocument>
      <Document>
        <documentReference>.</documentReference>
        <documentType>N271</documentType>
      </Document>
      <ArchiveInformation>
        <archiveLocationIndicator>1</archiveLocationIndicator>
        <archiveSupport>2</archiveSupport>
      </ArchiveInformation>
    </ProducedDocument>
    <destinationCountry>FR</destinationCountry>
    <SupplementaryUnits>
      <supplementaryUnits>0</supplementaryUnits>
      <supplementaryUnitsCode>NAR</supplementaryUnitsCode>
    </SupplementaryUnits>
    <originCountry>{dispatch}</originCountry>
    <CustomsTreatment>
      <valuationMethod>1</valuationMethod>
      <Preference>
        <preference1>1</preference1>
        <preference2>00</preference2>
      </Preference>
      <Procedure>
        <procedurePart1>40</procedurePart1>
        <procedurePart2>00</procedurePart2>
        <procedureType>H</procedureType>
        <nationalProcedureCode>4A0</nationalProcedureCode>
      </Procedure>
    </CustomsTreatment>
    <destinationRegion>1</destinationRegion>
    <Price>
      <price>{price}</price>
    </Price>
  </GoodsItem>
        '''         
            # Format goods items with the given data
    
    formatted_goods_items.append(goods_items.format(
      itemNbr=itemNumber,
      hs=data_items["HSCODE"],
      dispatch=data["dispatch_country"],
      Container=data["container"],
      grossweight=data_items["Gross Weight"],
      netweight=data_items["Net Weight"],
      packages=data_items["Packages"],
      price=data_items["VALEUR"],
    ))

    itemNumber += 1

    # Join the goods items list into a single string
    formatted_goods_items_str = "".join(formatted_goods_items)

  # Fill the XML template with the formatted goods items
  xml_filled = xml_template.format (
      container=data["container"],
      dispatchCountry=data["dispatch_country"],
      incoterm1=data["Incoterm"][0],
      incoterm2=data["Incoterm"][1],
      freight=data["Freight"],
      vat=data["Vat"],
      goodsItems = formatted_goods_items_str
  )

  return xml_filled

print(processed_output['container'])

#print(json_to_xml(processed_output))






