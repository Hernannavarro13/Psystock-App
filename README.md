# Stock Predictor Application

## Project Overview
A web application that allows users to:
- Create accounts and authenticate
- View stock predictions using machine learning
- Perform paper trading (simulated trading with virtual money)
- Add stocks to a watchlist
- Save all activities and preferences

## Tech Stack
- **Frontend**: React.js
- **Backend**: Django (Python)
- **Authentication**: JWT tokens
- **Database**: PostgreSQL
- **Stock Data**: Yahoo Finance API (yfinance)
- **Prediction Models**: Scikit-learn, Prophet

## Project Structure

### Frontend (React)
```
stock-predictor-frontend/
├── public/
├── src/
│   ├── api/                 # API calls to backend
│   ├── assets/              # Images, icons
│   ├── components/          # Reusable UI components
│   │   ├── auth/            # Login, register, profile components
│   │   ├── charts/          # Stock charts components
│   │   ├── dashboard/       # Main dashboard components
│   │   ├── layout/          # Layout components (header, footer)
│   │   ├── stocks/          # Stock listing, details components
│   │   ├── trading/         # Paper trading components
│   │   └── watchlist/       # Watchlist components
│   ├── contexts/            # React contexts (auth, theme)
│   ├── hooks/               # Custom hooks
│   ├── pages/               # Pages components
│   ├── routes/              # Route definitions
│   ├── services/            # Services for API interaction
│   ├── utils/               # Utility functions
│   ├── App.js               # Main App component
│   └── index.js             # Entry point
├── package.json
└── README.md
```

### Backend (Django)
```
stock_predictor_backend/
├── stock_predictor/             # Main Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                    # User authentication app
│   ├── models.py                # User model
│   ├── serializers.py           # User serializers
│   ├── views.py                 # Auth views
│   └── urls.py
├── api/                         # Main API app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── stocks/                      # Stocks app
│   ├── models.py                # Stock models
│   ├── serializers.py           # Stock serializers
│   ├── views.py                 # Stock views
│   ├── utils.py                 # Stock utility functions
│   └── urls.py
├── predictions/                 # Predictions app
│   ├── models.py                # Prediction models
│   ├── serializers.py           # Prediction serializers
│   ├── views.py                 # Prediction views
│   ├── ml_models/               # ML model files
│   ├── services.py              # Prediction services
│   └── urls.py
├── trading/                     # Paper trading app
│   ├── models.py                # Trading models
│   ├── serializers.py           # Trading serializers
│   ├── views.py                 # Trading views
│   └── urls.py
├── watchlist/                   # Watchlist app
│   ├── models.py                # Watchlist models
│   ├── serializers.py           # Watchlist serializers
│   ├── views.py                 # Watchlist views
│   └── urls.py
├── requirements.txt
└── manage.py
```
