#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for СтолицаЗдоровья Medical Inventory Management System
Tests all CRUD operations, dashboard stats, search functionality, and alerts system
"""

import requests
import json
import uuid
from datetime import datetime, date, timedelta
import sys

# Backend URL from frontend environment
BACKEND_URL = "https://healthcap-inventory.preview.emergentagent.com/api"

class InventoryAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.created_items = []  # Track created items for cleanup
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name, success, message=""):
        """Log test result"""
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(f"{self.base_url.replace('/api', '')}/")
            if response.status_code == 200:
                data = response.json()
                if "СтолицаЗдоровья" in data.get("message", ""):
                    self.log_result("Root Endpoint", True, "Russian text working")
                else:
                    self.log_result("Root Endpoint", False, f"Unexpected message: {data}")
            else:
                self.log_result("Root Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Root Endpoint", False, f"Exception: {str(e)}")
    
    def create_test_inventory_items(self):
        """Create test inventory items with Russian text and various scenarios"""
        test_items = [
            {
                "name": "Парацетамол 500мг",
                "category": "medication",
                "quantity": 150,
                "unit": "шт",
                "manufacturer": "Фармстандарт",
                "batch_number": "PAR2024001",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
                "cost_per_unit": 12.50,
                "supplier": "МедФарм ООО",
                "location": "Аптека-1, Полка А-3",
                "description": "Жаропонижающее и обезболивающее средство",
                "min_quantity_threshold": 50
            },
            {
                "name": "Шприцы одноразовые 5мл",
                "category": "equipment",
                "quantity": 8,  # Low stock
                "unit": "шт",
                "manufacturer": "МедТех",
                "batch_number": "SYR2024002",
                "cost_per_unit": 15.00,
                "supplier": "МедОборудование",
                "location": "Склад-2, Ящик Б-1",
                "description": "Стерильные одноразовые шприцы",
                "min_quantity_threshold": 20
            },
            {
                "name": "Бинт эластичный",
                "category": "consumable",
                "quantity": 25,
                "unit": "шт",
                "manufacturer": "МедТекстиль",
                "expiry_date": (date.today() - timedelta(days=10)).isoformat(),  # Expired
                "cost_per_unit": 45.00,
                "supplier": "МедСнаб",
                "location": "Перевязочная",
                "description": "Эластичный бинт для фиксации",
                "min_quantity_threshold": 10
            },
            {
                "name": "Антибиотик Амоксициллин",
                "category": "medication", 
                "quantity": 30,
                "unit": "шт",
                "manufacturer": "Биосинтез",
                "batch_number": "AMX2024003",
                "expiry_date": (date.today() + timedelta(days=15)).isoformat(),  # Expiring soon
                "cost_per_unit": 85.00,
                "supplier": "ФармДистрибьюция",
                "location": "Холодильник-1",
                "description": "Антибактериальный препарат широкого спектра",
                "min_quantity_threshold": 15
            },
            {
                "name": "Перчатки латексные",
                "category": "consumable",
                "quantity": 0,  # Out of stock
                "unit": "пар",
                "manufacturer": "ЛатексПро",
                "cost_per_unit": 8.50,
                "supplier": "МедЗащита",
                "location": "Склад-1",
                "description": "Стерильные латексные перчатки",
                "min_quantity_threshold": 100
            }
        ]
        
        print("\n🧪 Creating test inventory items...")
        for item_data in test_items:
            try:
                response = requests.post(f"{self.base_url}/inventory", json=item_data)
                if response.status_code == 200:
                    created_item = response.json()
                    self.created_items.append(created_item["id"])
                    self.log_result(f"Create Item: {item_data['name']}", True, f"ID: {created_item['id']}")
                else:
                    self.log_result(f"Create Item: {item_data['name']}", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_result(f"Create Item: {item_data['name']}", False, f"Exception: {str(e)}")
    
    def test_inventory_crud(self):
        """Test CRUD operations"""
        print("\n🔧 Testing CRUD Operations...")
        
        # Test GET all inventory
        try:
            response = requests.get(f"{self.base_url}/inventory")
            if response.status_code == 200:
                items = response.json()
                if len(items) >= len(self.created_items):
                    self.log_result("GET All Inventory", True, f"Retrieved {len(items)} items")
                    
                    # Check if Russian text is preserved
                    russian_items = [item for item in items if any(ord(char) > 127 for char in item.get('name', ''))]
                    if russian_items:
                        self.log_result("Russian Text Support", True, f"Found {len(russian_items)} items with Russian text")
                    else:
                        self.log_result("Russian Text Support", False, "No Russian text found in items")
                else:
                    self.log_result("GET All Inventory", False, f"Expected at least {len(self.created_items)} items, got {len(items)}")
            else:
                self.log_result("GET All Inventory", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GET All Inventory", False, f"Exception: {str(e)}")
        
        # Test GET specific item
        if self.created_items:
            try:
                item_id = self.created_items[0]
                response = requests.get(f"{self.base_url}/inventory/{item_id}")
                if response.status_code == 200:
                    item = response.json()
                    self.log_result("GET Specific Item", True, f"Retrieved item: {item.get('name', 'Unknown')}")
                else:
                    self.log_result("GET Specific Item", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("GET Specific Item", False, f"Exception: {str(e)}")
        
        # Test UPDATE item
        if self.created_items:
            try:
                item_id = self.created_items[0]
                update_data = {
                    "quantity": 200,
                    "description": "Обновленное описание препарата"
                }
                response = requests.put(f"{self.base_url}/inventory/{item_id}", json=update_data)
                if response.status_code == 200:
                    updated_item = response.json()
                    if updated_item["quantity"] == 200:
                        self.log_result("UPDATE Item", True, f"Updated quantity to {updated_item['quantity']}")
                    else:
                        self.log_result("UPDATE Item", False, f"Quantity not updated correctly")
                else:
                    self.log_result("UPDATE Item", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("UPDATE Item", False, f"Exception: {str(e)}")
    
    def test_filtering(self):
        """Test filtering by category and status"""
        print("\n🔍 Testing Filtering...")
        
        # Test filter by category
        categories = ["medication", "equipment", "consumable"]
        for category in categories:
            try:
                response = requests.get(f"{self.base_url}/inventory?category={category}")
                if response.status_code == 200:
                    items = response.json()
                    if all(item["category"] == category for item in items):
                        self.log_result(f"Filter by Category: {category}", True, f"Found {len(items)} items")
                    else:
                        self.log_result(f"Filter by Category: {category}", False, "Items with wrong category returned")
                else:
                    self.log_result(f"Filter by Category: {category}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Filter by Category: {category}", False, f"Exception: {str(e)}")
        
        # Test filter by status
        statuses = ["active", "low_stock", "expired", "out_of_stock"]
        for status in statuses:
            try:
                response = requests.get(f"{self.base_url}/inventory?status={status}")
                if response.status_code == 200:
                    items = response.json()
                    self.log_result(f"Filter by Status: {status}", True, f"Found {len(items)} items")
                else:
                    self.log_result(f"Filter by Status: {status}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Filter by Status: {status}", False, f"Exception: {str(e)}")
    
    def test_search_functionality(self):
        """Test search functionality"""
        print("\n🔎 Testing Search Functionality...")
        
        search_queries = [
            "Парацетамол",  # Russian medication name
            "шприц",        # Russian equipment name (partial)
            "МедТех",       # Manufacturer
            "PAR2024001"    # Batch number
        ]
        
        for query in search_queries:
            try:
                response = requests.get(f"{self.base_url}/inventory/search?q={query}")
                if response.status_code == 200:
                    items = response.json()
                    self.log_result(f"Search: '{query}'", True, f"Found {len(items)} items")
                else:
                    self.log_result(f"Search: '{query}'", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Search: '{query}'", False, f"Exception: {str(e)}")
    
    def test_dashboard_stats(self):
        """Test dashboard statistics API"""
        print("\n📊 Testing Dashboard Stats...")
        
        try:
            response = requests.get(f"{self.base_url}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_items", "low_stock_items", "expired_items", "expiring_soon_items", "total_value", "categories"]
                
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    self.log_result("Dashboard Stats Structure", True, "All required fields present")
                    
                    # Validate data types and values
                    if isinstance(stats["total_items"], int) and stats["total_items"] >= 0:
                        self.log_result("Dashboard Stats - Total Items", True, f"Total: {stats['total_items']}")
                    else:
                        self.log_result("Dashboard Stats - Total Items", False, f"Invalid total_items: {stats['total_items']}")
                    
                    if isinstance(stats["categories"], dict):
                        self.log_result("Dashboard Stats - Categories", True, f"Categories: {stats['categories']}")
                    else:
                        self.log_result("Dashboard Stats - Categories", False, f"Invalid categories: {stats['categories']}")
                    
                    if isinstance(stats["total_value"], (int, float)) and stats["total_value"] >= 0:
                        self.log_result("Dashboard Stats - Total Value", True, f"Value: {stats['total_value']}")
                    else:
                        self.log_result("Dashboard Stats - Total Value", False, f"Invalid total_value: {stats['total_value']}")
                        
                else:
                    self.log_result("Dashboard Stats Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Dashboard Stats", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Dashboard Stats", False, f"Exception: {str(e)}")
    
    def test_alerts_system(self):
        """Test alerts system API"""
        print("\n🚨 Testing Alerts System...")
        
        try:
            response = requests.get(f"{self.base_url}/alerts")
            if response.status_code == 200:
                alerts = response.json()
                required_alert_types = ["low_stock", "expired", "expiring_soon"]
                
                missing_types = [alert_type for alert_type in required_alert_types if alert_type not in alerts]
                if not missing_types:
                    self.log_result("Alerts Structure", True, "All alert types present")
                    
                    # Check each alert type
                    for alert_type in required_alert_types:
                        alert_items = alerts[alert_type]
                        if isinstance(alert_items, list):
                            self.log_result(f"Alerts - {alert_type}", True, f"Found {len(alert_items)} items")
                            
                            # Validate alert logic based on our test data
                            if alert_type == "low_stock" and len(alert_items) > 0:
                                # Should have low stock items (quantity <= threshold)
                                low_stock_valid = all(item["quantity"] <= item.get("min_quantity_threshold", 10) for item in alert_items)
                                self.log_result(f"Alerts Logic - {alert_type}", low_stock_valid, "Low stock logic validation")
                            
                            if alert_type == "expired" and len(alert_items) > 0:
                                # Should have expired items
                                current_date = date.today().isoformat()
                                expired_valid = all(item.get("expiry_date", "") < current_date for item in alert_items if item.get("expiry_date"))
                                self.log_result(f"Alerts Logic - {alert_type}", expired_valid, "Expired logic validation")
                                
                        else:
                            self.log_result(f"Alerts - {alert_type}", False, f"Invalid format: {type(alert_items)}")
                else:
                    self.log_result("Alerts Structure", False, f"Missing alert types: {missing_types}")
            else:
                self.log_result("Alerts System", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Alerts System", False, f"Exception: {str(e)}")
    
    def test_status_calculations(self):
        """Test automatic status calculations"""
        print("\n⚙️ Testing Status Calculations...")
        
        try:
            # Get all items to check status calculations
            response = requests.get(f"{self.base_url}/inventory")
            if response.status_code == 200:
                items = response.json()
                
                status_counts = {"active": 0, "low_stock": 0, "expired": 0, "out_of_stock": 0}
                for item in items:
                    status = item.get("status", "unknown")
                    if status in status_counts:
                        status_counts[status] += 1
                
                # Validate status logic
                expired_items = [item for item in items if item.get("expiry_date") and item["expiry_date"] < date.today().isoformat()]
                out_of_stock_items = [item for item in items if item["quantity"] == 0]
                low_stock_items = [item for item in items if item["quantity"] <= item.get("min_quantity_threshold", 10) and item["quantity"] > 0]
                
                self.log_result("Status Calculation - Expired", len(expired_items) == status_counts["expired"], 
                              f"Expected: {len(expired_items)}, Got: {status_counts['expired']}")
                self.log_result("Status Calculation - Out of Stock", len(out_of_stock_items) == status_counts["out_of_stock"],
                              f"Expected: {len(out_of_stock_items)}, Got: {status_counts['out_of_stock']}")
                
                self.log_result("Status Distribution", True, f"Active: {status_counts['active']}, Low Stock: {status_counts['low_stock']}, Expired: {status_counts['expired']}, Out of Stock: {status_counts['out_of_stock']}")
            else:
                self.log_result("Status Calculations", False, f"Could not retrieve items for status validation")
        except Exception as e:
            self.log_result("Status Calculations", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test items"""
        print("\n🧹 Cleaning up test data...")
        
        for item_id in self.created_items:
            try:
                response = requests.delete(f"{self.base_url}/inventory/{item_id}")
                if response.status_code == 200:
                    self.log_result(f"Delete Item: {item_id}", True)
                else:
                    self.log_result(f"Delete Item: {item_id}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Delete Item: {item_id}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🏥 Starting СтолицаЗдоровья Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence
        self.test_root_endpoint()
        self.create_test_inventory_items()
        self.test_inventory_crud()
        self.test_filtering()
        self.test_search_functionality()
        self.test_dashboard_stats()
        self.test_alerts_system()
        self.test_status_calculations()
        self.cleanup_test_data()
        
        # Final results
        print("\n" + "=" * 60)
        print("📋 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        return self.test_results['failed'] == 0

if __name__ == "__main__":
    tester = InventoryAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)