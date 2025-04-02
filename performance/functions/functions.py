import logging
from datetime import datetime

def calculate_process_times(result):
    # Initialize storage variables
    declaration_metrics = []
    company_metrics = {}
    type_metrics = {}
    creation_type_metrics = {
        'Manual': {'count': 0, 'creation_to_dec': 0, 'dec_to_dms': 0, 'total': 0},
        'Automated': {'count': 0, 'creation_to_dec': 0, 'dec_to_dms': 0, 'total': 0}
    }
    
    for item in result:
        try:
            decl_id = item["DECLARATIONID"]
            history = item["HISTORY"]
            
            # Sort history by datetime
            sorted_history = sorted(history, key=lambda x: x["HISTORYDATETIME"])
            
            # Get first event
            first_event = sorted_history[0]
            first_event_type = first_event["HISTORY_STATUS"]
            first_event_time = datetime.fromisoformat(first_event["HISTORYDATETIME"])
                
            # Find first DEC_DAT
            dec_dat_event = next((h for h in sorted_history if h["HISTORY_STATUS"] == "DEC_DAT"), None)
            if not dec_dat_event:
                continue
                
            dec_dat_time = datetime.fromisoformat(dec_dat_event["HISTORYDATETIME"])
            
            # Find first DMSACC after DEC_DAT
            dmsacc_event = next((h for h in sorted_history 
                               if h["HISTORYDATETIME"] > dec_dat_event["HISTORYDATETIME"] 
                               and h["HISTORY_STATUS"] == "DMSACC"), None)
            if not dmsacc_event:
                print(f"Skipping {decl_id}: No DMSACC event found after DEC_DAT.")
                continue
                
            dmsacc_time = datetime.fromisoformat(dmsacc_event["HISTORYDATETIME"])
            
            # Calculate time differences in hours
            creation_to_dec = (dec_dat_time - first_event_time).total_seconds() / 3600
            dec_to_dms = (dmsacc_time - dec_dat_time).total_seconds() / 3600
            total_time = (dmsacc_time - first_event_time).total_seconds() / 3600
            
            # Get company and type
            company = first_event["ACTIVECOMPANY"]
            doc_type = first_event["TYPEDECLARATIONSSW"]
            
            # Determine creation type
            creation_type = 'Automated' if first_event_type == 'INTERFACE' else 'Manual'
            
            # Store declaration metrics
            declaration_metrics.append({
                "DECLARATIONID": decl_id,
                "ACTIVECOMPANY": company,
                "TYPEDECLARATIONSSW": doc_type,
                "CREATION_TYPE": creation_type,
                "CREATION_TO_DEC_DAT_HRS": creation_to_dec,
                "DEC_DAT_TO_DMSACC_HRS": dec_to_dms,
                "TOTAL_PROCESS_TIME_HRS": total_time
            })
            
            # Aggregate for company metrics
            if company not in company_metrics:
                company_metrics[company] = {
                    "count": 0,
                    "creation_to_dec": 0,
                    "dec_to_dms": 0,
                    "total": 0
                }
            company_metrics[company]["count"] += 1
            company_metrics[company]["creation_to_dec"] += creation_to_dec
            company_metrics[company]["dec_to_dms"] += dec_to_dms
            company_metrics[company]["total"] += total_time
            
            # Aggregate for type metrics
            if doc_type not in type_metrics:
                type_metrics[doc_type] = {
                    "count": 0,
                    "creation_to_dec": 0,
                    "dec_to_dms": 0,
                    "total": 0
                }
            type_metrics[doc_type]["count"] += 1
            type_metrics[doc_type]["creation_to_dec"] += creation_to_dec
            type_metrics[doc_type]["dec_to_dms"] += dec_to_dms
            type_metrics[doc_type]["total"] += total_time
            
            # Aggregate for creation type metrics
            creation_type_metrics[creation_type]["count"] += 1
            creation_type_metrics[creation_type]["creation_to_dec"] += creation_to_dec
            creation_type_metrics[creation_type]["dec_to_dms"] += dec_to_dms
            creation_type_metrics[creation_type]["total"] += total_time
            
        except Exception as e:
            print(f"Error processing declaration {decl_id}: {str(e)}")
            continue
    
    # Calculate averages with zero division protection
    def safe_divide(a, b):
        return a / b if b > 0 else 0
    
    avg_by_company = [
        {
            "ACTIVECOMPANY": company,
            "AVG_CREATION_TO_DEC_DAT_HRS": safe_divide(metrics["creation_to_dec"], metrics["count"]),
            "AVG_DEC_DAT_TO_DMSACC_HRS": safe_divide(metrics["dec_to_dms"], metrics["count"]),
            "AVG_TOTAL_PROCESS_TIME_HRS": safe_divide(metrics["total"], metrics["count"]),
            "COUNT": metrics["count"]
        }
        for company, metrics in company_metrics.items()
    ]
    
    avg_by_type = [
        {
            "TYPEDECLARATIONSSW": doc_type,
            "AVG_CREATION_TO_DEC_DAT_HRS": safe_divide(metrics["creation_to_dec"], metrics["count"]),
            "AVG_DEC_DAT_TO_DMSACC_HRS": safe_divide(metrics["dec_to_dms"], metrics["count"]),
            "AVG_TOTAL_PROCESS_TIME_HRS": safe_divide(metrics["total"], metrics["count"]),
            "COUNT": metrics["count"]
        }
        for doc_type, metrics in type_metrics.items()
    ]
    
    avg_by_creation_type = [
        {
            "CREATION_TYPE": creation_type,
            "AVG_CREATION_TO_DEC_DAT_HRS": safe_divide(metrics["creation_to_dec"], metrics["count"]),
            "AVG_DEC_DAT_TO_DMSACC_HRS": safe_divide(metrics["dec_to_dms"], metrics["count"]),
            "AVG_TOTAL_PROCESS_TIME_HRS": safe_divide(metrics["total"], metrics["count"]),
            "COUNT": metrics["count"]
        }
        for creation_type, metrics in creation_type_metrics.items()
        if metrics["count"] > 0  # Only include if there are documents of this type
    ]
    
    return {
        "declaration_level_metrics": declaration_metrics,
        "average_by_company": avg_by_company,
        "average_by_type": avg_by_type,
        "average_by_creation_type": avg_by_creation_type
    }