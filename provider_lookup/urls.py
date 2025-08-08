"""
URL configuration for provider_lookup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# provider_lookup/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_info(request):
    return JsonResponse({
        'message': 'Individual Healthcare Provider Lookup API',
        'version': '2.0',
        'description': 'Search for individual healthcare providers only (excludes organizations)',
        'total_individual_providers': '6,881,257 providers available',
        'endpoints': {
            'search': {
                'url': '/api/search/',
                'method': 'GET/POST',
                'description': 'Search individual providers by name, location, specialty',
                'parameters': {
                    'first_name': 'Provider first name',
                    'last_name': 'Provider last name', 
                    'city': 'Practice city',
                    'state': 'US state abbreviation (e.g., CA, NY)',
                    'zip_code': 'ZIP code (5 or 9 digits)',
                    'specialty': 'Medical specialty',
                    'page': 'Page number (default: 1)',
                    'page_size': 'Results per page (max: 100, default: 25)'
                }
            },
            'quick_search': {
                'url': '/api/quick-search/',
                'method': 'GET',
                'description': 'Quick search for autocomplete (min 2 characters)',
                'parameters': {'q': 'Search query'}
            },
            'advanced_search': {
                'url': '/api/advanced-search/',
                'method': 'GET',
                'description': 'Advanced search with additional filters'
            },
            'provider_detail': {
                'url': '/api/provider/{npi}/',
                'method': 'GET',
                'description': 'Get detailed information for specific individual provider'
            },
            'health_check': {
                'url': '/api/health/',
                'method': 'GET',
                'description': 'Database connectivity and stats'
            },
            'states': {
                'url': '/api/states/',
                'method': 'GET',
                'description': 'List of US states with individual providers'
            },
            'cities': {
                'url': '/api/cities/',
                'method': 'GET',
                'description': 'List of cities with individual providers',
                'parameters': {'state': 'Filter by state (optional)'}
            },
            'taxonomies': {
                'url': '/api/taxonomies/',
                'method': 'GET',
                'description': 'Healthcare taxonomy codes and descriptions',
                'parameters': {'q': 'Search query (optional)'}
            },
            'specialty_groups': {
                'url': '/api/specialty-groups/',
                'method': 'GET',
                'description': 'List of medical specialty groups'
            },
            'specialty_classifications': {
                'url': '/api/specialty-classifications/',
                'method': 'GET',
                'description': 'List of specialty classifications',
                'parameters': {'group': 'Filter by specialty group (optional)'}
            }
        },
        'notes': {
            'entity_types': 'Only individual providers (entity_type_code = 1) are included',
            'data_source': 'NPPES (National Plan and Provider Enumeration System)',
            'us_states_only': 'State dropdown limited to 50 US states + DC',
            'search_tips': [
                'Use first_name and last_name separately for better results',
                'State must be 2-letter abbreviation (CA, NY, TX, etc.)',
                'ZIP codes support both 5-digit and 9-digit formats',
                'Specialty search includes classification, specialization, and grouping'
            ]
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_info, name='api_info'),
    path('', include('search_function.urls')),
]