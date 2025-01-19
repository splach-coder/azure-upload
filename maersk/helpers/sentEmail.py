import xml.etree.ElementTree as ET
import json


def json_to_xml(json_data):
    containers_data = json.loads(json_data)

    xml_list = []  # List to store the generated XMLs for each container

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
        <contactPersonCode>BCTN</contactPersonCode>
      </ContactPerson>
    </Principal>
    <IntegratedLogisticStreamliner>
      <createDossier>F</createDossier>
      <IlsDossier>
        <iLSCompany>DKM</iLSCompany>
        <dossierId>72496</dossierId>
      </IlsDossier>
    </IntegratedLogisticStreamliner>
    <ControlValues>
      <ControlArticles>0</ControlArticles>
      <ControlPackages>{globalPkgs}</ControlPackages>
      <ControlGrossmass>{globalGROSSWeight}</ControlGrossmass>
      <ControlNetmass>{globalNETWeight}</ControlNetmass>
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
      <simplifiedProcedureFlag>T</simplifiedProcedureFlag>
    </Header>
  </GoodsDeclaration>
    {GoodsItems}
  </MessageBody>
</NctsSswDeclaration>'''

    # Loop through each container's data and generate XML
    for container_data in containers_data:
        formatted_goods_items = []
        itemNumber = 1
        
        for data_items in container_data['items']:
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
        xml_filled = xml_template.format(
            Container=container_data["container"],
            Vissel=container_data["vissel"],
            DispatchCountry=container_data["dispatch_country"],
            Quay=container_data["Quay"],
            globalGROSSWeight=container_data["totals"]["Gross Weight"],
            globalNETWeight=container_data["totals"]["Net Weight"],
            globalPkgs=container_data["totals"]["Packages"],
            GoodsItems=formatted_goods_items_str
        )

        # Append the generated XML to the list
        xml_list.append(xml_filled)

    return xml_list
