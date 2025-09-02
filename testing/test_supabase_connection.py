#!/usr/bin/env python3
"""
Simple test to check Supabase connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    try:
        from supabase import create_client, Client
        
        # Get credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        print("🔍 Checking Supabase configuration...")
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: NOT SET")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
            return False
        
        # Test connection
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test basic auth method (this won't create a user, just test connection)
        print("\n🔐 Testing basic Supabase connection...")
        
        # Try to get current user (should fail gracefully if not authenticated)
        try:
            user = supabase.auth.get_user()
            print("✅ Supabase auth connection successful")
        except Exception as e:
            print(f"⚠️ Auth connection warning (expected if not authenticated): {e}")
        
        # Test database connection
        print("\n🗄️ Testing database connection...")
        try:
            # Try to access the profiles table
            response = supabase.table("profiles").select("*").limit(1).execute()
            print("✅ Database connection successful")
            print(f"📊 Profiles table accessible (found {len(response.data)} records)")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("💡 This is likely the issue! You need to create the profiles table.")
            return False
        
        print("\n🎉 Supabase connection test completed successfully!")
        return True
        
    except ImportError:
        print("❌ Supabase package not installed. Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Supabase Connection\n")
    success = test_supabase_connection()
    
    if not success:
        print("\n🔧 To fix the database issue, run this SQL in your Supabase dashboard:")
        print("""
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login TIMESTAMP WITH TIME ZONE
);

-- Enable RLS (Row Level Security)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policy for users to read their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Create policy for users to update their own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Create policy for inserting profiles
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);
        """)
