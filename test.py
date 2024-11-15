from sofidel.helpers.functions import find_page_with_cmr_data, handle_invoice_data
from sofidel.service.extractors import extract_cmr_collis_data_with_dynamic_coordinates, extract_table_data_with_dynamic_coordinates, extract_text_from_coordinates
from sofidel.config.coords import cmr_coordinates, invoice_coordinates, cmr_adress_coords, cmr_totals_coords


pdfpath = "CMR 5470783.pdf"

page_dn = find_page_with_cmr_data(pdfpath, keywords=["PRODUCT CODE", "CUSTOMER PART NUMBER", "DESCRIPTION", "u.o.M.", "QUANTITY", "H.U"])
page_totals = find_page_with_cmr_data(pdfpath, keywords=["DELIVERY NOTE", "TOTAL WEIGHT", "UNITS TOTAL WEIGHT", "PALLETS TOTAL WEIGHT", "PALLETS"])
cmr_collis = extract_cmr_collis_data_with_dynamic_coordinates(pdfpath, page_dn[0])

print(page_totals)