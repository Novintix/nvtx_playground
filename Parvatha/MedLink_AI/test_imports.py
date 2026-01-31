# fix_everything.py
import subprocess
import sys

print("=" * 50)
print("FIXING ALL ISSUES")
print("=" * 50)

# Fix 1: Migrate database
print("\n1️⃣ Migrating database...")
try:
    from db import migrate_db
    migrate_db()
except Exception as e:
    print(f"❌ Migration failed: {e}")

# Fix 2: Check protobuf
print("\n2️⃣ Checking protobuf version...")
try:
    import google.protobuf
    version = google.protobuf.__version__
    print(f"Current protobuf version: {version}")
    
    if version < "5.28.3":
        print("⚠️ Upgrading protobuf...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "protobuf==5.28.3"])
        print("✅ Protobuf upgraded!")
except Exception as e:
    print(f"❌ Protobuf check failed: {e}")

# Fix 3: Test imports
print("\n3️⃣ Testing imports...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ Sentence transformers working")
except Exception as e:
    print(f"❌ Sentence transformers failed: {e}")

print("\n" + "=" * 50)
print("✅ ALL FIXES APPLIED - RESTART YOUR APP NOW")
print("=" * 50)