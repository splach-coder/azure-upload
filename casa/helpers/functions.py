from casa.data.data import ports


def hanlde_country(header_details, ports):
    for entry in ports:
        if header_details["City"] == entry["Port"]:
            header_details["City"] = entry["Country"].upper()
    return  header_details       
   