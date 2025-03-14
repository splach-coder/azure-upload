coordinates = [
    #vat number
    (14, 12, 158, 90),
    #invoice date
    (180, 105, 235, 137),
    #invoice ref
    (310, 105, 370, 137),
    #shipt to
    (40, 230, 260, 286),
    #INCO
    (15, 308, 205, 329),
]

coordinates_fr = [
    #vat number
    (14, 12, 158, 73),
    #invoice date
    (180, 95, 240, 105),
    #invoice ref
    (280, 90, 370, 100),
    #shipt to
    (40, 230, 260, 286),
    #INCO
    (15, 308, 205, 320),
]

coordinates_be = [
    #vat number
    (62, 48, 122, 58),
    #invoice date
    (180, 98, 238, 107),
    #invoice ref
    (310, 98, 399, 107),
    #shipt to
    (47, 233, 246, 296),
    #INCO
    (18, 312, 282, 321),
]

coordinates_it = [
     #vat number
    (14, 12, 158, 73),
    #invoice date
    (180, 98, 238, 107),
    #invoice ref
    (310, 97, 370, 106),
    #shipt to
    (40, 230, 260, 286),
    #INCO
    (15, 308, 205, 320),
]

coordinates_lastpage = [
    #total invoice 
    (75, 713, 145, 740),
]

coordinates_lastpage_fr = [
    #total invoice 
    (54, 706, 156, 716),
]

key_map = ["Vat", "Inv Date", "Inv Ref", "ship to", "Inco"]


inv_keyword_params = {
    "DN Nbr:": ((40, 0), 5),
    "Batches:": ((100, 0), 0),
    "Net Weight:": ((100, 0), 0),
    "All in Price": ((120, 0), 150),
    "Total for the line item": ((150, 10), 350),
    "Total freight related surcharges for the item:": ((150, 0), 300),
    "Commodity Code of country of dispatch:": ((100, 0), 0),
    "Country of Origin: ": ((25, 0), 5)
}

inv_keyword_params_fr = {
    "DN Nbr:": ((40, 0), 5),
    "Lots:": ((100, 0), 0),
    "Poids net: ": ((100, 0), 0),
    "Prix tout compris": ((120, 0), 150),
    "Total pour la ligne d'article": ((150, 10), 350),
    "Total freight related surcharges for the item:": ((150, 0), 300),
    "Code douanier du pays d'envoi:": ((100, 0), 0),
    "Pays d'origine:": ((35, 0), 2)
}

inv_keyword_params_it = {
    "DN Nbr:": ((40, 0), 5),
    "Batches:": ((100, 0), 0),
    "Peso netto: ": ((100, 0), 0),
    "Prezzo forfettario": ((120, 0), 150),
    "Totale per la voce": ((150, 10), 350),
    "Spese di trasporto totali per la voce:": ((150, 0), 300),
    "Codice delle merci del paese di spedizione:": ((100, 0), 0),
    "Country of Origin: ": ((25, 0), 5)
}

fallback_inv_keywords = {"Total freight related surcharges for the item:": {"Temp Reco Surchg" : ((170, 0), 300)}}

inv_keyword_params_de = {"Country of Origin: " : ((25, 0), 5), "Statistische Warennummer vom Versandland:" : ((100, 0), 0), "Batches:" : ((100, 0), 0), "Nettogewicht:" : ((100, 0), 0), "Total für Produkt" : ((150, 10), 350), "Gesamttransportzuschläge für den Artikel:" : ((150, 0), 300), "Pauschalpreis" : ((120, 0), 150), "DN Nbr:" : ((40, 0), 5)}

packingList_keyword_params = {"Tot. Carton": ((40, 0), 10), "Grand Total" : ((250, 0), 30), "Batch Number:" : ((70, 0), 0), "Delivery Note" : ((70, 0), 4), "Cust. Mat No:" : ((150, 0), 70), "Cust Mat Name:" : ((372, 0), 70)}