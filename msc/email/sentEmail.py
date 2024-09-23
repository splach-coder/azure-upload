import xml.etree.ElementTree as ET
import json
from msc.utils.searchOnPorts import search_ports

def transform_json(input_data):
    transformed_data = []

    currentIndex = 0
    for container in input_data.get("containers", []):
        
        dispatch_country = search_ports(input_data.get("Port Of Loading"))

        # Construct transformed data for each item in each container
        transformed_data.append({
            "Vissel": input_data.get("Vissel"),
            "Container": container.get("container"),
            "globalWeight": 0,
            "globalPkgs": 0,
            "Quay" : "",
            "DispatchCountry" : dispatch_country,
            "items" : []
        })

        if input_data.get("Quay") == "1742" : 
            transformed_data[currentIndex]["Quay"] = "BEANRAZ03318002"
        
        for item in container.get("items", []):
            item_number = ''.join([i for i in item.get("Item", "") if i.isdigit()]).zfill(4)
            packages = ''.join([i for i in item.get("Packages", "") if i.isdigit()])
            description = item.get("desc", "")
            gross_weight = ''.join([i for i in item.get("Gross Weight", "") if i.isdigit()])
            net_weight = gross_weight

            transformed_data[currentIndex]["globalWeight"] += int(gross_weight)
            transformed_data[currentIndex]["globalPkgs"] += int(packages)

            item = {
                "ArrivalNotice1": f"1{input_data.get('Stay')}L{input_data.get('LoydsNumber')}*{input_data.get('Article').zfill(4)}",
                "ArrivalNotice2": f"{input_data.get('Agent Code')}*{item_number}*{input_data.get('BL number')}",
                "Container": container.get("container"),
                "Packages": packages,
                "Description": description,
                "Gross Weight": gross_weight,
                "Net Weight": net_weight
            }

            # Construct transformed data for each item in each container
            transformed_data[currentIndex]["items"].append(item)
        currentIndex += 1     

    return json.dumps(transformed_data, indent=4)

def json_to_xml(json_data):
    json_data = json.loads(transform_json(json_data))
    xml_files = []

    for data in json_data:
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
            Container=data["Container"],
            Vissel=data["Vissel"],
            DispatchCountry=data["DispatchCountry"],
            Quay=data["Quay"],
            globalWeight=data["globalWeight"],
            globalPkgs=data["globalPkgs"],
            GoodsItems = formatted_goods_items_str
        )

        xml_files.append(xml_filled)

    return xml_files