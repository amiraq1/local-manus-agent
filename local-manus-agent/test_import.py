import os
import time
import requests
import hashlib

API_URL = "http://localhost:8000/api"

def run_tests():
    print("Testing Model Import Flow...")
    
    # Create fake files
    with open("fake.litertlm", "wb") as f:
        f.write(os.urandom(100 * 1024))  # 100 KB
    
    with open("bad.exe", "wb") as f:
        f.write(b"bad")

    # Test 1: Reject .exe
    r = requests.post(f"{API_URL}/models/import/start", json={"filename": "bad.exe", "size": 3})
    assert not r.json().get("accepted"), "Should reject .exe"
    print("Test 1 Passed: Rejected .exe")
    
    # Test 2: Reject path traversal
    r = requests.post(f"{API_URL}/models/import/start", json={"filename": "../fake.litertlm", "size": 102400})
    assert not r.json().get("accepted") or ".." not in r.json().get("filename", ""), "Should reject path traversal"
    print("Test 2 Passed: Handled path traversal")
    
    # Test 3: Import fake small .litertlm
    r = requests.post(f"{API_URL}/models/import/start", json={"filename": "fake.litertlm", "size": 102400, "model_name": "Test Model"})
    data = r.json()
    assert data.get("accepted"), "Should accept .litertlm"
    import_id = data["import_id"]
    chunk_size = data["chunk_size"]
    print("Test 3 Passed: Started import session")
    
    # Test 4: Chunk upload works
    with open("fake.litertlm", "rb") as f:
        chunk = f.read(chunk_size)
        files = {"chunk": ("blob", chunk)}
        data = {"import_id": import_id, "chunk_index": "0"}
        r = requests.post(f"{API_URL}/models/import/chunk", data=data, files=files)
        assert r.json().get("success"), "Should receive chunk"
    print("Test 4 Passed: Chunk uploaded")
    
    # Test 5: Finish combines chunks & SHA256
    r = requests.post(f"{API_URL}/models/import/finish", json={"import_id": import_id})
    data = r.json()
    assert data.get("success"), f"Should finish import, got {data}"
    
    with open("fake.litertlm", "rb") as f:
        expected_sha = hashlib.sha256(f.read()).hexdigest()
        
    assert data.get("sha256") == expected_sha, "SHA256 mismatch"
    print("Test 5 Passed: Finished and verified SHA256")
    
    # Cleanup test files
    os.remove("fake.litertlm")
    os.remove("bad.exe")
    
    # Check if imported model appears in registry
    r = requests.get(f"{API_URL}/models/status")
    models = r.json().get("models", [])
    found = any(m.get("is_imported") and m.get("name") == "Test Model" for m in models)
    assert found, "Imported model not found in registry status"
    print("Test 6 Passed: Imported model found in registry")
    
    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
