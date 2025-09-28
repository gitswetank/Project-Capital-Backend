import pandas as pd
from faker import Faker
import numpy as np
from pymongo import MongoClient
import random
from datetime import datetime, timedelta


fake = Faker()
N_CUSTOMERS = 999
start_cid = 1000+np.random.randint(N_CUSTOMERS)


customers = []
for cid in range(1, N_CUSTOMERS + 1):
    name = fake.unique.name()
    username = (name[0]+name.split(' ')[1]).lower()
    username_suffix = str(len(name.split()[1]))+str(len(name.split()[0])%3)+name.split()[0][-1]
    customers.append({
        "customer_id": 100000+(start_cid+cid) % N_CUSTOMERS,
        "name": name,
        "username": username+username_suffix,
        "password": "12345_"+str(len(name.split()[0])),
        "salary": round((np.random.normal(loc=70000, scale=20000)/12), 2),
        "raise": np.random.uniform(0, 0.02)
    })

df_customers = pd.DataFrame(customers)

df_customers  = df_customers.drop_duplicates(subset="username", keep="first")

df_customers.to_csv("customers.csv", index=False)

accounts = []

account_id_counter = 10000
for customer in customers:
    cust_id = customer["customer_id"]
    n_checking = random.randint(1, 3)
    n_savings = random.randint(0, 3)
    saved = np.random.uniform(0, 0.4)

    checking_portions = np.random.dirichlet(np.ones(n_checking)) * (1 - saved)
    
    # Randomly split savings portion (saved) across n_savings accounts (if any)
    if n_savings > 0:
        savings_portions = np.random.dirichlet(np.ones(n_savings)) * saved
    else:
        savings_portions = []
    
    for portion in checking_portions:
        accounts.append({
            "customer_id": cust_id,
            "account_id": account_id_counter,
            "type": "checking",
            "balance": round(random.uniform(50000, 200000), 2),
            "interest":0,
            "salary_portion": portion
        })
        account_id_counter += 1
    for portion in savings_portions:
        accounts.append({
            "customer_id": cust_id,
            "account_id": account_id_counter,
            "type": "savings",
            "balance": round(random.uniform(5000, 10000), 2),
            "interest": np.random.uniform(0, 0.01),
            "salary_portion":portion
        })
        account_id_counter += 1

transactions = []

low_spending_cat = ['food', 'entertainment', 'utilities', 'transportation', 'shopping', 'miscellaneous']
high_spending_cat = ['housing', 'education', 'healthcare']
card_type = ["credit", "debit"]

start_date = datetime(2027, 1, 1)   # start year = 2027
days = 365                          # simulate 1 yea


# spending distributions


for act in accounts:
    if act["type"] == "checking":
        # Pick type of transaction
        for d in range(days):
            date = start_date + timedelta(days=d)
            small_beta = np.random.beta(a=3, b=50) * 300
            big_beta   = np.random.beta(a=5, b=1)  * 1500
            for _ in range(np.random.randint(1, 5)):  # 3 transactions per day
                tx_type = np.random.choice(["spend_credit", "deposit_debit", "spend_debit"], 
                                           p=[0.85, 0.075, 0.075])
                
                if tx_type == "spend_credit":
                    if np.random.rand() < 0.03:  # 5% chance of big spending
                        category = random.choice(high_spending_cat)
                        amount = -big_beta
                    else:
                        category = random.choice(low_spending_cat)
                        amount = -small_beta
                    card = "credit"

                elif tx_type == "deposit_debit":
                    category = "deposit"
                    amount = abs(np.random.normal(1000, 300))  # deposit amount
                    card = "debit"

                else:  # spend_debit
                    category = random.choice(low_spending_cat)
                    amount = -small_beta
                    card = "debit"
                
                transactions.append({
                    "account_id": act["account_id"],
                    "category": category,
                    "amount": round(float(amount), 2),
                    "card_type": card,
                    "date": date.strftime("%Y-%m-%d")

                })




customers_df = pd.DataFrame(customers)
accounts_df = pd.DataFrame(accounts)
transactions_df = pd.DataFrame(transactions)

customers_df.to_csv("customers.csv", index=False)
accounts_df.to_csv("accounts.csv", index=False)
transactions_df.to_csv("transactions.csv", index=False)

client = MongoClient("mongodb://localhost:27017")
db = client["bank_db"]


# --- Load CSVs ---
customers_data = pd.read_csv("customers.csv").to_dict(orient="records")
accounts_data = pd.read_csv("accounts.csv").to_dict(orient="records")
transactions_data = pd.read_csv("transactions.csv").to_dict(orient="records")

# --- Insert into MongoDB ---
db.customers.drop()
db.accounts.drop()
db.transactions.drop()

db.customers.insert_many(customers_data)
db.accounts.insert_many(accounts_data)
db.transactions.insert_many(transactions_data)
