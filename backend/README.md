#Tạo môi trường:
py -m venv venv  hoặc python3.11 -m venv venv
.\venv\Scripts\Activate hoặc source venv/bin/activate

#Cài thư viện:
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8001
