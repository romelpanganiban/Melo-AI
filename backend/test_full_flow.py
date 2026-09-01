"""End-to-end test for register → login → create session → fetch sessions flow."""

import json
import time
import uuid
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000"


def test_full_flow():
    """Test the complete auth and session workflow."""
    import requests

    test_email = f"flowtest-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "correct horse battery staple"

    print("\n" + "=" * 70)
    print("FULL FLOW TEST: Register → Login → Create Session → Fetch Sessions")
    print("=" * 70)

    # Step 1: Register
    print(f"\n[1/5] Registering user: {test_email}")
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": test_email, "password": test_password},
            timeout=10,
        )
        print(f"   Status: {response.status_code}")
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            return False
        reg_data = response.json()
        print(f"   ✓ User registered")
        print(f"   Response keys: {list(reg_data.keys())}")
        user_id = reg_data.get('user', {}).get('id') or reg_data.get('id')
        workspace_id_reg = reg_data.get('workspace', {}).get('id') or reg_data.get('workspace_id')
        print(f"   - User ID: {user_id}")
        print(f"   - Platform role: {reg_data.get('user', {}).get('platform_role') or reg_data.get('platform_role')}")
        print(f"   - Default workspace ID: {workspace_id_reg}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Step 2: Login
    print(f"\n[2/5] Logging in with {test_email}")
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": test_email, "password": test_password},
            timeout=10,
        )
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False
        login_data = response.json()
        print(f"   Response keys: {list(login_data.keys())}")
        access_token = login_data.get("access_token")
        workspace_id = login_data.get('workspace', {}).get('id') or login_data.get('workspace_id')
        print(f"   ✓ Login successful")
        print(f"   - Token received: {access_token[:20]}...")
        print(f"   - Workspace ID: {workspace_id}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Step 3: Create Session
    print(f"\n[3/5] Creating a new session")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Workspace-ID": workspace_id,
        }
        response = requests.post(
            f"{API_URL}/sessions",
            headers=headers,
            timeout=10,
        )
        print(f"   Status: {response.status_code}")
        if response.status_code not in [200, 201]:
            print(f"   Error: {response.text}")
            return False
        session_data = response.json()
        session_id = session_data.get("id")
        print(f"   ✓ Session created")
        print(f"   - Session ID: {session_id}")
        print(f"   - Title: {session_data.get('title')}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Step 4: Fetch Sessions
    print(f"\n[4/5] Fetching all sessions")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Workspace-ID": workspace_id,
        }
        response = requests.get(
            f"{API_URL}/sessions",
            headers=headers,
            timeout=10,
        )
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False
        sessions_data = response.json()
        sessions = sessions_data.get("sessions", [])
        print(f"   ✓ Sessions fetched")
        print(f"   - Total sessions: {len(sessions)}")
        for i, sess in enumerate(sessions, 1):
            print(f"     {i}. {sess.get('title')} (ID: {sess.get('id')})")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Step 5: Verify the created session is in the list
    print(f"\n[5/5] Verifying session {session_id} is in fetched list")
    try:
        session_found = any(s.get('id') == session_id for s in sessions)
        if not session_found:
            print(f"   ✗ Session not found in list")
            return False
        print(f"   ✓ Session verified in list")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ FULL FLOW TEST PASSED")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    try:
        success = test_full_flow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
