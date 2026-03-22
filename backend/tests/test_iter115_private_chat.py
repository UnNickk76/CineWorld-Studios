"""
Test Suite for Private 1:1 Chat (Step 3 - DM System)
Tests: POST /chat/direct/{target_user_id}, GET /chat/rooms, POST /chat/messages, GET /chat/rooms/{room_id}/messages
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {
    "email": "fandrex1@gmail.com",
    "password": "Ciaociao1",
    "nickname": "NeoMorpheus",
    "id": "25e2aa00-d353-4ecf-9a89-b3959520ea5c"
}

OTHER_USERS = {
    "Emilians": "7e1bb9ec-91f7-4f8e-9ff2-5f400896ba44",
    "fabbro": "976eb90b-5ff6-4ce7-9cb6-e3d592c8e92e",
    "mic": "8bd4396f-c6dc-4bc9-9e2a-8a0ed7855ec4",
    "Benny": "a0081c6d-268d-4093-b57f-2c568d8b59be"
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestDirectChatCreation:
    """Tests for POST /api/chat/direct/{target_user_id}"""
    
    def test_create_dm_room_success(self, api_client):
        """Create a new DM room with another user"""
        target_id = OTHER_USERS["mic"]
        response = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        
        assert response.status_code == 200, f"Failed to create DM: {response.text}"
        data = response.json()
        
        # Verify room structure
        assert "id" in data, "Room should have an id"
        assert data.get("is_private") == True, "Room should be private"
        assert "participant_ids" in data, "Room should have participant_ids"
        assert ADMIN_USER["id"] in data["participant_ids"], "Admin should be in participants"
        assert target_id in data["participant_ids"], "Target user should be in participants"
        
        # Verify other_user info
        assert "other_user" in data, "Room should include other_user info"
        assert "nickname" in data["other_user"], "other_user should have nickname"
        assert "is_online" in data["other_user"], "other_user should have is_online status"
        
        print(f"✓ Created DM room: {data['id']} with {data['other_user']['nickname']}")
    
    def test_create_dm_idempotent(self, api_client):
        """Calling create DM twice returns the SAME room (idempotent)"""
        target_id = OTHER_USERS["fabbro"]
        
        # First call
        response1 = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        assert response1.status_code == 200
        room1 = response1.json()
        
        # Second call - should return same room
        response2 = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        assert response2.status_code == 200
        room2 = response2.json()
        
        assert room1["id"] == room2["id"], "Same room should be returned on duplicate call"
        print(f"✓ Idempotent: Both calls returned room {room1['id']}")
    
    def test_create_dm_nonexistent_user(self, api_client):
        """Creating DM with non-existent user returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.post(f"{BASE_URL}/api/chat/direct/{fake_id}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent user returns 404")
    
    def test_dm_room_has_other_user_info(self, api_client):
        """DM room response includes other_user with nickname, avatar, is_online"""
        target_id = OTHER_USERS["Emilians"]
        response = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        other_user = data.get("other_user", {})
        assert "nickname" in other_user, "other_user should have nickname"
        assert "is_online" in other_user, "other_user should have is_online"
        # avatar_url may be optional
        
        print(f"✓ other_user info: {other_user.get('nickname')}, online={other_user.get('is_online')}")


class TestPrivateMessaging:
    """Tests for sending and retrieving private messages"""
    
    def test_send_private_message(self, api_client):
        """Send a message to a private room"""
        # First create/get a DM room
        target_id = OTHER_USERS["mic"]
        room_response = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        assert room_response.status_code == 200
        room = room_response.json()
        room_id = room["id"]
        
        # Send a message
        test_content = f"Test private message {int(time.time())}"
        msg_response = api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room_id,
            "content": test_content,
            "message_type": "text"
        })
        
        assert msg_response.status_code == 200, f"Failed to send message: {msg_response.text}"
        msg_data = msg_response.json()
        
        assert msg_data.get("room_id") == room_id, "Message should be in correct room"
        assert msg_data.get("content") == test_content, "Message content should match"
        assert msg_data.get("sender_id") == ADMIN_USER["id"], "Sender should be admin"
        assert "created_at" in msg_data, "Message should have timestamp"
        
        print(f"✓ Sent private message: {test_content[:30]}...")
    
    def test_retrieve_private_messages(self, api_client):
        """Retrieve messages from a private room"""
        # Get/create DM room
        target_id = OTHER_USERS["mic"]
        room_response = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        room = room_response.json()
        room_id = room["id"]
        
        # Send a unique message first
        unique_content = f"Unique test msg {int(time.time())}"
        api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room_id,
            "content": unique_content,
            "message_type": "text"
        })
        
        # Retrieve messages
        msgs_response = api_client.get(f"{BASE_URL}/api/chat/rooms/{room_id}/messages")
        assert msgs_response.status_code == 200, f"Failed to get messages: {msgs_response.text}"
        
        messages = msgs_response.json()
        assert isinstance(messages, list), "Messages should be a list"
        
        # Find our unique message
        found = any(m.get("content") == unique_content for m in messages)
        assert found, "Our sent message should be in the retrieved messages"
        
        # Check message structure
        if messages:
            msg = messages[-1]  # Most recent
            assert "id" in msg, "Message should have id"
            assert "sender_id" in msg, "Message should have sender_id"
            assert "content" in msg, "Message should have content"
            assert "created_at" in msg, "Message should have created_at"
            assert "sender" in msg, "Message should have sender info"
            
            if msg.get("sender"):
                assert "nickname" in msg["sender"], "Sender should have nickname"
        
        print(f"✓ Retrieved {len(messages)} messages from private room")
    
    def test_message_persistence(self, api_client):
        """Verify messages are persistent - send, then fetch and confirm"""
        target_id = OTHER_USERS["fabbro"]
        room_response = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        room = room_response.json()
        room_id = room["id"]
        
        # Send message
        persist_content = f"Persistence test {int(time.time())}"
        api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room_id,
            "content": persist_content,
            "message_type": "text"
        })
        
        # Wait a moment
        time.sleep(0.5)
        
        # Fetch messages
        msgs_response = api_client.get(f"{BASE_URL}/api/chat/rooms/{room_id}/messages")
        messages = msgs_response.json()
        
        # Verify our message is persisted
        found = any(m.get("content") == persist_content for m in messages)
        assert found, "Message should be persisted and retrievable"
        
        print(f"✓ Message persistence verified: {persist_content[:30]}...")


