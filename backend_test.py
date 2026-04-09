#!/usr/bin/env python3
"""
Backend API Testing for CineWorld Studio's
Tests all major API endpoints and functionality
"""

import requests
import sys
import json
import time
from datetime import datetime

class CineWorldAPITester:
    def __init__(self):
        self.base_url = "https://contest-fix-1.preview.emergentagent.com/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}: {details}")

    def make_request(self, method, endpoint, data=None, expect_status=200):
        """Make API request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expect_status
            response_data = {}
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text}

            return success, response_data, response.status_code

        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_user_registration(self):
        """Test user registration endpoint"""
        test_email = f"test_{int(time.time())}@cineworld.com"
        register_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "nickname": "TestProducer",
            "production_house_name": "Test Studios",
            "owner_name": "Test Owner",
            "language": "en"
        }

        success, response, status = self.make_request('POST', '/auth/register', register_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            self.log_result("User Registration", True, f"User created with ID: {self.user_data.get('id')}")
        else:
            self.log_result("User Registration", False, f"Status: {status}, Response: {response}")

        return success

    def test_user_login(self):
        """Test user login endpoint"""
        if not self.user_data:
            self.log_result("User Login", False, "No user data available for login test")
            return False

        login_data = {
            "email": self.user_data['email'],
            "password": "TestPassword123!"
        }

        success, response, status = self.make_request('POST', '/auth/login', login_data, 200)
        
        if success and 'access_token' in response:
            self.log_result("User Login", True, f"Login successful")
        else:
            self.log_result("User Login", False, f"Status: {status}, Response: {response}")

        return success

    def test_get_user_profile(self):
        """Test get current user profile"""
        success, response, status = self.make_request('GET', '/auth/me', None, 200)
        
        if success and 'id' in response:
            self.log_result("Get User Profile", True, f"Profile retrieved for user: {response.get('nickname')}")
        else:
            self.log_result("Get User Profile", False, f"Status: {status}, Response: {response}")

        return success

    def test_get_translations(self):
        """Test translations endpoint"""
        languages = ['en', 'it', 'es', 'fr', 'de']
        
        for lang in languages:
            success, response, status = self.make_request('GET', f'/translations/{lang}', None, 200)
            
            if success and isinstance(response, dict) and 'welcome' in response:
                self.log_result(f"Translations - {lang.upper()}", True, f"Translation keys loaded: {len(response)} keys")
            else:
                self.log_result(f"Translations - {lang.upper()}", False, f"Status: {status}")

    def test_get_game_data(self):
        """Test game data endpoints (sponsors, locations, equipment)"""
        endpoints = [
            ('/sponsors', 'Sponsors'),
            ('/locations', 'Locations'),
            ('/equipment', 'Equipment'),
            ('/countries', 'Countries')
        ]

        for endpoint, name in endpoints:
            success, response, status = self.make_request('GET', endpoint, None, 200)
            
            if success and isinstance(response, (list, dict)):
                count = len(response) if isinstance(response, list) else len(response.keys())
                self.log_result(f"Get {name}", True, f"{count} items loaded")
            else:
                self.log_result(f"Get {name}", False, f"Status: {status}")

    def test_get_people(self):
        """Test people endpoints (actors, directors, screenwriters)"""
        people_types = ['actors', 'directors', 'screenwriters']
        
        for people_type in people_types:
            success, response, status = self.make_request('GET', f'/{people_type}', None, 200)
            
            if success and people_type in response:
                count = len(response[people_type])
                self.log_result(f"Get {people_type.title()}", True, f"{count} people loaded")
            else:
                self.log_result(f"Get {people_type.title()}", False, f"Status: {status}")

    def test_create_film(self):
        """Test film creation endpoint"""
        if not self.token:
            self.log_result("Create Film", False, "No auth token available")
            return False

        film_data = {
            "title": "Test Film",
            "genre": "action",
            "release_date": "2025-03-01T00:00:00Z",
            "weeks_in_theater": 4,
            "sponsor_id": None,
            "equipment_package": "Standard",
            "locations": ["Hollywood Studio"],
            "location_days": {"Hollywood Studio": 7},
            "screenwriter_id": "test-screenwriter-id",
            "director_id": "test-director-id",
            "actors": [{"actor_id": "test-actor-id", "role": "Lead"}],
            "extras_count": 50,
            "extras_cost": 50000,
            "screenplay": "Test screenplay content",
            "screenplay_source": "manual",
            "poster_url": "",
            "poster_prompt": "",
            "ad_duration_seconds": 0,
            "ad_revenue": 0
        }

        # First get real IDs for people
        actors_success, actors_response, _ = self.make_request('GET', '/actors', None, 200)
        directors_success, directors_response, _ = self.make_request('GET', '/directors', None, 200)
        screenwriters_success, screenwriters_response, _ = self.make_request('GET', '/screenwriters', None, 200)

        if actors_success and directors_success and screenwriters_success:
            film_data["screenwriter_id"] = screenwriters_response["screenwriters"][0]["id"]
            film_data["director_id"] = directors_response["directors"][0]["id"]
            film_data["actors"] = [{"actor_id": actors_response["actors"][0]["id"], "role": "Lead"}]

        success, response, status = self.make_request('POST', '/films', film_data, 200)
        
        if success and 'id' in response:
            self.film_id = response['id']
            self.log_result("Create Film", True, f"Film created with ID: {response.get('id')}")
        else:
            self.log_result("Create Film", False, f"Status: {status}, Response: {response}")

        return success

    def test_get_my_films(self):
        """Test get user's films"""
        success, response, status = self.make_request('GET', '/films/my', None, 200)
        
        if success and isinstance(response, list):
            self.log_result("Get My Films", True, f"{len(response)} films found")
        else:
            self.log_result("Get My Films", False, f"Status: {status}")

        return success

    def test_social_feed(self):
        """Test social feed endpoint"""
        success, response, status = self.make_request('GET', '/films/social/feed', None, 200)
        
        if success and 'films' in response:
            self.log_result("Social Feed", True, f"{len(response['films'])} films in feed")
        else:
            self.log_result("Social Feed", False, f"Status: {status}")

        return success

    def test_statistics(self):
        """Test statistics endpoints"""
        # Global statistics
        success, response, status = self.make_request('GET', '/statistics/global', None, 200)
        if success and 'total_films' in response:
            self.log_result("Global Statistics", True, f"Global stats loaded")
        else:
            self.log_result("Global Statistics", False, f"Status: {status}")

        # Personal statistics  
        success, response, status = self.make_request('GET', '/statistics/my', None, 200)
        if success and 'total_films' in response:
            self.log_result("Personal Statistics", True, f"Personal stats loaded")
        else:
            self.log_result("Personal Statistics", False, f"Status: {status}")

    def test_chat_system(self):
        """Test chat system endpoints"""
        # Get chat rooms
        success, response, status = self.make_request('GET', '/chat/rooms', None, 200)
        if success and 'public' in response:
            self.log_result("Get Chat Rooms", True, f"{len(response['public'])} public rooms found")
        else:
            self.log_result("Get Chat Rooms", False, f"Status: {status}")

        # Get messages for a room (assuming default room exists)
        if success and len(response.get('public', [])) > 0:
            room_id = response['public'][0]['id']
            success, response, status = self.make_request('GET', f'/chat/rooms/{room_id}/messages', None, 200)
            if success:
                self.log_result("Get Chat Messages", True, f"Messages retrieved for room")
            else:
                self.log_result("Get Chat Messages", False, f"Status: {status}")

    def test_ai_endpoints(self):
        """Test AI integration endpoints"""
        # Test screenplay generation
        screenplay_data = {
            "genre": "action",
            "title": "Test AI Film",
            "language": "en",
            "tone": "dramatic",
            "length": "medium"
        }
        
        success, response, status = self.make_request('POST', '/ai/screenplay', screenplay_data, 200)
        if success and 'screenplay' in response:
            self.log_result("AI Screenplay Generation", True, f"Screenplay generated")
        else:
            self.log_result("AI Screenplay Generation", False, f"Status: {status}")

        # Test translation
        translation_data = {
            "text": "Hello World",
            "source_lang": "en",
            "target_lang": "it"
        }
        
        success, response, status = self.make_request('POST', '/ai/translate', translation_data, 200)
        if success and 'translated_text' in response:
            self.log_result("AI Translation", True, f"Translation completed")
        else:
            self.log_result("AI Translation", False, f"Status: {status}")

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🎬 Starting CineWorld Studio's Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 50)

        # Authentication tests
        if self.test_user_registration():
            self.test_user_login()
            self.test_get_user_profile()

        # Core data tests
        self.test_get_translations()
        self.test_get_game_data()
        self.test_get_people()

        # Film management tests
        if self.token:
            self.test_create_film()
            self.test_get_my_films()
            self.test_social_feed()
            self.test_statistics()
            self.test_chat_system()
            self.test_ai_endpoints()

        # Results summary
        print("=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")

        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")

        return success_rate >= 80  # Consider 80%+ as passing

def main():
    tester = CineWorldAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())