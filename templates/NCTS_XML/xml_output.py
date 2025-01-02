from typing import List, Dict
from xml.sax.saxutils import escape as escape_xml_chars
from global_db.ncts.dynamic_values import dossier_number

class NCTSXMLGenerator:
    """Generate NCTS XML declarations from input data."""
    
    def __init__(self):
        self.XML_VERSION = "516.1.002"
        self.XML_TEMPLATE = self._load_xml_template()
        
    def generate_declarations(self, json_data: List[Dict]) -> List[Dict]:
        """
        Generate XML declarations for each container in the input data.
        
        Args:
            json_data: List of container data dictionaries
            
        Returns:
            List of dictionaries containing XML content and container numbers
        """
        return [self._generate_single_declaration(data) for data in json_data]
    
    def _generate_single_declaration(self, data: Dict) -> Dict:
        """Generate XML declaration for a single container."""
        goods_items = self._format_goods_items(data['items'])
        xml_content = self.XML_TEMPLATE.format(
            Container=data.get("containers"),
            Vissel=data.get("vissel"),
            DispatchCountry=data.get("Origin"),
            Quay=data.get("Quay"),
            globalWeight=data.get("globalWeight"),
            globalWeight2=data.get("globalWeight2"),
            globalPkgs=data.get("Packages"),
            dossier_number=dossier_number,
            GoodsItems=goods_items
        )
        return {"xml": xml_content, "container": data["containers"]}
    
    def _format_goods_items(self, items: List[Dict]) -> str:
        """Format goods items section of the XML."""
        formatted_items = []
        for index, item in enumerate(items, 1):
            goods_item = self._format_single_goods_item(item, index)
            formatted_items.append(goods_item)
        return "".join(formatted_items)
    
    def _format_single_goods_item(self, item: Dict, item_number: int) -> str:
        """Format a single goods item entry."""
        return '''
        <GoodsItems>
            <itemNumber>{itemNumber}</itemNumber>
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
        '''.format(
            Description=escape_xml_chars(item["Description"]),
            GrossWeight=item.get("Gross Weight"),
            NetWeight=item.get("Net Weight"),
            ArrivalNotice1=item.get("ArrivalNotice1"),
            ArrivalNotice2=item.get("ArrivalNotice2"),
            Container=item.get("container"),
            Packages=item.get("Packages"),
            itemNumber=item_number
        )
    
    def _load_xml_template(self) -> str:
        """Load the base XML template."""
        return '''<?xml version="1.0" encoding="iso-8859-1"?>
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
        <dossierId>{dossier_number}</dossierId>
      </IlsDossier>
    </IntegratedLogisticStreamliner>
    <ControlValues>
      <ControlArticles>0</ControlArticles>
      <ControlPackages>{globalPkgs}</ControlPackages>
      <ControlGrossmass>{globalWeight}</ControlGrossmass>
      <ControlNetmass>{globalWeight2}</ControlNetmass>
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

# Usage example:
def generate_xml_declarations(json_data: List[Dict]) -> List[Dict]:
    """Wrapper function to generate XML declarations."""
    generator = NCTSXMLGenerator()
    return generator.generate_declarations(json_data)