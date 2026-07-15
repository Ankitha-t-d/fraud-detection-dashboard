from flask import Flask, render_template, request, redirect, url_for, Response
import csv
import mysql.connector

app = Flask(__name__)

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Anku2006..",
    database="fraud_detection"
)

cursor = db.cursor()

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Temporary login
        if username == "bankadmin" and password == "admin123":
            return redirect(url_for("home"))

        else:
            return render_template(
                "login.html",
                error="Invalid Username or Password"
            ) 

    return render_template("login.html")

@app.route('/logout')
def logout():
    return redirect(url_for('login'))


@app.route('/download')
def download_csv():

    account_id = request.args.get("account_id")

    if account_id:
        cursor.execute("""
            SELECT transaction_id, account_id, amount, category
            FROM transactions
            WHERE account_id = %s
            ORDER BY transaction_time DESC
        """, (account_id,))
    else:
        cursor.execute("""
            SELECT transaction_id, account_id, amount, category
            FROM transactions
            ORDER BY transaction_time DESC
        """)

    rows = cursor.fetchall()

    csv_data = "Transaction ID,Account ID,Amount,Category\n"

    for row in rows:
        csv_data += f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions.csv"
        }
    )

@app.route('/')
def index():
    return redirect(url_for("login"))


@app.route('/dashboard')

def home():
    cursor.execute("SELECT COUNT(*) FROM accounts")
    total_accounts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM fraud_alerts")
    fraud_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE amount > 5000")
    high_value = cursor.fetchone()[0]

    

    account_id = request.args.get("account_id", "").strip()

    customer_name = ""
    risk_level = "Low"
    total_amount=0

    if account_id:

        cursor.execute("""
            SELECT customer_name
            FROM accounts
            WHERE account_id = %s
        """,(account_id,))

        result = cursor.fetchone()

        if result:
            customer_name = result[0]

    if account_id:
        cursor.execute("""
            SELECT transaction_id, account_id, amount, category
          FROM transactions
          WHERE account_id = %s
          ORDER BY transaction_time DESC
    """, (account_id,))
    else:
        cursor.execute("""
            SELECT transaction_id, account_id, amount, category
            FROM transactions
            ORDER BY transaction_time DESC
            LIMIT 5
    """)

    recent_transactions = cursor.fetchall()

    

    if account_id:
        cursor.execute("""
            SELECT category, COUNT(*)
        FROM transactions
        WHERE account_id = %s
        GROUP BY category
    """, (account_id,))
    else:
        cursor.execute("""
            SELECT category, COUNT(*)
        FROM transactions
        GROUP BY category
    """)

    chart_data = [list(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM fraud_alerts")
    fraud_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
      FROM transactions
      WHERE transaction_id NOT IN (
        SELECT transaction_id FROM fraud_alerts
    )
""")
    normal_count = cursor.fetchone()[0]

    # Account-wise statistics
    account_total = 0
    account_fraud = 0
    account_normal = 0

    if account_id:

    # Total transactions
        cursor.execute("""
            SELECT COUNT(*)
        FROM transactions
        WHERE account_id = %s
    """, (account_id,))
        account_total = cursor.fetchone()[0]

    # Fraud transactions
        cursor.execute("""
            SELECT COUNT(*)
        FROM fraud_alerts
        WHERE account_id = %s
    """, (account_id,))
        account_fraud = cursor.fetchone()[0]

    # Normal transactions
        account_normal = account_total - account_fraud

       # Total amount
    cursor.execute("""
        SELECT SUM(amount)
    FROM transactions
    WHERE account_id = %s
""", (account_id,))

    result = cursor.fetchone()
    total_amount = result[0] if result[0] is not None else 0

# Risk level
    if account_fraud > 5:
        risk_level = "High"
    elif account_fraud > 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

   # print(chart_data)
    #print(fraud_count)
    #print(normal_count)
    #print(account_fraud)
    #print(account_normal)

    if account_id:
          return render_template(
        "account_details.html",
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        fraud_alerts=fraud_alerts,
        high_value=high_value,
        recent_transactions=recent_transactions,
        chart_data=chart_data,
        fraud_count=fraud_count,
        normal_count=normal_count,
        account_total=account_total,
        account_fraud=account_fraud,
        account_normal=account_normal,
        customer_name=customer_name,
        total_amount=total_amount,
        risk_level=risk_level,
        account_id=account_id,
    )
    else:
        return render_template(
         "index.html",
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        fraud_alerts=fraud_alerts,
        high_value=high_value
    )
if __name__ == '__main__':
    app.run(debug=True)