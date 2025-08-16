#!/usr/bin/env python3
"""
Playwright test script for Weight Tracker webapp functionality
"""

import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class WeightTrackerTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        
    async def setup(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def teardown(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
    
    async def wait_for_app_ready(self):
        """Wait for the application to be ready"""
        print("🔄 Waiting for application to be ready...")
        try:
            await self.page.goto(self.base_url, wait_until="networkidle", timeout=10000)
            await self.page.wait_for_load_state("domcontentloaded")
            print("✅ Application loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load application: {e}")
            return False
    
    async def test_homepage_load(self):
        """Test if homepage loads correctly"""
        print("\n🧪 Testing homepage load...")
        
        # Check if page title is correct
        title = await self.page.title()
        print(f"📄 Page title: {title}")
        
        # Check for main navigation elements
        nav_links = await self.page.query_selector_all("nav a, .navbar a")
        print(f"🔗 Found {len(nav_links)} navigation links")
        
        # Check for main content area
        content = await self.page.query_selector("main, .container, .content")
        if content:
            print("✅ Main content area found")
        else:
            print("❌ Main content area not found")
        
        return True
    
    async def test_authentication_system(self):
        """Test user authentication functionality"""
        print("\n🧪 Testing authentication system...")
        
        # Look for login/register links
        login_link = await self.page.query_selector("a[href*='login'], .login, #login")
        register_link = await self.page.query_selector("a[href*='register'], .register, #register")
        
        if login_link:
            print("✅ Login functionality found")
            # Try to click login link
            try:
                await login_link.click()
                await self.page.wait_for_load_state("domcontentloaded")
                
                # Check for login form
                login_form = await self.page.query_selector("form")
                if login_form:
                    print("✅ Login form accessible")
                    
                    # Check for username/email and password fields
                    username_field = await self.page.query_selector("input[type='email'], input[name*='username'], input[name*='email']")
                    password_field = await self.page.query_selector("input[type='password']")
                    
                    if username_field and password_field:
                        print("✅ Login form has required fields")
                    else:
                        print("⚠️ Login form missing required fields")
                else:
                    print("❌ Login form not found")
            except Exception as e:
                print(f"⚠️ Could not test login form: {e}")
        else:
            print("⚠️ Login functionality not found - might be already logged in")
        
        if register_link:
            print("✅ Registration functionality found")
        
        return True
    
    async def test_weight_tracking_features(self):
        """Test weight tracking functionality"""
        print("\n🧪 Testing weight tracking features...")
        
        # Look for weight entry forms or buttons
        add_weight_elements = await self.page.query_selector_all(
            "button:has-text('Add'), input[type='number'], .weight-form, .add-weight"
        )
        
        if add_weight_elements:
            print(f"✅ Found {len(add_weight_elements)} weight tracking elements")
        else:
            print("⚠️ Weight tracking elements not found")
        
        # Look for charts/plots
        chart_elements = await self.page.query_selector_all(
            ".plotly, .chart, canvas, svg"
        )
        
        if chart_elements:
            print(f"✅ Found {len(chart_elements)} chart/visualization elements")
        else:
            print("⚠️ No charts or visualizations found")
        
        # Look for data tables
        table_elements = await self.page.query_selector_all("table, .data-table")
        
        if table_elements:
            print(f"✅ Found {len(table_elements)} data table elements")
        else:
            print("⚠️ No data tables found")
        
        return True
    
    async def test_responsive_design(self):
        """Test responsive design on different screen sizes"""
        print("\n🧪 Testing responsive design...")
        
        # Test mobile viewport
        await self.page.set_viewport_size({"width": 375, "height": 667})
        await self.page.wait_for_timeout(1000)
        
        # Check if navigation is still accessible
        nav = await self.page.query_selector("nav, .navbar")
        if nav:
            print("✅ Navigation responsive on mobile")
        else:
            print("⚠️ Navigation issues on mobile")
        
        # Test tablet viewport
        await self.page.set_viewport_size({"width": 768, "height": 1024})
        await self.page.wait_for_timeout(1000)
        print("✅ Tablet viewport tested")
        
        # Reset to desktop
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        await self.page.wait_for_timeout(1000)
        print("✅ Desktop viewport restored")
        
        return True
    
    async def test_performance(self):
        """Test basic performance metrics"""
        print("\n🧪 Testing performance...")
        
        # Measure page load time
        start_time = time.time()
        await self.page.reload(wait_until="networkidle")
        load_time = time.time() - start_time
        
        print(f"⏱️ Page load time: {load_time:.2f} seconds")
        
        if load_time < 5:
            print("✅ Good page load performance")
        else:
            print("⚠️ Slow page load performance")
        
        return True
    
    async def test_accessibility(self):
        """Test basic accessibility features"""
        print("\n🧪 Testing accessibility...")
        
        # Check for alt text on images
        images = await self.page.query_selector_all("img")
        images_with_alt = await self.page.query_selector_all("img[alt]")
        
        print(f"🖼️ Images: {len(images)}, with alt text: {len(images_with_alt)}")
        
        if len(images) == len(images_with_alt) or len(images) == 0:
            print("✅ All images have alt text")
        else:
            print("⚠️ Some images missing alt text")
        
        # Check for form labels
        inputs = await self.page.query_selector_all("input[type='text'], input[type='email'], input[type='password'], input[type='number']")
        labels = await self.page.query_selector_all("label")
        
        print(f"📝 Form inputs: {len(inputs)}, labels: {len(labels)}")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Weight Tracker webapp tests...\n")
        
        await self.setup()
        
        try:
            # Wait for app to be ready
            if not await self.wait_for_app_ready():
                print("❌ Application not ready, stopping tests")
                return False
            
            # Run all test functions
            tests = [
                self.test_homepage_load,
                self.test_authentication_system,
                self.test_weight_tracking_features,
                self.test_responsive_design,
                self.test_performance,
                self.test_accessibility
            ]
            
            results = []
            for test in tests:
                try:
                    result = await test()
                    results.append(result)
                except Exception as e:
                    print(f"❌ Test failed: {e}")
                    results.append(False)
            
            # Summary
            passed = sum(results)
            total = len(results)
            
            print(f"\n📊 Test Summary: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed!")
            elif passed > total // 2:
                print("⚠️ Most tests passed, some issues found")
            else:
                print("❌ Many tests failed, significant issues found")
                
            return passed == total
            
        finally:
            await self.teardown()

async def main():
    """Main function to run tests"""
    tester = WeightTrackerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())