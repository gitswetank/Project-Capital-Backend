from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import json_util
import json
from typing import List
from collections import defaultdict


app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_db_client():
    global client, db
    client = MongoClient("mongodb://localhost:27017")
    db = client["bank_db"]
    print("MongoDB connected")

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        print("MongoDB disconnected")

def get_db():
    return db


# --- Endpoint 2: Spending per category for a user in a date range ---
@app.get("/{user}/spending/percategory")
async def spending_per_category(
    user: int,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    start = start_date
    end = end_date

    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},
            "transactions.date": {"$gte": start, "$lte": end}
        }},
        {"$group": {
            "_id": "$transactions.category",
            "total": {"$sum": "$transactions.amount"}
        }},
        {"$project": {"category": "$_id", "total": 1, "_id": 0}}
    ]

    results = list(db.accounts.aggregate(pipeline))

    total_spent = -sum(r["total"] for r in results)
    for r in results:
        r["percentage"] = round((-r["total"] / total_spent) * 100, 2) if total_spent else 0

    return results

# http://127.0.0.1:8000/100001/spending/selectcategories?categories=food&categories=utilities&start_date=2027-01-01&end_date=2027-12-31
@app.get("/{user}/spending/selectcategories")
async def spending_per_category(
    user: int,
    categories: List[str] = Query(..., description="List of categories"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    start = start_date
    end = end_date

    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},
            "transactions.date": {"$gte": start, "$lte": end},
            "transactions.category": {"$in": categories}
        }},
        {"$group": {
            "_id": "$transactions.category",
            "total": {"$sum": "$transactions.amount"}
        }},
        {"$project": {"category": "$_id", "total": 1, "_id": 0}}
    ]

    results = list(db.accounts.aggregate(pipeline))
    return results

# http://127.0.0.1:8000/100001/spending/category/selectcategories/cummulative?categories=food&categories=utilities&categories=healthcare&start_date=2027-01-01&end_date=2027-06-30
@app.get("/{user}/spending/category/selectcategories/cummulative")
async def spending_per_category_cuum(
    user: int,
    categories: List[str] = Query(..., description="List of categories"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},
            "transactions.category": {"$in": categories},
            "transactions.date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": {"date": "$transactions.date", "category": "$transactions.category"},
            "daily_total": {"$sum": "$transactions.amount"}
        }},
        {"$sort": {"_id.date": 1}}
    ]

    results = list(db.accounts.aggregate(pipeline))

    # Organize by date
    date_map = defaultdict(lambda: {cat: 0 for cat in categories})
    for r in results:
        date_map[r["_id"]["date"]][r["_id"]["category"]] = r["daily_total"]

    # Compute cumulative sums
    cumulative = []
    running_totals = {cat: 0 for cat in categories}
    for date in sorted(date_map.keys()):
        daily = {}
        for cat in categories:
            running_totals[cat] += date_map[date].get(cat, 0)
            daily[cat] = running_totals[cat]
        cumulative.append({"date": date, **daily})

    return cumulative

@app.get("/{user}/spending/percategory/all")
async def spending_per_category(
    user: int,
    db=Depends(get_db)
):

    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},
        }},
        {"$group": {
            "_id": "$transactions.category",
            "total": {"$sum": "$transactions.amount"}
        }},
        {"$project": {"category": "$_id", "total": 1, "_id": 0}}
    ]

    results = list(db.accounts.aggregate(pipeline))

    total_spent = -sum(r["total"] for r in results)
    for r in results:
        r["percentage"] = round((-r["total"] / total_spent) * 100, 2) if total_spent else 0

    return results


