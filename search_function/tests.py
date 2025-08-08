# search_function/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.db import connection
import json
from .models import Provider, NuccTaxonomy


class ProviderSearchTestCase(TestCase):
    """Test cases for provider search functionality"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_api_info_endpoint(self):
        """Test the main API info endpoint"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('endpoints', data)
        self.assertEqual(data['message'], 'Provider Lookup API')
    
    def test_search_endpoint_basic(self):
        """Test basic search functionality"""
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        self.assertIn('search_params', data)
    
    def test_search_with_first_name_parameter(self):
        """Test search with first name parameter"""
        response = self.client.get('/api/search/?first_name=John')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(data['search_params']['first_name'], 'John')
    
    def test_search_with_last_name_parameter(self):
        """Test search with last name parameter"""
        response = self.client.get('/api/search/?last_name=Smith')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(data['search_params']['last_name'], 'Smith')
    
    def test_search_with_both_names(self):
        """Test search with both first and last name"""
        response = self.client.get('/api/search/?first_name=John&last_name=Smith')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(data['search_params']['first_name'], 'John')
        self.assertEqual(data['search_params']['last_name'], 'Smith')
    
    def test_search_with_legacy_name_parameter(self):
        """Test search with legacy name parameter (should split into first/last)"""
        response = self.client.get('/api/search/?name=John Smith')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(data['search_params']['name'], 'John Smith')
    
    def test_search_with_location_parameters(self):
        """Test search with location parameters"""
        response = self.client.get('/api/search/?city=Boston&state=MA')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(data['search_params']['city'], 'Boston')
        self.assertEqual(data['search_params']['state'], 'MA')
    
    def test_search_grouped_by_specialty(self):
        """Test search with specialty grouping"""
        response = self.client.get('/api/search/?group_by_specialty=true')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('grouped_results', data)
        self.assertIn('grouped_by', data)
        self.assertEqual(data['grouped_by'], 'specialty')
    
    def test_quick_search_endpoint(self):
        """Test quick search for autocomplete"""
        response = self.client.get('/api/quick-search/?q=John')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)
    
    def test_quick_search_short_query(self):
        """Test quick search with short query (should return empty)"""
        response = self.client.get('/api/quick-search/?q=J')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['suggestions'], [])
    
    def test_advanced_search_endpoint(self):
        """Test advanced search endpoint"""
        response = self.client.get('/api/advanced-search/?first_name=John&last_name=Smith&state=CA')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIn('pagination', data)
    
    def test_states_api_endpoint(self):
        """Test states API endpoint - should only return US states"""
        response = self.client.get('/api/states/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('states', data)
        self.assertIsInstance(data['states'], list)
        
        # Check that only US state codes are returned (2 characters)
        for state in data['states']:
            self.assertEqual(len(state), 2)
            self.assertTrue(state.isalpha())
    
    def test_cities_api_endpoint(self):
        """Test cities API endpoint"""
        response = self.client.get('/api/cities/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('cities', data)
        self.assertIsInstance(data['cities'], list)
    
    def test_cities_api_with_state_filter(self):
        """Test cities API with state filter"""
        response = self.client.get('/api/cities/?state=CA')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('cities', data)
    
    def test_taxonomies_api_endpoint(self):
        """Test taxonomies API endpoint"""
        response = self.client.get('/api/taxonomies/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('taxonomies', data)
        self.assertIsInstance(data['taxonomies'], list)
    
    def test_taxonomies_api_with_query(self):
        """Test taxonomies API with search query"""
        response = self.client.get('/api/taxonomies/?q=cardio')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('taxonomies', data)
    
    def test_specialty_groups_api(self):
        """Test specialty groups API endpoint"""
        response = self.client.get('/api/specialty-groups/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('specialty_groups', data)
        self.assertIsInstance(data['specialty_groups'], list)
    
    def test_specialty_classifications_api(self):
        """Test specialty classifications API endpoint"""
        response = self.client.get('/api/specialty-classifications/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('classifications', data)
        self.assertIsInstance(data['classifications'], list)
    
    def test_specialty_classifications_with_group(self):
        """Test specialty classifications API with group filter"""
        response = self.client.get('/api/specialty-classifications/?group=Physicians')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('classifications', data)
    
    def test_pagination_parameters(self):
        """Test pagination parameters"""
        response = self.client.get('/api/search/?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('pagination', data)
        self.assertEqual(data['pagination']['page_size'], 10)
    
    def test_invalid_json_post(self):
        """Test POST request with invalid JSON"""
        response = self.client.post(
            '/api/search/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_health_check_endpoint(self):
        """Test database health check endpoint"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertIn('total_individual_providers', data)


class DatabaseConnectionTestCase(TestCase):
    """Test database connectivity and basic queries"""
    
    def test_database_connection(self):
        """Test that we can connect to the database"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_providers_table_exists(self):
        """Test that providers table exists and is accessible"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM providers WHERE entity_type_code = '1' LIMIT 1")
                # If we get here, table exists
                self.assertTrue(True)
        except Exception as e:
            self.fail(f"Providers table not accessible: {e}")
    
    def test_nucc_taxonomy_table_exists(self):
        """Test that nucc_taxonomy table exists and is accessible"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM nucc_taxonomy LIMIT 1")
                # If we get here, table exists
                self.assertTrue(True)
        except Exception as e:
            self.fail(f"NUCC taxonomy table not accessible: {e}")
    
    def test_individual_providers_exist(self):
        """Test that individual providers exist in database"""
        try:
            # This will fail if model fields don't match database
            providers = Provider.objects.filter(entity_type_code='1')[:1]
            for provider in providers:
                # Try to access each field
                _ = provider.npi
                _ = provider.last_name
                _ = provider.first_name
                _ = provider.practice_city
                _ = provider.practice_state
                _ = provider.primary_taxonomy_code
            self.assertTrue(True)
        except Provider.DoesNotExist:
            # No providers in DB is OK for this test
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Provider model field access failed: {e}")
    
    def test_taxonomy_model_fields(self):
        """Test that NuccTaxonomy model can access database fields"""
        try:
            taxonomies = NuccTaxonomy.objects.all()[:1]
            for taxonomy in taxonomies:
                _ = taxonomy.code
                _ = taxonomy.grouping
                _ = taxonomy.classification
                _ = taxonomy.specialization
            self.assertTrue(True)
        except NuccTaxonomy.DoesNotExist:
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Taxonomy model field access failed: {e}")


class SearchServiceTestCase(TestCase):
    """Test the ProviderSearchService utility functions"""
    
    def test_normalize_search_term(self):
        """Test search term normalization"""
        from .views import ProviderSearchService
        
        # Test normal case
        result = ProviderSearchService.normalize_search_term("  John   Smith  ")
        self.assertEqual(result, "john smith")
        
        # Test empty case
        result = ProviderSearchService.normalize_search_term("")
        self.assertEqual(result, "")
        
        # Test None case
        result = ProviderSearchService.normalize_search_term(None)
        self.assertEqual(result, "")
    
    def test_is_zip_code(self):
        """Test ZIP code validation"""
        from .views import ProviderSearchService
        
        # Valid ZIP codes
        self.assertTrue(ProviderSearchService.is_zip_code("12345"))
        self.assertTrue(ProviderSearchService.is_zip_code("12345-6789"))
        
        # Invalid ZIP codes
        self.assertFalse(ProviderSearchService.is_zip_code("1234"))
        self.assertFalse(ProviderSearchService.is_zip_code("123456"))
        self.assertFalse(ProviderSearchService.is_zip_code("abcde"))
        self.assertFalse(ProviderSearchService.is_zip_code(""))