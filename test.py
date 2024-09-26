import json


def process_container_data(data):
    data = data[0]

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
        description = item.get("description", "")  # Use .get() to avoid KeyError
        gross_weight = float(item.get("Gross Weight", 0))
        net_weight = float(item.get("Net Weight", 0))

        item_data = {
            "ArrivalNotice1": f"1{data['Stay']}{data['LoydsNumber']}*{str(data['Article']).zfill(4)}",
            "ArrivalNotice2": f"{data['Agent Code']}*{item_number}*{data['BL number']}",
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
    
    # Reconstruct the processed entry
    processed_entry = {
        "container": data["container"],
        "vissel": data["Vissel"],
        "Quay": Quay,
        "dispatch_country": data["Port Of Loading"].strip()[:2],
        "items": newItems,
        "totals": {
            "Gross Weight": total_gross_weight,
            "Net Weight": total_net_weight,
            "Packages": total_packages
        }
    }

    return json.dumps(processed_entry, indent=4)

data= [
    {
        "container": "TTNU1152536",
        "Vissel": "CMA CGM CONCORDE",
        "Port Of Loading": "CNJIU",
        "LoydsNumber": "L9839208",
        "BL number": "NCG0104614",
        "Article": 157,
        "Agent Code": "CMACGM",
        "Stay": 285255,
        "Quay": 1700,
        "items": [
            {
                "item": 1,
                "description": "WORKED SLATE AND ARTICLES OF S",
                "Gross Weight": 22974,
                "Net Weight": 22974,
                "Packages": 1969
            }
        ]
    }
]

dj = process_container_data(data)

def json_to_xml(json_data):
    data = json.loads(json_data)
    xml_files = []

    xml_template = '''<?xml version="1.0" encoding="iso-8859-1"?>
<NctsSswDeclaration xsi:noNamespaceSchemaLocation="NctsSsw.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeDeclaration>N</typeDeclaration>
  <version>516.1.002</version>
  <CustomsStreamliner>
    <template>CASA</template>
    <company>DKM</company>
    <user>STAGIAIR2</user>
    <printLocation>DEFAULT PRINTGROEP</printLocation>
    <createDeclaration>F</createDeclaration>
    <sendingMode>R</sendingMode>
    <sendDeclaration>F</sendDeclaration>
    <dossierNumberERP>{Container}</dossierNumberERP>
    <transhipment>F</transhipment>
    <isFerry>F</isFerry>
    <Principal>
      <id>CASAINTERN</id>
      <ContactPerson>
        <contactPersonCode>MSC NCTS</contactPersonCode>
      </ContactPerson>
    </Principal>
    <IntegratedLogisticStreamliner>
      <createDossier>F</createDossier>
      <IlsDossier>
        <iLSCompany>DKM</iLSCompany>
        <dossierId>71100</dossierId>
      </IlsDossier>
    </IntegratedLogisticStreamliner>
    <ControlValues>
      <ControlArticles>0</ControlArticles>
      <ControlPackages>{globalPkgs}</ControlPackages>
      <ControlGrossmass>{globalWeight}</ControlGrossmass>
      <ControlNetmass>{globalWeight}</ControlNetmass>
    </ControlValues>
  </CustomsStreamliner>
  <MessageBody>
  <GoodsDeclaration>
    <Header>
      <typeOfDeclaration>T1</typeOfDeclaration>
      <countryOfDestinationCode>BE</countryOfDestinationCode>
      <codeAuthorisedLocationOfGoods>{Quay}</codeAuthorisedLocationOfGoods>
      <countryOfDispatchExportCode>{DispatchCountry}</countryOfDispatchExportCode>
      <identityOfMeansOfTransportCrossingBorder language="EN">{Vissel}</identityOfMeansOfTransportCrossingBorder>
    </Header>
  </GoodsDeclaration>
    {GoodsItems}
  </MessageBody>
</NctsSswDeclaration>'''
    formatted_goods_items = []
    itemNumber = 1
    for data_items in data['items'] :
        goods_items = '''
        <GoodsItems>
            <itemNumber>{itemNmber}</itemNumber>
            <goodsDescription language="EN">{Description}</goodsDescription>
            <grossMass>{GrossWeight}</grossMass>
            <netMass>{NetWeight}</netMass>
            <PreviousAdministrativeReferences>
                <previousDocumentType>126E</previousDocumentType>
                <previousDocumentReference language="EN">{ArrivalNotice1}</previousDocumentReference>
                <complementOfInformation language="EN">{ArrivalNotice2}</complementOfInformation>
            </PreviousAdministrativeReferences>
            <ProducedDocuments>
                <documentType>Y026</documentType>
                <documentReference language="EN">BEAEOF0000064GDA</documentReference>
                <complementOfInformation language="EN">.</complementOfInformation>
            </ProducedDocuments>
            <Containers>
                <containerNumber>{Container}</containerNumber>
            </Containers>
            <Packages>
                <marksAndNumbersOfPackages language="EN">KARTON</marksAndNumbersOfPackages>
                <kindOfPackages>CT</kindOfPackages>
                <numberOfPackages>{Packages}</numberOfPackages>
                <numberOfPieces>0</numberOfPieces>
            </Packages>
        </GoodsItems>
        '''
          
        # Format goods items with the given data
        formatted_goods_items.append(goods_items.format(
            Description=data_items["Description"],
            GrossWeight=data_items["Gross Weight"],
            NetWeight=data_items["Net Weight"],
            ArrivalNotice1=data_items["ArrivalNotice1"],
            ArrivalNotice2=data_items["ArrivalNotice2"],
            Container=data_items["Container"],
            Packages=data_items["Packages"],
            itemNmber=itemNumber,
        ))

        itemNumber += 1

        # Join the goods items list into a single string
    formatted_goods_items_str = "".join(formatted_goods_items)

        # Fill the XML template with the formatted goods items
    xml_filled = xml_template.format (
        Container=data["container"],
        Vissel=data["vissel"],
        DispatchCountry=data["dispatch_country"],
        Quay=data["Quay"],
        globalWeight=data["totals"]["Gross Weight"],
        globalPkgs=data["totals"]["Packages"],
        GoodsItems = formatted_goods_items_str
    )

    xml_files.append(xml_filled)

    return xml_files

print(json_to_xml(dj))

#print(dj)