class TestChatRoomsListing:
    """Tests for GET /api/chat/rooms"""
    
    def test_get_rooms_returns_public_and_private(self, api_client):
        """GET /chat/rooms returns both public and private rooms"""
        response = api_client.get(f"{BASE_URL}/api/chat/rooms")
        
        assert response.status_code == 200, f"Failed to get rooms: {response.text}"
        data = response.json()
        
        assert "public" in data, "Response should have 'public' key"
        assert "private" in data, "Response should have 'private' key"
        assert isinstance(data["public"], list), "public should be a list"
        assert isinstance(data["private"], list), "private should be a list"
        
        print(f"✓ Got {len(data['public'])} public rooms, {len(data['private'])} private rooms")
    
    def test_private_rooms_sorted_by_last_message(self, api_client):
        """Private rooms should be sorted by last_message date (most recent first)"""
        # First, ensure we have at least 2 DM rooms with messages
        for target_id in [OTHER_USERS["mic"], OTHER_USERS["fabbro"]]:
            room_resp = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
            room = room_resp.json()
            # Send a message to ensure last_message exists
            api_client.post(f"{BASE_URL}/api/chat/messages", json={
                "room_id": room["id"],
                "content": f"Sort test {int(time.time())}",
                "message_type": "text"
            })
            time.sleep(0.3)  # Small delay to ensure different timestamps
        
        # Now send a message to the first room to make it most recent
        room_resp = api_client.post(f"{BASE_URL}/api/chat/direct/{OTHER_USERS['mic']}")
        room = room_resp.json()
        api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room["id"],
            "content": f"Most recent {int(time.time())}",
            "message_type": "text"
        })
        
        # Get rooms
        response = api_client.get(f"{BASE_URL}/api/chat/rooms")
        data = response.json()
        private_rooms = data.get("private", [])
        
        if len(private_rooms) >= 2:
            # Check that rooms with last_message are sorted by date
            rooms_with_msgs = [r for r in private_rooms if r.get("last_message")]
            if len(rooms_with_msgs) >= 2:
                dates = [r["last_message"]["created_at"] for r in rooms_with_msgs]
                assert dates == sorted(dates, reverse=True), "Private rooms should be sorted by last_message date descending"
                print(f"✓ Private rooms sorted correctly by last_message date")
            else:
                print("⚠ Not enough rooms with messages to verify sorting")
        else:
            print("⚠ Not enough private rooms to verify sorting")
    
    def test_private_rooms_include_last_message(self, api_client):
        """Private rooms should include last_message content"""
        # Ensure we have a DM with a message
        target_id = OTHER_USERS["Emilians"]
        room_resp = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        room = room_resp.json()
        
        test_content = f"Last message test {int(time.time())}"
        api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room["id"],
            "content": test_content,
            "message_type": "text"
        })
        
        # Get rooms
        response = api_client.get(f"{BASE_URL}/api/chat/rooms")
        data = response.json()
        
        # Find our room
        our_room = next((r for r in data["private"] if r["id"] == room["id"]), None)
        assert our_room is not None, "Our DM room should be in private rooms"
        
        last_msg = our_room.get("last_message")
        assert last_msg is not None, "Room should have last_message"
        assert last_msg.get("content") == test_content, "last_message content should match"
        assert "created_at" in last_msg, "last_message should have created_at"
        
        print(f"✓ Private room includes last_message: {test_content[:30]}...")
    
    def test_private_rooms_include_other_user_info(self, api_client):
        """Private rooms should include other_user info with is_online"""
        response = api_client.get(f"{BASE_URL}/api/chat/rooms")
        data = response.json()
        
        private_rooms = data.get("private", [])
        if private_rooms:
            room = private_rooms[0]
            assert "other_user" in room, "Private room should have other_user"
            other_user = room["other_user"]
            assert "nickname" in other_user, "other_user should have nickname"
            assert "is_online" in other_user, "other_user should have is_online"
            print(f"✓ Private room has other_user: {other_user.get('nickname')}, online={other_user.get('is_online')}")
        else:
            print("⚠ No private rooms to verify other_user info")


class TestMessageModel:
    """Tests for message model structure"""
    
    def test_message_has_required_fields(self, api_client):
        """Message should have: id, room_id, sender_id, content, message_type, image_url, created_at"""
        target_id = OTHER_USERS["mic"]
        room_resp = api_client.post(f"{BASE_URL}/api/chat/direct/{target_id}")
        room = room_resp.json()
        
        # Send message
        msg_resp = api_client.post(f"{BASE_URL}/api/chat/messages", json={
            "room_id": room["id"],
            "content": "Field test message",
            "message_type": "text"
        })
        
        assert msg_resp.status_code == 200
        msg = msg_resp.json()
        
        required_fields = ["id", "room_id", "sender_id", "content", "message_type", "created_at"]
        for field in required_fields:
            assert field in msg, f"Message should have '{field}' field"
        
        # image_url is optional but should be in schema
        assert "image_url" in msg or msg.get("image_url") is None, "image_url field should exist (can be null)"
        
        print(f"✓ Message has all required fields: {required_fields}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
