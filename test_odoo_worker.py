import requests
import json
import time

URL = "http://localhost:7071/api/OdooService"

def test_feature(name, payload):
    print(f"\n--- Testing Feature: {name} ---")
    try:
        resp = requests.post(URL, json=payload)
        print(f"🔢 Status: {resp.status_code}")
        print(f"📦 Response: {resp.text}")
        return resp.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_capability_test():
    print("🚀 Starting OdooService Final Verification...")

    # 1. CREATE WITH CUSTOM PRIORITY
    create_res = test_feature("CREATE_TASK (Priority: Low)", {
        "command": "CREATE_TASK",
        "project_name": "Interface",
        "task_name": "Donna Final Test - Stage & Msg",
        "description": "Technical check for custom stages and messaging.",
        "priority": "Low"
    })
    
    if not create_res or not create_res.get("task_id"):
        return

    task_id = create_res["task_id"]

    # 2. MOVE THROUGH CUSTOM STAGES
    stages = ["Anas", "Taha", "Anas adapting"]
    for stage in stages:
        test_feature(f"MOVE_STAGE to {stage}", {
            "command": "MOVE_STAGE",
            "task_id": task_id,
            "stage_name": stage
        })
        time.sleep(1) # Visual pause

    # 3. ADD INTERNAL COMMENT
    test_feature("ADD_COMMENT (Internal Note)", {
        "command": "ADD_COMMENT",
        "task_id": task_id,
        "comment": "This is an <i>internal</i> log note only."
    })

    # 4. SEND EXTERNAL MESSAGE
    test_feature("SEND_MESSAGE (To Followers)", {
        "command": "SEND_MESSAGE",
        "task_id": task_id,
        "message": "<b>Donna Notification:</b> The project has successfully moved through Anas, Taha, and Anas adapting stages."
    })

if __name__ == "__main__":
    run_capability_test()
