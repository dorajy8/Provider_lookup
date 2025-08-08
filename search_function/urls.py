# search_function/urls.py

from django.urls import path
from django.http import JsonResponse
from . import views
from django.shortcuts import render


app_name = 'search_function'

urlpatterns = [
    # Main search endpoint - returns JSON for individual providers only
    path('api/search/', views.search_providers_view, name='search'),
    
    # Quick search for autocomplete
    path('api/quick-search/', views.quick_search_view, name='quick_search'),
    
    # Advanced search with multiple filters
    path('api/advanced-search/', views.advanced_search_view, name='advanced_search'),
    
    # Provider detail view (using NPI internally but not exposed to users)
    path('api/provider/<str:npi>/', views.provider_detail_view, name='provider_detail'),
    
    # Database health check
    path('api/health/', views.database_health_check, name='health_check'),
    
    # API endpoints for suggestions
    path('api/states/', 
         lambda request: JsonResponse({'states': views.get_state_suggestions()}), 
         name='api_states'),
    
    path('api/cities/', 
         lambda request: JsonResponse({
             'cities': views.get_city_suggestions(
                 request.GET.get('state'), 
                 int(request.GET.get('limit', 50))
             )
         }), 
         name='api_cities'),
    
    path('api/taxonomies/', 
         lambda request: JsonResponse({
             'taxonomies': views.get_taxonomy_suggestions(
                 request.GET.get('q'), 
                 int(request.GET.get('limit', 20))
             )
         }), 
         name='api_taxonomies'),
    
    path('api/specialty-groups/', 
         lambda request: JsonResponse({
             'specialty_groups': views.get_specialty_groups()
         }), 
         name='api_specialty_groups'),
    
    path('api/specialty-classifications/', 
         lambda request: JsonResponse({
             'classifications': views.get_specialty_classifications(
                 request.GET.get('group')
             )
         }), 
         name='api_specialty_classifications'),

    path('search/', views.search_interface, 
         name='search_interface'),
]