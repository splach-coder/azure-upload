from casa.data.data import ports


def hanlde_country(header_details, ports):
    for entry in ports:
        if header_details["City"] == entry["Port"]:
            header_details["City"] = entry["Country"].upper()
    return  header_details

def aggregate_container_data(results):
    """
    Aggregates container data by summing package, net, and gross values for each container
    """
    container_totals = {}
    
    for obj in results:
        container = obj['container']

        # Initialize container data if not exists
        if container not in container_totals:
            container_totals[container] = {
                'container': container,
                'package': 0,
                'net': 0,
                'gross': 0
            }
            
        for item in obj['items']:
            # Sum the values
            container_totals[container]['package'] += item.get('pckg', 0)  # assuming 'pckg' is the field name
            container_totals[container]['net'] += item.get('net', 0)  # assuming 'net' is the field name
            container_totals[container]['gross'] += item.get('gross', 0)  # assuming 'gross' is the field name

    # Convert dictionary to list of container data
    return list(container_totals.values())
       
   