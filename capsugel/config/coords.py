coordinates = [
    #vat number
    (50, 49, 122, 57),
    #invoice date
    (180, 105, 235, 115),
    #invoice ref
    (310, 97, 370, 106),
    #shipt to
    (40, 230, 260, 276),
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

coordinates_lastpage = [
    #total invoice 
    (80, 730, 130, 740),
]

key_map = ["Vat", "Inv Date", "Inv Ref", "ship to", "Inco"]

inv_keyword_params = {"Country of Origin: " : ((25, 0), 5), "Commodity Code of country of dispatch:" : ((100, 0), 0), "Batches:" : ((100, 0), 0),  "Net Weight:" : ((100, 0), 0), "Total for the line item" : ((150, 10), 350), "Total freight related surcharges for the item:" : ((150, 0), 300), "All in Price" : ((120, 0), 150), "DN Nbr:" : ((40, 0), 5)}
fallback_inv_keywords = {"Total freight related surcharges for the item:": {"Temp Reco Surchg" : ((170, 0), 300)}}

inv_keyword_params_de = {"Country of Origin: " : ((25, 0), 5), "Statistische Warennummer vom Versandland:" : ((100, 0), 0), "Batches:" : ((100, 0), 0), "Nettogewicht:" : ((100, 0), 0), "Total für Produkt" : ((150, 10), 350), "Gesamttransportzuschläge für den Artikel:" : ((150, 0), 300), "Pauschalpreis" : ((120, 0), 150), "DN Nbr:" : ((40, 0), 5)}

packingList_keyword_params = {"Tot. Carton": ((30, 0), 30), "Grand Total" : ((250, 0), 30), "Batch Number:" : ((70, 0), 0), "Delivery Note" : ((70, 0), 4), "Cust. Mat No:" : ((150, 0), 70), "Cust Mat Name:" : ((372, 0), 70)}