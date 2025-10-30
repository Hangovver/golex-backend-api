"""
GOLEX Backend - Supabase Test Script
Quick test for database + storage connectivity
"""

import os
import asyncio
from app.db.supabase_client import SupabaseClient
from app.storage.r2_client import R2Client

async def test_supabase():
    """Test Supabase database connectivity"""
    print("\n" + "="*50)
    print("🔍 TESTING SUPABASE DATABASE...")
    print("="*50)
    
    try:
        # Initialize client
        db = SupabaseClient()
        
        # Test: Get fixtures count
        print("\n1️⃣ Testing fixtures table...")
        fixtures = await db.get_fixtures(limit=5)
        print(f"   ✅ Found {len(fixtures)} fixtures")
        if fixtures:
            print(f"   📊 Sample: {fixtures[0].get('home_team')} vs {fixtures[0].get('away_team')}")
        
        # Test: Get teams count
        print("\n2️⃣ Testing teams table...")
        teams = await db.get_teams(limit=5)
        print(f"   ✅ Found {len(teams)} teams")
        if teams:
            print(f"   📊 Sample: {teams[0].get('name')}")
        
        # Test: Insert test fixture
        print("\n3️⃣ Testing insert...")
        test_fixture = {
            "id": "test_12345",
            "league_id": "39",
            "home_team_id": "33",
            "away_team_id": "34",
            "match_date": "2025-10-29T19:00:00Z",
            "status": "NS"
        }
        success = await db.upsert_fixture(test_fixture)
        if success:
            print(f"   ✅ Insert successful!")
        
        # Test: Delete test fixture
        print("\n4️⃣ Testing delete...")
        deleted = await db.delete_fixture("test_12345")
        if deleted:
            print(f"   ✅ Delete successful!")
        
        print("\n" + "="*50)
        print("✅ SUPABASE DATABASE: ALL TESTS PASSED!")
        print("="*50 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ SUPABASE ERROR: {e}")
        print("\n⚠️ Check:")
        print("  - SUPABASE_URL is set")
        print("  - SUPABASE_SERVICE_ROLE_KEY is set")
        print("  - DATABASE_URL is set")
        print("  - Migration SQL is executed\n")
        return False

async def test_r2():
    """Test Cloudflare R2 storage connectivity"""
    print("\n" + "="*50)
    print("🔍 TESTING CLOUDFLARE R2 STORAGE...")
    print("="*50)
    
    try:
        # Initialize client
        r2 = R2Client()
        
        # Test: List images
        print("\n1️⃣ Testing list images...")
        images = await r2.list_images(limit=5)
        print(f"   ✅ Found {len(images)} images")
        if images:
            print(f"   📊 Sample: {images[0]}")
        
        # Test: Upload test image
        print("\n2️⃣ Testing upload...")
        test_data = b"GOLEX TEST IMAGE"
        key = "test/golex_test.txt"
        url = await r2.upload_image(key, test_data, "text/plain")
        if url:
            print(f"   ✅ Upload successful!")
            print(f"   🔗 URL: {url}")
        
        # Test: Download test image
        print("\n3️⃣ Testing download...")
        data = await r2.download_image(key)
        if data == test_data:
            print(f"   ✅ Download successful!")
        
        # Test: Delete test image
        print("\n4️⃣ Testing delete...")
        deleted = await r2.delete_image(key)
        if deleted:
            print(f"   ✅ Delete successful!")
        
        print("\n" + "="*50)
        print("✅ CLOUDFLARE R2: ALL TESTS PASSED!")
        print("="*50 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ R2 ERROR: {e}")
        print("\n⚠️ Check:")
        print("  - R2_ACCOUNT_ID is set")
        print("  - R2_ACCESS_KEY_ID is set")
        print("  - R2_SECRET_ACCESS_KEY is set")
        print("  - R2_BUCKET_NAME is set")
        print("  - R2_ENDPOINT is set\n")
        return False

async def main():
    """Run all tests"""
    print("\n" + "🚀"*25)
    print("GOLEX BACKEND - CONNECTIVITY TEST")
    print("🚀"*25 + "\n")
    
    # Check environment variables
    print("📋 Checking environment variables...")
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME"
    ]
    
    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}")
        else:
            print(f"   ❌ {var} (MISSING!)")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️ {len(missing)} environment variable(s) missing!")
        print("   Add them to Railway or .env file\n")
        return
    
    print("\n   ✅ All environment variables are set!\n")
    
    # Run tests
    supabase_ok = await test_supabase()
    r2_ok = await test_r2()
    
    # Final summary
    print("\n" + "🏆"*25)
    print("FINAL SUMMARY")
    print("🏆"*25 + "\n")
    
    if supabase_ok and r2_ok:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 Backend is ready to use!")
        print("\nNext steps:")
        print("  1. Run sync worker: python -m app.workers.sync_worker")
        print("  2. Start API server: uvicorn app.main:app --reload")
        print("  3. Test mobile app\n")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease fix the errors above and try again.\n")

if __name__ == "__main__":
    asyncio.run(main())

