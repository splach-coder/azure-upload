import xml.etree.ElementTree as ET
import json

def json_to_xml(data):

  xml_template = '''
  <PldaSswDeclaration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="file:///C:/Users/luc.dekerf/Desktop/XSD%20Schema/PLDASSW.xsd">
    <typeDeclaration>PI</typeDeclaration>
    <linkIdERP>ETA - AN </linkIdERP>
    <CustomsStreamliner>
        <template>SEB IMAH</template>
        <company>IDEAL</company>
        <status>LUC</status>
        <createDeclaration>T</createDeclaration>
          <ControlValues>
            <ControlPrice>{globalPrice}</ControlPrice>
            <ControlPackages>{globalPkgs}</ControlPackages>
            <ControlGrossmass>{globalGross}</ControlGrossmass>
            <ControlNetmass>{globalNet}</ControlNetmass>
          </ControlValues>
    </CustomsStreamliner>
    <MessageBody>
<SADImport>
  <functionCode>9</functionCode>
  <languageCode>NL</languageCode>
  <GoodsDeclaration>
    <commercialReference>{Container}</commercialReference>
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
    </MessageBody>
</PldaSswDeclaration>
  '''

  formatted_goods_items = []
  itemNumber = 1
  for data_items in data['items'] :
    goods_items = '''
          <GoodsItem>
    <sequence>{itemNbr}</sequence>
    <commodityCode>{hs}</commodityCode>
    <netMass>{netweight}</netMass>
    <grossMass>{grossweight}</grossMass>
    <Packaging>
      <marksNumber>NO AN</marksNumber>
      <packages>{packages}</packages>
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
      container=data["container"],
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
      Container=data["container"],
      dispatchCountry=data["dispatch_country"],
      incoterm1=data["Incoterm"][0],
      incoterm2=data["Incoterm"][1],
      freight=data["Freight"],
      vat=data["Vat"],
      globalPkgs=data["totals"]["Gross Weight"],
      globalGross=data["totals"]["Net Weight"],
      globalNet=data["totals"]["Packages"],
      globalPrice=data["totals"]["DEVISES"],
      goodsItems = formatted_goods_items_str
  )

  return xml_filled