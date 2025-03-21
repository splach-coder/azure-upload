import xml.etree.ElementTree as ET
import json

def json_to_xml(json_data):
    data = json.loads(json_data)

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
        <dossierId>71266</dossierId>
      </IlsDossier>
    </IntegratedLogisticStreamliner>
    <ControlValues>
      <ControlArticles>0</ControlArticles>
      <ControlPackages>{globalPkgs}</ControlPackages>
      <ControlGrossmass>{globalWeight}</ControlGrossmass>
      <ControlNetmass>0</ControlNetmass>
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
    formatted_goods_items = []
    itemNumber = 1
    for data_items in data['items'] :
        goods_items = '''
        <GoodsItems>
            <itemNumber>{itemNmber}</itemNumber>
            <goodsDescription language="EN">{Description}</goodsDescription>
            <grossMass>{GrossWeight}</grossMass>
            <netMass>0</netMass>
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

    return xml_filled



