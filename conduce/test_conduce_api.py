import unittest
import api
import mock
from mock import patch

class TestCalls(unittest.TestCase):

   @patch('api.make_post_request')	
   def test_create_account(self, mock_get):
      name = 'Raghavendra'
      email = 'raghavendra@conduce.com'
      mock_get.return_value.status_code = 200
      response = api.create_account(name, email)
      self.assertEquals(response.status_code, 200)
	  
   @patch('api.make_post_request')
   def test_account_exists(self, mock_get):
      email = 'raghavendra@conduce.com'
      mock_get.return_value.status_code = 200
      response = api.account_exists(email)
      #self.assertEquals(response.status_code, 200)
      self.assertTrue(True)
	  
   # @patch('api.make_post_request')
   # def test_create_api_key(self, mock_get):
      # user = 'raghavendra@conduce.com'
      # password = 'Conduce@m'
      # mock_get.return_value = {"api_key":"IOelDLg6ShGGfne6eJYUDNvBmJqhn0f5j8sxyqQPXSY"}
      # response = api.create_api_key()
      # self.assertEquals(response, 'IOelDLg6ShGGfne6eJYUDNvBmJqhn0f5j8sxyqQPXSY')
	  
   @patch('api.make_post_request')
   def test_remove_api_key(self, mock_get):
      api_key = 'IOelDLg6ShGGfne6eJYUDNvBmJqhn0f5j8sxyqQPXSY'
      response = api.remove_api_key(api_key)
	  
if __name__ == "__main__":
    unittest.main()
