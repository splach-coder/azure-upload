import pandas as pd
from collections import Counter

PARQUET_FILE = "all_data.parquet"
TARGET_USER = "ZOHRA.HMOUDOU"

def load_data(parquet_path):
    df = pd.read_parquet(parquet_path)
    return df

def normalize_data(df):
    for col in ["USERCREATE", "USERCODE", "HISTORY_STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()
        
    df["HISTORYDATETIME"] = pd.to_datetime(df["HISTORYDATETIME"], errors="coerce", format='mixed')
    df = df.dropna(subset=["HISTORYDATETIME"])
    return df

def inspect_user_logs(df, user):
    user = user.upper()
    df_user = df[df["USERCODE"] == user].copy()
    print(f"Total rows for {user}: {len(df_user)}")
    
    # Check some example DECLARATIONIDs
    decl_ids = df_user["DECLARATIONID"].unique()
    print(f"Unique DECLARATIONIDs for {user} (sample 5): {decl_ids[:5]}")
    
    for decl_id in decl_ids[:5]:  # limit output
        print(f"\n=== History for DECLARATIONID: {decl_id} ===")
        decl_history = df[df["DECLARATIONID"] == decl_id].sort_values("HISTORYDATETIME")
        print(decl_history[["USERCREATE", "USERCODE", "HISTORY_STATUS", "HISTORYDATETIME"]])
        
        first_user_create = decl_history.iloc[0]["USERCREATE"]
        print(f"First USERCREATE: {first_user_create}")

        statuses = set(decl_history["HISTORY_STATUS"].tolist())
        print(f"Statuses in history: {statuses}")

import pandas as pd
import json
from datetime import datetime

def export_parquet_to_log(parquet_path: str, log_path: str):
    try:
        df = pd.read_parquet(parquet_path)

        # Normalize datetime
        df['HISTORYDATETIME'] = pd.to_datetime(df['HISTORYDATETIME'], errors='coerce', format='mixed')
        df = df.dropna(subset=['HISTORYDATETIME'])

        # Keep only important columns
        export_df = df[['DECLARATIONID', 'USERCREATE', 'USERCODE', 'HISTORY_STATUS', 'HISTORYDATETIME']]
        export_df['HISTORYDATETIME'] = export_df['HISTORYDATETIME'].astype(str)

        # Convert to list of dicts
        logs = export_df.to_dict(orient='records')

        # Write to JSON file
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        print(f"[✅] Log export completed: {log_path}")
    except Exception as e:
        print(f"[❌] Failed to export log: {e}")


def main():
    df = load_data(PARQUET_FILE)
    df = normalize_data(df)
    inspect_user_logs(df, TARGET_USER)

if __name__ == "__main__":
    export_parquet_to_log("all_data.parquet", "debug_data_dump.json")
    main()