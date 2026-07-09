from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.register),
    path('auth/login', views.login_view),
    path('auth/logout', views.logout_view),
    path('auth/google', views.google_auth),

    # Health
    path('health', views.health),

    # Market
    path('market/overview', views.market_overview),
    path('stock/<str:ticker>', views.stock_detail),
    path('predict', views.predict),
    path('backtest', views.backtest),
    path('commodity/predict', views.commodity_predict),
    path('commodity/<str:symbol>', views.commodity_detail),
    path('watchlist/prices', views.watchlist_prices),

    # Watchlist & Portfolio (auth)
    path('watchlist', views.watchlist),
    path('portfolio', views.portfolio),
    path('trade', views.trade),

    # IPO
    path('ipo', views.ipo_list),
    path('ipo/predict', views.ipo_predict),

    # Sentiment & Social
    path('sentiment/<str:ticker>', views.sentiment),
    path('social/<str:ticker>', views.social_posts),
    path('news/<str:ticker>', views.news),
    path('analyze/<str:ticker>', views.analyze_ticker),
    path('chat', views.chat),
]
