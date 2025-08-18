#-----------------------------------------------------------------------------
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import pandas as pd

def count_user_file_creations_last_10_days(df):
    import_users = [
        'FADWA.ERRAZIKI', 'AYOUB.SOURISTE', 'AYMANE.BERRIOUA', 'SANA.IDRISSI', 'AMINA.SAISS',
        'KHADIJA.OUFKIR', 'ZOHRA.HMOUDOU', 'SIMO.ONSI', 'YOUSSEF.ASSABIR', 'ABOULHASSAN.AMINA',
        'MEHDI.OUAZIR', 'OUMAIMA.EL.OUTMANI', 'HAMZA.ALLALI', 'MUSTAPHA.BOUJALA', 'HIND.EZZAOUI'
    ]

    export_users = [
        'IKRAM.OULHIANE', 'MOURAD.ELBAHAZ', 'MOHSINE.SABIL', 'AYA.HANNI',
        'ZAHIRA.OUHADDA', 'CHAIMAAE.EJJARI', 'HAFIDA.BOOHADDOU', 'KHADIJA.HICHAMI', 'FATIMA.ZAHRA.BOUGSIM'
    ]

    users = import_users + export_users

    manual_statuses = {"INTERFACE", "COPIED", "COPY", "NEW"}

    # Clean columns like in calculate_single_user_metrics_fast
    for col in ["USERCREATE", "USERCODE", "HISTORY_STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    df["HISTORYDATETIME"] = pd.to_datetime(df["HISTORYDATETIME"], errors="coerce", format="mixed")
    df = df.dropna(subset=["HISTORYDATETIME"])
    df["HISTORYDATETIME"] = df["HISTORYDATETIME"].dt.tz_localize(None)

    # Last 10 working days (Mon-Fri)
    today = datetime.now().date()
    working_days = []
    curr = today
    while len(working_days) < 10:
        if curr.weekday() < 5:
            working_days.insert(0, curr)
        curr -= timedelta(days=1)

    results = []

    for user in users:
        user_daily = {day.strftime("%d/%m"): 0 for day in working_days}

        cutoff = datetime.now() - timedelta(days=90)
        recent_df = df[df["HISTORYDATETIME"] >= cutoff]
        user_decls = recent_df[recent_df["USERCODE"] == user]["DECLARATIONID"].unique()

        # Work on all declarations this user touched
        user_scope_df = df[df["DECLARATIONID"].isin(user_decls)].copy()

        grouped = user_scope_df.groupby("DECLARATIONID")

        for decl_id, group in grouped:
            group = group.sort_values("HISTORYDATETIME")
            if group.empty:
                continue

            user_rows = group[group["USERCODE"] == user]
            if user_rows.empty:
                continue

            first_action_date = user_rows["HISTORYDATETIME"].min().date()
            if first_action_date not in working_days:
                continue

            user_statuses = set(user_rows["HISTORY_STATUS"].tolist())
            is_manual = bool(manual_statuses.intersection(user_statuses))

            is_automatic = False
            if not is_manual:
                has_batchproc_interface = not group[
                    (group["USERCODE"] == "BATCHPROC") & (group["HISTORY_STATUS"] == "INTERFACE")
                ].empty

                if has_batchproc_interface:
                    mod_users = group[
                        (group["HISTORY_STATUS"] == "MODIFIED") & (group["USERCODE"] != "BATCHPROC")
                    ]["USERCODE"].value_counts()

                    if not mod_users.empty and mod_users.index[0] == user:
                        is_automatic = True

            if is_manual or is_automatic:
                key = first_action_date.strftime("%d/%m")
                user_daily[key] += 1

        results.append({
            "user": user,
            "team": "import" if user in import_users else "export",
            "daily_file_creations": user_daily
        })

    return results

def calculate_single_user_metrics_fast(df_all, username):
    df = df_all.copy()

    for col in ["USERCREATE", "USERCODE", "HISTORY_STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    df["HISTORYDATETIME"] = pd.to_datetime(df["HISTORYDATETIME"], errors="coerce", format="mixed")
    df = df.dropna(subset=["HISTORYDATETIME"])
    df["HISTORYDATETIME"] = df["HISTORYDATETIME"].dt.tz_localize(None)

    username = username.upper()
    cutoff = datetime.now() - timedelta(days=90)
    recent_df = df[df["HISTORYDATETIME"] >= cutoff]

    user_decls = recent_df[recent_df["USERCODE"] == username]["DECLARATIONID"].unique()
    if len(user_decls) == 0:
        return {
            "user": username,
            "daily_metrics": [],
            "summary": {}
        }

    user_scope_df = df[df["DECLARATIONID"].isin(user_decls)].copy()
    manual_statuses = {"INTERFACE", "COPIED", "COPY", "NEW"}

    daily_summary = defaultdict(lambda: {
        "manual_files_created": 0,
        "automatic_files_created": 0,
        "modification_count": 0,
        "modification_file_ids": set(),
        "total_files_handled": set(),
        "file_creation_times": [],
        "manual_file_ids": [],
        "automatic_file_ids": []
    })

    grouped = user_scope_df.groupby("DECLARATIONID")

    for decl_id, group in grouped:
        group = group.sort_values("HISTORYDATETIME")
        if group.empty:
            continue
        
        user_rows = group[group["USERCODE"] == username]
        if user_rows.empty:
            continue

        first_action_date = user_rows["HISTORYDATETIME"].min().date().isoformat()
        is_manual, is_automatic = False, False

        user_statuses = set(user_rows["HISTORY_STATUS"].tolist())
        if manual_statuses.intersection(user_statuses):
            is_manual = True

        if not is_manual:
            has_batchproc_interface = not group[
                (group["USERCODE"] == "BATCHPROC") & (group["HISTORY_STATUS"] == "INTERFACE")
            ].empty

            if has_batchproc_interface:
                mod_users = group[
                    (group["HISTORY_STATUS"] == "MODIFIED") & (group["USERCODE"] != "BATCHPROC")
                ]["USERCODE"].value_counts()

                if not mod_users.empty and mod_users.index[0] == username:
                    is_automatic = True

        if is_manual:
            daily_summary[first_action_date]["manual_files_created"] += 1
            daily_summary[first_action_date]["total_files_handled"].add(decl_id)
            daily_summary[first_action_date]["manual_file_ids"].append(decl_id)
        elif is_automatic:
            daily_summary[first_action_date]["automatic_files_created"] += 1
            daily_summary[first_action_date]["total_files_handled"].add(decl_id)
            daily_summary[first_action_date]["automatic_file_ids"].append(decl_id)

        mods = group[group["USERCODE"] == username]
        daily_summary[first_action_date]["modification_count"] += len(mods[mods["HISTORY_STATUS"] == "MODIFIED"])
        daily_summary[first_action_date]["total_files_handled"].update(mods["DECLARATIONID"].tolist())
        daily_summary[first_action_date]["modification_file_ids"].update(mods["DECLARATIONID"].tolist())

        # 🆕 File lifecycle logic
        session_start = None
        for _, row in mods.sort_values("HISTORYDATETIME").iterrows():
            if row["HISTORY_STATUS"] == "MODIFIED" and session_start is None:
                session_start = row["HISTORYDATETIME"]
            elif row["HISTORY_STATUS"] == "WRT_ENT" and session_start:
                duration = (row["HISTORYDATETIME"] - session_start).total_seconds() / 3600
                daily_summary[first_action_date]["file_creation_times"].append(duration)
                session_start = None

    # Build daily metrics
    daily_metrics = []
    for date in sorted(daily_summary.keys()):
        data = daily_summary[date]
        avg_creation_time = (sum(data["file_creation_times"]) / len(data["file_creation_times"])) if data["file_creation_times"] else None
        daily_metrics.append({
            "date": date,
            "manual_files_created": data["manual_files_created"],
            "automatic_files_created": data["automatic_files_created"],
            "modification_count": data["modification_count"],
            "modification_file_ids": list(data["modification_file_ids"]),
            "total_files_handled": len(data["total_files_handled"]),
            "avg_creation_time": round(avg_creation_time, 2) if avg_creation_time else None,
            "manual_file_ids": data["manual_file_ids"],
            "automatic_file_ids": data["automatic_file_ids"]
        })

    total_manual = sum(d["manual_files_created"] for d in daily_metrics)
    total_auto = sum(d["automatic_files_created"] for d in daily_metrics)
    total_mods = sum(d["modification_count"] for d in daily_metrics)
    total_handled = sum(d["total_files_handled"] for d in daily_metrics)

    all_creation_times = [t for d in daily_summary.values() for t in d["file_creation_times"]]
    avg_creation_time_total = (sum(all_creation_times) / len(all_creation_times)) if all_creation_times else None

    df_user_summary = user_scope_df[user_scope_df["USERCODE"] == username]
    file_type_counts = df_user_summary["TYPEDECLARATIONSSW"].value_counts().to_dict()
    activity_by_hour = df_user_summary["HISTORYDATETIME"].dt.hour.value_counts().sort_index().to_dict()
    company_specialization = df_user_summary["ACTIVECOMPANY"].value_counts().to_dict()

    most_productive_day = max(daily_metrics, key=lambda d: d["total_files_handled"], default={"date": None})["date"] if daily_metrics else None

    # 🆕 Smart avg per day (only weekdays + at least 1 file created)
    valid_days = [
        d for d in daily_metrics
        if (datetime.strptime(d["date"], "%Y-%m-%d").weekday() < 5) and
        ((d["manual_files_created"] + d["automatic_files_created"]) > 0)
    ]
    total_created = sum(d["manual_files_created"] + d["automatic_files_created"] for d in valid_days)
    avg_files_per_day = round(total_created / len(valid_days), 2) if valid_days else 0

    days_active = len(valid_days)
    modification_file_ids = set()
    for d in daily_metrics:
        modification_file_ids.update(d["modification_file_ids"])
    modifications_per_file = round(total_mods / len(modification_file_ids), 2) if modification_file_ids else 0

    manual_vs_auto_ratio = {
        "manual_percent": round((total_manual / total_handled) * 100, 2) if total_handled else 0,
        "automatic_percent": round((total_auto / total_handled) * 100, 2) if total_handled else 0,
    }

    activity_days = df_user_summary["HISTORYDATETIME"].dt.date.value_counts().to_dict()
    all_days = set((datetime.now() - timedelta(days=i)).date() for i in range(90))
    inactive_days = sorted([d.isoformat() for d in all_days if d not in activity_days])

    hour_with_most_activity = max(activity_by_hour.items(), key=lambda x: x[1], default=(None, None))[0]

    return {
        "user": username,
        "daily_metrics": daily_metrics,
        "summary": {
            "total_manual_files": total_manual,
            "total_automatic_files": total_auto,
            "total_files_handled": total_handled,
            "total_modifications": total_mods,
            "avg_files_per_day": avg_files_per_day,
            "avg_creation_time": round(avg_creation_time_total, 2) if avg_creation_time_total else None,
            "most_productive_day": most_productive_day,
            "file_type_counts": file_type_counts,
            "activity_by_hour": activity_by_hour,
            "company_specialization": company_specialization,
            "days_active": days_active,
            "modifications_per_file": modifications_per_file,
            "manual_vs_auto_ratio": manual_vs_auto_ratio,
            "activity_days": {str(k): int(v) for k, v in activity_days.items()},
            "inactivity_days": inactive_days,
            "hour_with_most_activity": hour_with_most_activity
        }
    }
    
def calculate_all_users_monthly_metrics(df_all):
    """
    Calculate file creation metrics for all users in the last month (30 days)
    Returns summary of files created and daily averages per user
    """
    df = df_all.copy()
    
    # Data preprocessing (same as original function)
    for col in ["USERCREATE", "USERCODE", "HISTORY_STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()
    
    df["HISTORYDATETIME"] = pd.to_datetime(df["HISTORYDATETIME"], errors="coerce", format="mixed")
    df = df.dropna(subset=["HISTORYDATETIME"])
    df["HISTORYDATETIME"] = df["HISTORYDATETIME"].dt.tz_localize(None)
    
    # Filter for last 30 days instead of 90
    cutoff = datetime.now() - timedelta(days=30)
    recent_df = df[df["HISTORYDATETIME"] >= cutoff]
    
    if recent_df.empty:
        return {}
    
    # Get all users who had activity in the last month
    active_users = recent_df["USERCODE"].unique()
    manual_statuses = {"INTERFACE", "COPIED", "COPY", "NEW"}
    
    user_results = {}
    
    for username in active_users:
        # Skip system users
        if username in ["BATCHPROC", "SYSTEM", ""]:
            continue
            
        # Get declarations this user worked on
        user_decls = recent_df[recent_df["USERCODE"] == username]["DECLARATIONID"].unique()
        if len(user_decls) == 0:
            continue
        
        # Get all activity for these declarations
        user_scope_df = df[df["DECLARATIONID"].isin(user_decls)].copy()
        
        # Track daily file creation
        daily_files = defaultdict(lambda: {
            "manual_files": 0,
            "automatic_files": 0,
            "total_files": set()
        })
        
        # Group by declaration to analyze file creation logic
        grouped = user_scope_df.groupby("DECLARATIONID")
        
        for decl_id, group in grouped:
            group = group.sort_values("HISTORYDATETIME")
            if group.empty:
                continue
            
            # Check if user worked on this declaration
            user_rows = group[group["USERCODE"] == username]
            if user_rows.empty:
                continue
            
            # Get the first action date within our 30-day window
            user_actions_in_period = user_rows[user_rows["HISTORYDATETIME"] >= cutoff]
            if user_actions_in_period.empty:
                continue
                
            first_action_date = user_actions_in_period["HISTORYDATETIME"].min().date().isoformat()
            
            # Determine if this is manual or automatic file creation
            is_manual = False
            is_automatic = False
            
            # Check for manual creation (same logic as original)
            user_statuses = set(user_rows["HISTORY_STATUS"].tolist())
            if manual_statuses.intersection(user_statuses):
                is_manual = True
            
            # Check for automatic creation (same logic as original)
            if not is_manual:
                has_batchproc_interface = not group[
                    (group["USERCODE"] == "BATCHPROC") & (group["HISTORY_STATUS"] == "INTERFACE")
                ].empty
                
                if has_batchproc_interface:
                    mod_users = group[
                        (group["HISTORY_STATUS"] == "MODIFIED") & (group["USERCODE"] != "BATCHPROC")
                    ]["USERCODE"].value_counts()
                    
                    if not mod_users.empty and mod_users.index[0] == username:
                        is_automatic = True
            
            # Count the file creation
            if is_manual:
                daily_files[first_action_date]["manual_files"] += 1
                daily_files[first_action_date]["total_files"].add(decl_id)
            elif is_automatic:
                daily_files[first_action_date]["automatic_files"] += 1
                daily_files[first_action_date]["total_files"].add(decl_id)
        
        # Calculate totals and averages
        total_manual = sum(day_data["manual_files"] for day_data in daily_files.values())
        total_automatic = sum(day_data["automatic_files"] for day_data in daily_files.values())
        total_files = total_manual + total_automatic
        
        # Calculate average per day (only for weekdays with file creation activity)
        valid_days = []
        for date_str, day_data in daily_files.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            files_created = day_data["manual_files"] + day_data["automatic_files"]
            
            # Only count weekdays (Monday=0, Sunday=6) with actual file creation
            if date_obj.weekday() < 5 and files_created > 0:
                valid_days.append(files_created)
        
        avg_files_per_day = round(sum(valid_days) / len(valid_days), 2) if valid_days else 0
        days_with_creation = len(valid_days)
        
        user_results[username] = {
            "total_files_created": total_files,
            "manual_files": total_manual,
            "automatic_files": total_automatic,
            "days_with_file_creation": days_with_creation,
            "avg_files_per_active_day": avg_files_per_day,
            "manual_vs_auto_ratio": {
                "manual_percent": round((total_manual / total_files) * 100, 2) if total_files else 0,
                "automatic_percent": round((total_automatic / total_files) * 100, 2) if total_files else 0
            }
        }
    
    return user_results
