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
