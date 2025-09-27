from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    category: str = Query(...),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db=Depends(get_db)
):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    pipeline = [
        { "$match": { "customer_id": user, "type": "checking" } },  # only checking accounts
        { "$lookup": {
            "from": "transactions",
            "localField": "account_id",
            "foreignField": "account_id",
            "as": "transactions"
        }},
        { "$unwind": "$transactions" },  # flatten transactions
        { "$match": {
            "transactions.amount": { "$lt": 0 },  # only negative spending
            "transactions.date": { "$gte": start, "$lte": end }
        }},
        { "$group": {
            "_id": "$transactions.category",
            "total": { "$sum": "$transactions.amount" }  # negative totals
        }},
        { "$project": {
            "category": "$_id",
            "total": 1,
            "_id": 0
        }}
    ]

    results = list(db.accounts.aggregate(pipeline))

    # Compute percentages
    total_spent = -sum(r["total"] for r in results)  # total positive value of spending
    for r in results:
        r["percentage"] = round((-r["total"] / total_spent) * 100, 2) if total_spent else 0

    return results


# --- Example Endpoint ---
# @app.get("/{user}/spending/category/all")
# async def get_customers(start_date, end_dat):
#     return list(db.customers.find({}, {"_id": 0}))

# @app.get("/{user}/spending/percategory")
# async def get_customers(category, start_date, end_dat):
#     return list(db.customers.find({}, {"_id": 0}))

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
