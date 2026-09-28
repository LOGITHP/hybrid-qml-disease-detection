import httpx
import asyncio

async def test_execute():
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # Login to get token
        login_data = {"username": "admin@hybridqml.com", "password": "password"}
        auth_resp = await client.post("/auth/login", data=login_data)
        if auth_resp.status_code != 200:
            print("Login failed:", auth_resp.text)
            return
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get datasets to find a valid ID
        datasets_resp = await client.get("/datasets", headers=headers)
        datasets = datasets_resp.json()
        print("Datasets:", datasets)
        if not datasets:
            return
        
        d = datasets[0]
        v_id = d['versions'][0]['id']
        
        # Test execute plan
        payload = {
            "dataset_version_id": v_id,
            "target_column": "LUNG_CANCER",
            "steps": [
                {
                    "step_id": 1,
                    "tool_name": "stratified_split",
                    "rationale": "test",
                    "parameters": {"train_ratio": 0.70},
                    "fit_on_train_only": False
                }
            ]
        }
        resp = await client.post("/preprocessing/execute", json=payload, headers=headers)
        print("Status Code:", resp.status_code)
        print("Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(test_execute())
