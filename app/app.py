from flask import Flask
import boto3
import json
import pymysql
import os
import socket

app = Flask(__name__)

# Values are supplied through environment variables
# rather than hard-coded into the application.
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SECRET_NAME = os.getenv("SECRET_NAME", "your-secret-name")
DB_HOST = os.getenv("DB_HOST", "your-rds-endpoint")


def get_db_credentials():
    """Retrieve database credentials from AWS Secrets Manager."""

    client = boto3.client(
        "secretsmanager",
        region_name=AWS_REGION
    )

    response = client.get_secret_value(
        SecretId=SECRET_NAME
    )

    return json.loads(response["SecretString"])


@app.route("/")
def home():
    try:
        credentials = get_db_credentials()

        connection = pymysql.connect(
            host=DB_HOST,
            user=credentials["username"],
            password=credentials["password"],
            database=credentials.get("dbname", "appdb"),
            connect_timeout=5
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()

        connection.close()

        hostname = socket.gethostname()

        return f"""
        <h1>AWS Multi-Tier Web Application</h1>
        <p>Application served from EC2 instance: <b>{hostname}</b></p>
        <p>Successfully connected to private Amazon RDS MySQL.</p>
        <p>Database response: {result[0]}</p>
        """

    except Exception as error:
        return f"Application error: {str(error)}", 500


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)