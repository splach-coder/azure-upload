import xml.etree.ElementTree as ET
import json
import io


def transform_json(input_data):
    # Extract fields from input
    vissel = input_data.get("Vissel")
    stay = input_data.get("Stay")
    loyds_number = input_data.get("LoydsNumber")
    article_number = input_data.get("Article").zfill(4)  # Make sure Article is 4 digits
    agent_code = input_data.get("Agent Code")
    item_number = ''.join([i for i in input_data.get("Item", "") if i.isdigit()]).zfill(4)  # Remove strings, ensure 4 digits
    bl_number = input_data.get("BL number")
    quay = input_data.get("Quay")
    container = input_data.get("Container")
    packages = ''.join([i for i in input_data.get("Packages") if i.isdigit()])  # Remove strings, keep only digits
    description = input_data.get("Description")
    gross_weight = ''.join([i for i in input_data.get("Gross Weight") if i.isdigit()])  # Remove strings, keep only digits
    net_weight = gross_weight  # Net Weight equals Gross Weight
    
    # Transform values based on rules
    arrival_notice1 = f"1{stay}L{loyds_number}*{article_number}"
    arrival_notice2 = f"{agent_code}*{item_number}*{bl_number}"
    if quay == "1742":
        quay = "BEDELAZ03318001"
    if quay == "CS1700P":
        quay = "BEDELAZ03318001" 
    if quay == "913":
        quay = "BEDELAZ03318001"
    if quay == "CSP":
        quay = "BEDELAZ03318001"    
    
    # Construct the output JSON
    output_data = {
        "Vissel": vissel,
        "ArrivalNotice1": arrival_notice1,
        "ArrivalNotice2": arrival_notice2,
        "Quay": quay,
        "Container": container,
        "Packages": packages,
        "Description": description,
        "Gross Weight": gross_weight,
        "Net Weight": net_weight
    }
    
    return json.dumps(output_data, indent=4)

def json_to_xml(json_data):
    json_data = json.loads(transform_json(json_data))

    # Define the XML structure with placeholders for data
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
      </IlsDossier>
    </IntegratedLogisticStreamliner>
    <ControlValues>
      <ControlArticles>0</ControlArticles>
      <ControlPackages>{Packages}</ControlPackages>
      <ControlGrossmass>{GrossWeight}</ControlGrossmass>
      <ControlNetmass>{NetWeight}</ControlNetmass>
    </ControlValues>
  </CustomsStreamliner>
  <MessageBody>
    <GoodsDeclaration>
      <Header>
        <typeOfDeclaration>T1</typeOfDeclaration>
        <countryOfDestinationCode>BE</countryOfDestinationCode>
        <codeAuthorisedLocationOfGoods>BEDELAZ03318001</codeAuthorisedLocationOfGoods>
        <countryOfDispatchExportCode>CN</countryOfDispatchExportCode>
        <inlandTransportMode>80</inlandTransportMode>
        <transportModeAtBorder>10</transportModeAtBorder>
        <identityOfMeansOfTransportAtDeparture language="EN">LICHTER</identityOfMeansOfTransportAtDeparture>
        <nationalityOfMeansOfTransportAtDeparture>BE</nationalityOfMeansOfTransportAtDeparture>
        <identityOfMeansOfTransportCrossingBorder language="EN">{Vissel}</identityOfMeansOfTransportCrossingBorder>
        <nationalityOfMeansOfTransportCrossingBorder>BE</nationalityOfMeansOfTransportCrossingBorder>
        <typeOfMeansOfTransportCrossingBorder>11</typeOfMeansOfTransportCrossingBorder>
        <containerisedIndicator>T</containerisedIndicator>
        <dialogLanguageIndicatorAtDeparture>NL</dialogLanguageIndicatorAtDeparture>
        <nctsAccompanyingDocumentLanguageCode>NL</nctsAccompanyingDocumentLanguageCode>
        <simplifiedProcedureFlag>T</simplifiedProcedureFlag>
        <declarationPlace language="EN">2000</declarationPlace>
        <Security>(</Security>
      </Header>
    </GoodsDeclaration>
    <GoodsItems>
      <itemNumber>1</itemNumber>
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
  </MessageBody>
</NctsSswDeclaration>
    '''

    # Replace placeholders with actual values from JSON
    xml_filled = xml_template.format(
        Container=json_data["Container"],
        Packages=json_data["Packages"],
        GrossWeight=json_data["Gross Weight"],
        NetWeight=json_data["Net Weight"],
        Vissel=json_data["Vissel"],
        Description=json_data["Description"],
        ArrivalNotice1=json_data["ArrivalNotice1"],
        ArrivalNotice2=json_data["ArrivalNotice2"]
    )
    
    return xml_filled

