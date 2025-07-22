#-----------------------------------------------------------------------------
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import pandas as pd

def count_user_file_creations_last_10_days(df):
    import_users = [
       'FADWA.ERRAZIKI', 'AYOUB.SOURISTE',  'AYMANE.BERRIOUA', 'SANA.IDRISSI', 'AMINA.SAISS','KHADIJA.OUFKIR', 'ZOHRA.HMOUDOU', 'SIMO.ONSI', 'YOUSSEF.ASSABIR',  'ABOULHASSAN.AMINA'
'MEHDI.OUAZIR', 'OUMAIMA.EL.OUTMANI', 'HAMZA.ALLALI',  'MUSTAPHA.BOUJALA', 'HIND.EZZAOUI'
    ]

    export_users = [
        'IKRAM.OULHIANE', 'MOURAD.ELBAHAZ', 'MOHSINE.SABIL', 'AYA.HANNI',  'ZAHIRA.OUHADDA', 'CHAIMAAE.EJJARI',  'HAFIDA.BOOHADDOU', 'KHADIJA.HICHAMI', 'FATIMA.ZAHRA.BOUGSIM'
    ]

    users = import_users + export_users

    # clean
    for col in ["USERCREATE", "USERCODE", "HISTORY_STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    df["HISTORYDATETIME"] = pd.to_datetime(df["HISTORYDATETIME"], errors="coerce", format="mixed")
    df = df.dropna(subset=["HISTORYDATETIME"])
    df["HISTORYDATETIME"] = df["HISTORYDATETIME"].dt.tz_localize(None)

    # working days
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

        # get declarations the user was involved in during last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        recent_df = df[df["HISTORYDATETIME"] >= cutoff]
        user_decls = recent_df[recent_df["USERCODE"] == user]["DECLARATIONID"].unique()

        for decl_id in user_decls:
            decl_df = df[df["DECLARATIONID"] == decl_id].sort_values("HISTORYDATETIME")
            if decl_df.empty:
                continue

            first_row = decl_df.iloc[0]
            first_user = first_row["USERCODE"]
            first_status = first_row["HISTORY_STATUS"]

            is_manual = (first_user == user) and (first_status in ["NEW", "COPIED"])
            is_auto = (first_user == "BATCHPROC") and (user in decl_df["USERCODE"].values)

            if is_manual or is_auto:
                file_date = first_row["HISTORYDATETIME"].date()
                if file_date in working_days:
                    key = file_date.strftime("%d/%m")
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

        mods = group[(group["USERCODE"] == username) & (group["HISTORY_STATUS"] == "MODIFIED")]
        daily_summary[first_action_date]["modification_count"] += len(mods)
        daily_summary[first_action_date]["total_files_handled"].update(mods["DECLARATIONID"].tolist())
        daily_summary[first_action_date]["modification_file_ids"].update(mods["DECLARATIONID"].tolist())

        if not mods.empty:
            duration_hours = (mods["HISTORYDATETIME"].max() - mods["HISTORYDATETIME"].min()).total_seconds() / 3600
            daily_summary[first_action_date]["file_creation_times"].append(duration_hours)

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
    avg_files_per_day = round(total_handled / len(daily_metrics), 2) if daily_metrics else 0

    # Extra concepts
    days_active = len(daily_metrics)
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
