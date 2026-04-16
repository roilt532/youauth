#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class RedlineStudioAPITester:
    def __init__(self, base_url="https://tube-optimizer-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_job_id = None
        self.created_template_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if endpoint == "jobs" and method == "POST" and 'id' in response_data:
                        self.created_job_id = response_data['id']
                        print(f"   Created job ID: {self.created_job_id}")
                    elif endpoint == "templates" and method == "POST" and 'id' in response_data:
                        self.created_template_id = response_data['id']
                        print(f"   Created template ID: {self.created_template_id}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        success, data = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            required_fields = ['total_jobs', 'total_runs', 'success_rate', 'quota_used', 'recent_runs']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print(f"   📊 Stats: {data.get('total_jobs', 0)} jobs, {data.get('success_rate', 0)}% success rate")
        return success

    def test_create_job(self):
        """Test job creation"""
        job_data = {
            "title": "Test Roblox Video",
            "topic": "Los mejores trucos de Roblox que nadie conoce",
            "content_type": "roblox",
            "language": "bilingual",
            "format": "short",
            "made_for_kids": True,
            "priority": 5,
            "custom_prompt": "Enfócate en contenido viral para niños"
        }
        
        success, data = self.run_test(
            "Create Job",
            "POST",
            "jobs",
            200,
            data=job_data
        )
        return success

    def test_get_jobs(self):
        """Test getting jobs list"""
        success, data = self.run_test(
            "Get Jobs List",
            "GET",
            "jobs",
            200
        )
        if success and 'jobs' in data:
            print(f"   📋 Found {len(data['jobs'])} jobs")
        return success

    def test_get_job_by_id(self):
        """Test getting specific job by ID"""
        if not self.created_job_id:
            print("⚠️  Skipping job by ID test - no job created")
            return True
            
        success, data = self.run_test(
            "Get Job by ID",
            "GET",
            f"jobs/{self.created_job_id}",
            200
        )
        return success

    def test_run_job(self):
        """Test running a job (pipeline execution)"""
        if not self.created_job_id:
            print("⚠️  Skipping job run test - no job created")
            return True
            
        success, data = self.run_test(
            "Run Job Pipeline",
            "POST",
            f"jobs/{self.created_job_id}/run",
            200
        )
        if success and 'run_id' in data:
            print(f"   🚀 Pipeline started with run ID: {data['run_id']}")
        return success

    def test_create_template(self):
        """Test template creation"""
        template_data = {
            "name": "Roblox Viral ES",
            "content_type": "roblox",
            "hook_style": "surprise",
            "language": "bilingual",
            "tts_voice": "standard",
            "tags": ["roblox", "niños", "viral", "gaming"],
            "description": "Template para videos virales de Roblox en español",
            "custom_prompt": "Crea contenido emocionante y apropiado para niños"
        }
        
        success, data = self.run_test(
            "Create Template",
            "POST",
            "templates",
            200,
            data=template_data
        )
        return success

    def test_get_templates(self):
        """Test getting templates list"""
        success, data = self.run_test(
            "Get Templates List",
            "GET",
            "templates",
            200
        )
        if success and 'templates' in data:
            print(f"   📝 Found {len(data['templates'])} templates")
        return success

    def test_get_settings(self):
        """Test getting settings"""
        success, data = self.run_test(
            "Get Settings",
            "GET",
            "settings",
            200
        )
        if success:
            print(f"   ⚙️  YouTube connected: {data.get('youtube_connected', False)}")
        return success

    def test_update_settings(self):
        """Test updating settings"""
        settings_data = {
            "posting_window_start": "16:00",
            "posting_window_end": "21:00",
            "max_daily_uploads": 2,
            "anti_detection_enabled": True,
            "made_for_kids_default": True
        }
        
        success, data = self.run_test(
            "Update Settings",
            "PUT",
            "settings",
            200,
            data=settings_data
        )
        return success

    def test_get_runs(self):
        """Test getting runs list"""
        success, data = self.run_test(
            "Get Runs List",
            "GET",
            "runs",
            200
        )
        if success and 'runs' in data:
            print(f"   🏃 Found {len(data['runs'])} runs")
        return success

    def test_pipeline_status(self):
        """Test pipeline status"""
        success, data = self.run_test(
            "Pipeline Status",
            "GET",
            "pipeline/status",
            200
        )
        if success:
            print(f"   🔧 Pipeline active: {data.get('active', False)}")
        return success

    def test_analytics_channel(self):
        """Test channel analytics"""
        success, data = self.run_test(
            "Channel Analytics",
            "GET",
            "analytics/channel",
            200
        )
        if success:
            print(f"   📈 YouTube connected: {data.get('connected', False)}")
        return success

    def test_analytics_run_history(self):
        """Test run history analytics"""
        success, data = self.run_test(
            "Run History Analytics",
            "GET",
            "analytics/run-history",
            200
        )
        if success and 'history' in data:
            print(f"   📊 History entries: {len(data['history'])}")
        return success

    def test_health_endpoint(self):
        """Test health endpoint"""
        success, data = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success

    def cleanup_test_data(self):
        """Clean up created test data"""
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete created job
        if self.created_job_id:
            try:
                success, _ = self.run_test(
                    "Delete Test Job",
                    "DELETE",
                    f"jobs/{self.created_job_id}",
                    200
                )
                if success:
                    print(f"   ✅ Deleted job {self.created_job_id}")
            except:
                print(f"   ⚠️  Could not delete job {self.created_job_id}")

        # Delete created template
        if self.created_template_id:
            try:
                success, _ = self.run_test(
                    "Delete Test Template",
                    "DELETE",
                    f"templates/{self.created_template_id}",
                    200
                )
                if success:
                    print(f"   ✅ Deleted template {self.created_template_id}")
            except:
                print(f"   ⚠️  Could not delete template {self.created_template_id}")

def main():
    print("🎬 Redline Studio API Testing Suite")
    print("=" * 50)
    
    tester = RedlineStudioAPITester()
    
    # Core API tests
    tests = [
        tester.test_health_endpoint,
        tester.test_dashboard_stats,
        tester.test_get_settings,
        tester.test_update_settings,
        tester.test_get_jobs,
        tester.test_create_job,
        tester.test_get_job_by_id,
        tester.test_run_job,
        tester.test_get_templates,
        tester.test_create_template,
        tester.test_get_runs,
        tester.test_pipeline_status,
        tester.test_analytics_channel,
        tester.test_analytics_run_history,
    ]
    
    # Run all tests
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Cleanup
    tester.cleanup_test_data()
    
    # Print results
    print(f"\n📊 Test Results:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {round(tester.tests_passed / tester.tests_run * 100, 1)}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())