@app.get("/{user}/spending/transactions/all")
async def transactions(
    user: int,
    db=Depends(get_db)
):
    # user_accounts = list(db.accounts.find({"customer_id": user}, {"account_id": 1}))
    # account_ids = [a["account_id"] for a in user_accounts]
    # print(user)
    # print(account_ids)
    # print(user_accounts)
    # if not account_ids:
    #     return []  # No accounts, return empty list

    # s
    # transactions = list(
    #     db.transactions.find({"account_id": {"$in": [11782, 11783, 11784]}}).sort("date", 1)
    # )

    pipeline = [
        {"$match": {"customer_id": user}},  
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$replaceRoot": {"newRoot": "$transactions"}},
        {"$set": {"_id": {"$toString": "$_id"}}},
        {"$sort": {"transaction_date": -1}}  
        # {"$limit": 15}
    ]

    transactions = list(db.accounts.aggregate(pipeline))[::-1][:15]
    return json.loads(json_util.dumps(transactions))

@app.get("/{user}/spending/cummulative")
async def cummulative(    
    user: int,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},           
            "transactions.date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": "$transactions.date",                 
            "daily_total": {"$sum": "$transactions.amount"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "date": "$_id",
            "daily_total": 1,
            "_id": 0
        }}
    ]

    results = list(db.accounts.aggregate(pipeline))

    # Compute cumulative sum
    cumulative = []
    running_total = 0
    for r in results:
        running_total += r["daily_total"]
        cumulative.append({"date": r["date"], "cummulative_total": running_total})
    return cumulative


@app.get("/{user}/spending/cummulative/all")
async def cummulative_all(    
    user: int,
    db=Depends(get_db)
):
    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0}
        }},
        {"$group": {
            "_id": "$transactions.date",                 
            "daily_total": {"$sum": "$transactions.amount"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "date": "$_id",
            "daily_total": 1,
            "_id": 0
        }}
    ]

    results = list(db.accounts.aggregate(pipeline))

    # Compute cumulative sum
    cumulative = []
    running_total = 0
    for r in results:
        running_total += r["daily_total"]
        cumulative.append({"date": r["date"], "cummulative_total": running_total})
    return cumulative

@app.get("/{user}/spending/category/cummulative")
async def cummulative_cat(    
    user: int,
    categories: List[str] = Query(..., description="List of categories"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    pipeline = [
        {"$match": {"customer_id": user, "type": "checking"}},
        {"$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        {"$unwind": "$transactions"},
        {"$match": {
            "transactions.amount": {"$lt": 0},
            "transactions.category": {"$in": categories},
            "transactions.date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": "$transactions.date",                 
            "daily_total": {"$sum": "$transactions.amount"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "date": "$_id",
            "daily_total": 1,
            "_id": 0
        }}
    ]

    results = list(db.accounts.aggregate(pipeline))

    # Compute cumulative sum
    cumulative = []
    running_total = 0
    for r in results:
        running_total += r["daily_total"]
        cumulative.append({"date": r["date"], "cummulative_total": running_total})
    return cumulative


@app.get("/transactions/grocery")
async def root():
    return [
        {'date': '2007-04-23', 'close': 93.24},
        {'date': '2007-04-24', 'close': 95.35},
        {'date': '2007-04-25', 'close': 98.84},
        {'date': '2007-04-26', 'close': 99.92},
        {'date': '2007-04-29', 'close': 99.8},
        {'date': '2007-05-01', 'close': 99.47},
        {'date': '2007-05-02', 'close': 100.39},
        {'date': '2007-05-03', 'close': 100.4},
        {'date': '2007-05-04', 'close': 100.81},
        {'date': '2007-05-07', 'close': 103.92},
        {'date': '2007-05-08', 'close': 105.06},
        {'date': '2007-05-09', 'close': 106.88},
        {'date': '2007-05-09', 'close': 107.34},
        {'date': '2007-05-10', 'close': 108.74},
        {'date': '2007-05-13', 'close': 109.36},
        {'date': '2007-05-14', 'close': 107.52},
        {'date': '2007-05-15', 'close': 107.34},
        {'date': '2007-05-16', 'close': 109.44},
        {'date': '2007-05-17', 'close': 110.02},
        {'date': '2007-05-20', 'close': 111.98}
    ]
