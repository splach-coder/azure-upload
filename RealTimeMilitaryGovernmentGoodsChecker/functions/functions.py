def transform_data(rows):
    transformed_rows = []
    
    for row in rows:
        transformed_row = {
            "DECLARATIONID": row.get("DECLARATIONID", ""),
            "MESSAGESTATUS": row.get("MESSAGESTATUS", ""),
            "ACTIVECOMPANY": row.get("ACTIVECOMPANY", ""),
            "DATEOFACCEPTANCE": row.get("DATEOFACCEPTANCE", ""),
            "TYPEDECLARATIONSSW": row.get("TYPEDECLARATIONSSW", ""),
            "USERCREATE": row.get("USERCREATE", ""),
            "ADDRESS": " ".join([
                row.get("CONSIGNEENAME", ""),
                row.get("CONSIGNEESTREETANDNUMBER", ""),
                row.get("CONSIGNEEPOSTCODE", ""),
                row.get("CONSIGNEECITY", ""),
                row.get("CONSIGNEECOUNTRY", "")
            ]).strip()
        }
        transformed_rows.append(transformed_row)
    
    return transformed_rows