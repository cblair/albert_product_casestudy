from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from casestudy.models import Security
from casestudy.views import SecurityView
        
class SecurityViewTest(TestCase):
    login_url = reverse('login')

    def __setup_User(self):
        user = User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='password'
        )
        self.assertTrue(user.is_active)
        self.assertEqual(user.username, 'user1')
        self.assertEqual(user.email, 'test@example.com')
    
    def __get_login_token(self):
      response = self.client.post(
            SecurityViewTest.login_url,
            data={"username": "user1", "password": "password"},
        )
      return response.json()['token']

    def setUp(self):
        self.client = Client()
        self.__setup_User()
        self.token = self.__get_login_token()
        
        # Fake out calls to albert.com
        def get_ticker_price(tickers):
            return {"AAPL": 216.32}
        SecurityView.__SecurityView_get_ticker_price = get_ticker_price

    def test_security_view_get_search(self):
        Security.objects.create(
            name='Apple Inc',
            ticker='AAPL',
            last_price=100.0,
            user=User.objects.get(username='user1')
        )
        security_url = reverse(f'security', kwargs={'subpath': 'search'})
        security_url += '?ticker=AAPL'
        response = self.client.get(security_url, headers={'Authorization': f'Token {self.token}'})
        self.assertEquals(response.status_code, 200, response.json())
        self.assertEquals(response.json(), {'message': 'Ticker AAPL found', 'tickers': {'AAPL': 216.32}})
        # Test not found
        security_url = reverse(f'security', kwargs={'subpath': 'search'})
        security_url += '?ticker=BAD'
        response = self.client.get(security_url, headers={'Authorization': f'Token {self.token}'})
        self.assertEquals(response.status_code, 200, response.json())
        self.assertEquals(response.json(), {'error': 'Could not find ticker BAD'})
    
    def test_security_view_get_all(self):
        Security.objects.create(
            name='Apple Inc',
            ticker='AAPL',
            last_price=100.0,
            user=User.objects.get(username='user1')
        )
        security_url = reverse('security', kwargs={'subpath': 'all'})
        response = self.client.get(security_url, headers={'Authorization': f'Token {self.token}'})
        self.assertEquals(response.status_code, 200, response.json())
        self.assertEquals(response.json(), {'AAPL': 100.0})

    def test_security_view_post_add_and_remove(self):
        Security.objects.create(
            name='Apple Inc',
            ticker='AAPL',
            last_price=100.0,
            user=User.objects.get(username='user1')
        )
        # Testing add route
        security_url = reverse('security', kwargs={'subpath': 'add'})
        response = self.client.post(
            security_url, 
            headers={'Authorization': f'Token {self.token}'},
            data={'ticker': 'GOOGL'}
        )
        self.assertEquals(response.status_code, 200, response.json())
        security = Security.objects.get(ticker='GOOGL')
        self.assertEquals(security.ticker, 'GOOGL')
        response = self.client.post(
            security_url, 
            headers={'Authorization': f'Token {self.token}'},
            data={'ticker': 'GOOGL'}
        )
        self.assertEquals(response.status_code, 200, response.json())
        self.assertEquals(response.json()["message"], "Ticker GOOGL already in portfolio")
        # Testing remove route
        security_url = reverse('security', kwargs={'subpath': 'remove'})
        response = self.client.post(
            security_url, 
            headers={'Authorization': f'Token {self.token}'},
            data={'ticker': 'GOOGL'}
        )
        self.assertEquals(response.status_code, 200, response.json())
        def throws_not_found():
            Security.objects.get(ticker='GOOGL')
        self.assertRaises(Security.DoesNotExist, throws_not_found)
        # Remove - not found when already gone
        response = self.client.post(
            security_url, 
            headers={'Authorization': f'Token {self.token}'},
            data={'ticker': 'GOOGL'}
        )
        self.assertEquals(response.status_code, 200, response.json())
        self.assertEquals(response.json()["error"], "Ticker GOOGL not in portfolio, cannot remove")

    def test_security_view_missing_params(self):
        security_url = reverse('security', kwargs={'subpath': 'search'})
        response = self.client.get(
            security_url, 
            headers={'Authorization': f'Token {self.token}'},
        )
        self.assertEquals(response.status_code, 400, response.json())
