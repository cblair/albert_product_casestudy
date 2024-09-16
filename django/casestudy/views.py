"""
For more information on setting up DRF views see docs:
https://www.django-rest-framework.org/api-guide/views/#class-based-views
"""
import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from logging import getLogger

from casestudy.models import Security
from casestudy.scheduled_call import ScheduledCall

logger = getLogger(__name__)

logger.setLevel(os.getenv('LOG_LEVEL', 'DEBUG')) # TODO

class LoginView(ObtainAuthToken):
    """
    Login view for the API.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
          context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })

class SecurityView(APIView):
    """
    (Financial) Security view for the API.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    refresh_interval = 5
    updater_initialized = False
    
    def __init__(self):
        super().__init__()
        self.__handlers = {
          'search': {
            'handler': self.__handle_search_ticker,
            'params': {'ticker'},
            'help': '/search?ticker=<ticker>',
          },
          'all': {
            'handler': self.__handle_all_securities,
            'help': '/search?ticker=<ticker>',  
          },
          'add': {
            'handler': self.__handler_add_to_portfolio,
            'help': '/add?ticker=<ticker>',
          },
          'remove': {
            'handler': self.__handler_remove_from_portfolio,
            'help': '/remove?ticker=<ticker>',
          }
        }
        if not SecurityView.updater_initialized:
          self.__price_updater = ScheduledCall(self.__price_updater, SecurityView.refresh_interval)
          SecurityView.updater_initialized = True

    def get(self, request, subpath="", format=None):
        """
        Top level GET handler.
        """        
        logger.debug({'message': f"Security GET view for the API for user {request.user.username}, path: {subpath}"})
        
        return self.__handler(request, subpath)

    def post(self, request, subpath="", format=None):
        """
        Top level POST handler.
        """        
        logger.debug({'message': f"Security POST view for the API for user {request.user.username}, path: {subpath}"})
        
        return self.__handler(request, subpath)
    
    def __handler(self, request, subpath):
      response = None

      if subpath in self.__handlers:
        param_keys = set(request.query_params.keys())
        if 'params' in self.__handlers[subpath] and param_keys != self.__handlers[subpath]['params']:
          help_message = f"Parameters required for subpath '{subpath}': {','.join(self.__handlers[subpath]['params'])}. Params supplied: '{','.join(param_keys)}'."
          help_message += f" More path details: {self.__help_message(subpath)}"
          response = Response({'message': help_message}, status=400)
        else:
          handler = self.__handlers[subpath]['handler']
          response = handler(request)
      
      return response
  
    def __help_message(self, subpath = ""):
      if subpath in self.__handlers:
        return self.__handlers[subpath]['help']
      else:
        return [subpath.help for subpath in self.__handlers.values()]

    def __handle_search_ticker(self, request):
        """
        Handle the search for a security by ticker.
        """
        params = request.query_params
        ticker = params['ticker']

        ticker_data = self.__get_ticker_prices([ticker])

        if ticker_data is None:
          return Response({'error': f"Could not find ticker {ticker}"}, status=200)
        
        return Response({'message': f"Ticker {ticker} found", 'tickers': ticker_data}, status=200)

    def __handle_all_securities(self, request):
        """
        Get all securities in this user's portfolio.
        """
        data = request.user.securities.values('ticker', 'last_price')
        securities = {}
        for security in data:
          securities[security['ticker']] = security['last_price']
        return Response(securities, status=200)

    def __handler_add_to_portfolio(self, request):
      response = None
      ticker = request.data.get('ticker', None)
      ticker_already_exists = request.user.securities.filter(ticker=ticker).exists()

      if ticker_already_exists:
        response = Response({'message': f"Ticker {ticker} already in portfolio"}, status=200)
      else:
        request.user.securities.create(ticker=ticker)
        response = Response({'message': f"Ticker {ticker} added to portfolio"}, status=200)

      return response

    def __handler_remove_from_portfolio(self, request):
      response = None
      ticker = request.data.get('ticker', None)
      ticker_exists = request.user.securities.filter(ticker=ticker).exists()

      if not ticker_exists:
        response = Response({'error': f"Ticker {ticker} not in portfolio, cannot remove"}, status=200)
      else:
        request.user.securities.filter(ticker=ticker).delete()
        response = Response({'message': f"Ticker {ticker} removed from portfolio"}, status=200)

      return response

    def __get_ticker_prices(self, tickers):
      response = requests.get(f"https://app.albert.com/casestudy/stock/prices/?tickers={','.join(tickers)}",
          headers={
            "Albert-Case-Study-API-Key": settings.ALBERT_CASE_STUDY_API_KEY,
          }
        )

      if response.status_code != 200:
        return None
      
      return response.json()

    def __price_updater(self):
      unique_tickers = [security.get('ticker') for security in Security.objects.values('ticker').distinct()]
      logger.info(f"Updating prices for tickers: {','.join(unique_tickers)}.")
      data = self.__get_ticker_prices(unique_tickers) or {}

      for ticker, price in data.items():
        Security.objects.filter(ticker=ticker).update(last_price=price)        
      
      logger.info(f" -> Updating prices for tickers: {','.join(unique_tickers)}.")
      