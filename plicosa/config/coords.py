coordinates = [
    #vat number
    (50, 45, 120, 55),
    #invoice date
    (180, 105, 235, 115),
    #invoice ref
    (310, 105, 350, 115),
    #vat number
    (50, 230, 150, 260),
    #INCO
    (20, 310, 65, 320),
]

coordinates_lastpage = [
    #total invoice 
    (80, 730, 130, 740),
]

key_map = ["Vat", "Inv Date", "Inv Ref", "ship to", "Inco"]

inv_keyword_params = {"Country of Origin: " : ((25, 0), 5), "Commodity Code of country of dispatch:" : ((100, 0), 0), "Batches:" : ((100, 0), 0),  "Net Weight:" : ((100, 0), 0), "Total for the line item" : ((150, 10), 350), "All in Price" : ((120, 10), 150), "DN Nbr:" : ((40, 0), 5)}

packingList_keyword_params = {"Total Pallet": ((30, 10), 30), "Grand Total" : ((250, 0), 30), "Batch Number:" : ((70, 0), 0), "Delivery Note" : ((70, 0), 4)}