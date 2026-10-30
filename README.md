# Cloud-Based College Complaint System

Flask web app + MySQL (AWS RDS) deployed on AWS EC2.
Flow: Submitted -> Assigned -> In Progress -> Resolved

## Run locally
    pip install -r requirements.txt
    python app.py          # http://localhost:5000  (uses SQLite)
Register as Student, or as Admin using the Admin Access Code (default ADMIN2026, set env ADMIN_CODE to change).

## Deploy on AWS
1. RDS: create MySQL (free tier, db.t3.micro), DB name `complaintdb`, note endpoint/user/password.
   Security group: allow port 3306 ONLY from the EC2 security group.
2. EC2: Ubuntu t2/t3.micro. Security group: 22 (your IP), 80 (anywhere).
3. On EC2:
       sudo apt update && sudo apt install -y python3-pip python3-venv nginx
       unzip complaint-system.zip && cd complaint-system
       python3 -m venv venv && source venv/bin/activate
       pip install -r requirements.txt
       export DATABASE_URL="mysql+pymysql://USER:PASS@RDS-ENDPOINT/complaintdb"
       export SECRET_KEY="a-long-random-string"
       gunicorn -w 3 -b 127.0.0.1:8000 app:app
4. Nginx reverse proxy (/etc/nginx/sites-available/default):
       server { listen 80; location / { proxy_pass http://127.0.0.1:8000;
         proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; } }
   sudo systemctl restart nginx  -> open http://EC2-PUBLIC-IP
