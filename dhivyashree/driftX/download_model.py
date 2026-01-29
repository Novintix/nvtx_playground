from sentence_transformers import SentenceTransformer
import time

print("Attempting to download embedding model 'all-MiniLM-L6-v2'...")
print("This may take a minute depending on your internet connection.")

try:
    # This will download the model to the local huggingface cache
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    print("✅ Model downloaded successfully!")
except Exception as e:
    print(f"❌ Error downloading model: {e}")
    print("Retrying in 5 seconds...")
    time.sleep(5)
    try:
         model = SentenceTransformer('all-MiniLM-L6-v2')
         print("✅ Model downloaded successfully on retry!")
    except Exception as e:
         print(f"❌ Failed again: {e}")
