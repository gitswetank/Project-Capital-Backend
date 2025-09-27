import pandas as pd
from faker import Faker
import numpy as np
from pymongo import MongoClient
import random

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
        "password": "12345_"+str(len(name.split()[0]))
    })

df_customers = pd.DataFrame(customers)

df_customers  = df_customers.drop_duplicates(subset="username", keep="first")

df_customers.to_csv("customers.csv", index=False)

accounts = []

account_id_counter = 1
for customer in customers:
    cust_id = customer["customer_id"]
    n_checking = random.randint(1, 3)
    n_savings = random.randint(0, 3)
    for _ in range(n_checking):
        accounts.append({
            "customer_id": cust_id,
            "account_id": account_id_counter,
            "type": "checking",
            "balance": round(random.uniform(5000, 10000), 2)
        })
        account_id_counter += 1
    for _ in range(n_savings):
        accounts.append({
            "customer_id": cust_id,
            "account_id": account_id_counter,
            "type": "savings",
            "balance": round(random.uniform(5000, 10000), 2)
        })
        account_id_counter += 1

accounts_df = pd.DataFrame(accounts)
accounts_df.to_csv("accounts.csv", index=False)


# --- Connect to MongoDB ---
client = MongoClient("mongodb://localhost:27017")
db = client["bank_db"]  # database name

# --- Load CSVs ---
customers_df = pd.read_csv("customers.csv")
accounts_df = pd.read_csv("accounts.csv")

# --- Convert to dicts ---
customers_data = customers_df.to_dict(orient="records")
accounts_data = accounts_df.to_dict(orient="records")

# --- Insert into MongoDB ---
db.customers.drop()  # drop existing collection if any
db.accounts.drop()

db.customers.insert_many(customers_data)
db.accounts.insert_many(accounts_data)