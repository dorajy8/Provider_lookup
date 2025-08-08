# search_function/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Case, When, IntegerField
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import re
from .models import Provider, NuccTaxonomy


class ProviderSearchService:
    """Service class to handle all provider search operations"""
    
    @staticmethod
    def normalize_search_term(term):
        """Normalize search terms for better matching"""
        if not term:
            return ""
        return re.sub(r'\s+', ' ', term.strip().lower())
    
    @staticmethod
    def is_zip_code(term):
        """Check if search term looks like a ZIP code"""
        return bool(re.match(r'^\d{5}(-\d{4})?$', term.strip()))
    
    @staticmethod
    def search_providers(search_params):
        """Search providers with various filters - ONLY INDIVIDUALS"""
        # Start with individual providers only (entity_type_code = '1')
        queryset = Provider.objects.filter(entity_type_code='1')
        
        # Name search - now split into first and last name
        first_name = search_params.get('first_name', '').strip()
        last_name = search_params.get('last_name', '').strip()
        
        # Legacy 'name' parameter - try to split it
        name = search_params.get('name', '').strip()
        if name and not first_name and not last_name:
            name_parts = name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                # Could be either first or last name, search both
                queryset = queryset.filter(
                    Q(first_name__icontains=name) | Q(last_name__icontains=name)
                )
        
        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)
        
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)
        
        # Location filters
        city = search_params.get('city', '').strip()
        if city:
            queryset = queryset.filter(practice_city__icontains=city)
        
        state = search_params.get('state', '').strip()
        if state:
            queryset = queryset.filter(practice_state__iexact=state)
        
        zip_code = search_params.get('zip_code', '').strip()
        if zip_code:
            if ProviderSearchService.is_zip_code(zip_code):
                # Handle both 5-digit and 9-digit ZIP codes
                if len(zip_code) == 5:
                    queryset = queryset.filter(practice_postal_code__startswith=zip_code)
                else:
                    queryset = queryset.filter(practice_postal_code=zip_code)
        
        # Specialty/taxonomy search
        specialty = search_params.get('specialty', '').strip()
        if specialty:
            # Search in taxonomy classifications and specializations
            taxonomy_codes = NuccTaxonomy.objects.filter(
                Q(classification__icontains=specialty) |
                Q(specialization__icontains=specialty) |
                Q(grouping__icontains=specialty)
            ).values_list('code', flat=True)
            
            if taxonomy_codes:
                queryset = queryset.filter(primary_taxonomy_code__in=taxonomy_codes)
        
        # Phone search
        phone = search_params.get('phone', '').strip()
        if phone:
            # Remove non-digits for phone search
            phone_digits = re.sub(r'\D', '', phone)
            if phone_digits:
                queryset = queryset.filter(practice_phone__contains=phone_digits)
        
        return queryset.select_related().order_by('last_name', 'first_name')


def search_providers_view(request):
    """Main search view that handles both GET and POST requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        data = request.GET
    
    # Perform search
    queryset = ProviderSearchService.search_providers(data)
    
    # Group results by specialty if requested
    group_by_specialty = data.get('group_by_specialty', 'false').lower() == 'true'
    
    # Pagination
    page_number = data.get('page', 1)
    page_size = min(int(data.get('page_size', 25)), 100)
    
    if group_by_specialty:
        # Group results by specialty group
        specialty_groups = {}
        
        for provider in queryset:
            taxonomy = provider.primary_taxonomy
            specialty_key = 'Unknown Specialty'
            
            if taxonomy and taxonomy.grouping:
                specialty_key = taxonomy.grouping
            elif taxonomy and taxonomy.classification:
                specialty_key = taxonomy.classification
            
            if specialty_key not in specialty_groups:
                specialty_groups[specialty_key] = []
            
            # Add provider data
            provider_data = {
                'entity_type_display': 'Individual',
                'first_name': provider.first_name,
                'last_name': provider.last_name,
                'middle_name': provider.middle_name,
                'full_name': provider.full_name,
                'address': provider.full_address,
                'phone': provider.practice_phone,
                'city': provider.practice_city,
                'state': provider.practice_state,
                'zip_code': provider.practice_postal_code,
                'distance_miles': getattr(provider, 'distance_miles', 0),
            }
            
            # Add taxonomy info
            if taxonomy:
                provider_data.update({
                    'taxonomy_description': taxonomy.classification,
                    'specialization': taxonomy.specialization,
                    'taxonomy_grouping': taxonomy.grouping
                })
            
            specialty_groups[specialty_key].append(provider_data)
        
        # Sort each specialty group by last name
        for specialty in specialty_groups:
            specialty_groups[specialty] = sorted(
                specialty_groups[specialty], 
                key=lambda x: (x['last_name'] or '', x['first_name'] or '')
            )
        
        response_data = {
            'grouped_results': specialty_groups,
            'total_results': queryset.count(),
            'search_params': data,
            'grouped_by': 'specialty'
        }
        
    else:
        # Regular paginated results
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)
        
        # Prepare results
        results = []
        for provider in page_obj:
            result = {
                'entity_type_display': 'Individual',
                'first_name': provider.first_name,
                'last_name': provider.last_name,
                'middle_name': provider.middle_name,
                'full_name': provider.full_name,
                'address': provider.full_address,
                'phone': provider.practice_phone,
                'city': provider.practice_city,
                'state': provider.practice_state,
                'zip_code': provider.practice_postal_code,
                'distance_miles': getattr(provider, 'distance_miles', 0),
            }
            
            # Add taxonomy description if available
            taxonomy = provider.primary_taxonomy
            if taxonomy:
                result['taxonomy_description'] = taxonomy.classification
                result['specialization'] = taxonomy.specialization
                result['taxonomy_grouping'] = taxonomy.grouping
            else:
                result['taxonomy_description'] = None
                result['specialization'] = None
                result['taxonomy_grouping'] = None
            
            results.append(result)
        
        response_data = {
            'results': results,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_results': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_size': page_size
            },
            'search_params': data
        }
    
    return JsonResponse(response_data)


@require_http_methods(["GET"])
def quick_search_view(request):
    """Quick search endpoint for autocomplete/suggestions"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Limit to 10 suggestions for performance - individuals only
    queryset = ProviderSearchService.search_providers({'name': query})[:10]
    
    suggestions = []
    for provider in queryset:
        suggestions.append({
            'first_name': provider.first_name,
            'last_name': provider.last_name,
            'full_name': provider.full_name,
            'type': 'Individual',
            'location': f"{provider.practice_city}, {provider.practice_state}" if provider.practice_city else None,
            'specialty': provider.specialty_description
        })
    
    return JsonResponse({'suggestions': suggestions})


@require_http_methods(["GET"])
def provider_detail_view(request, npi):
    """Get detailed information for a specific provider"""
    try:
        # Only allow individual providers
        provider = Provider.objects.get(npi=npi, entity_type_code='1')
    except Provider.DoesNotExist:
        return JsonResponse({'error': 'Individual provider not found'}, status=404)
    
    # Get taxonomy information
    taxonomy_info = None
    taxonomy = provider.primary_taxonomy
    if taxonomy:
        taxonomy_info = {
            'code': taxonomy.code,
            'classification': taxonomy.classification,
            'specialization': taxonomy.specialization,
            'definition': taxonomy.definition,
            'grouping': taxonomy.grouping,
            'display_name': taxonomy.display_name,
            'section': taxonomy.section
        }
    
    provider_data = {
        'entity_type_display': 'Individual',
        'first_name': provider.first_name,
        'middle_name': provider.middle_name,
        'last_name': provider.last_name,
        'full_name': provider.full_name,
        'practice_address': {
            'line1': provider.practice_address_line1,
            'line2': provider.practice_address_line2,
            'city': provider.practice_city,
            'state': provider.practice_state,
            'postal_code': provider.practice_postal_code,
            'full_address': provider.full_address
        },
        'phone': provider.practice_phone,
        'taxonomy': taxonomy_info
    }
    
    return JsonResponse(provider_data)


@require_http_methods(["GET"])
def advanced_search_view(request):
    """Advanced search with multiple filters"""
    queryset = ProviderSearchService.search_providers(request.GET)
    
    # Add additional filters for advanced search
    specialty_group = request.GET.get('specialty_group', '').strip()
    phone_area_code = request.GET.get('phone_area_code', '').strip()
    
    if specialty_group:
        # Filter by taxonomy grouping
        taxonomy_codes = NuccTaxonomy.objects.filter(
            grouping__icontains=specialty_group
        ).values_list('code', flat=True)
        queryset = queryset.filter(primary_taxonomy_code__in=taxonomy_codes)
    
    if phone_area_code:
        # Filter by phone area code
        queryset = queryset.filter(practice_phone__startswith=phone_area_code)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    page_size = min(int(request.GET.get('page_size', 50)), 100)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)
    
    # Prepare results with additional detail for advanced search
    results = []
    for provider in page_obj:
        result = {
            'entity_type_display': 'Individual',
            'first_name': provider.first_name,
            'last_name': provider.last_name,
            'full_name': provider.full_name,
            'address': provider.full_address,
            'phone': provider.practice_phone,
        }
        
        # Add taxonomy details
        taxonomy = provider.primary_taxonomy
        if taxonomy:
            result.update({
                'taxonomy_classification': taxonomy.classification,
                'taxonomy_specialization': taxonomy.specialization,
                'taxonomy_grouping': taxonomy.grouping
            })
        
        results.append(result)
    
    response_data = {
        'results': results,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_results': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    }
    
    return JsonResponse(response_data)


@require_http_methods(["GET"])
def database_health_check(request):
    """Check database connectivity and return basic stats"""
    try:
        # Count individual providers only
        total_individual_providers = Provider.objects.filter(entity_type_code='1').count()
        
        # Get state distribution for individuals
        states = Provider.objects.filter(
            entity_type_code='1'
        ).exclude(
            practice_state__isnull=True
        ).exclude(
            practice_state__exact=''
        ).values_list('practice_state', flat=True).distinct()
        
        return JsonResponse({
            'status': 'healthy',
            'total_individual_providers': total_individual_providers,
            'states_with_providers': len(states),
            'database_connection': 'ok'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


# Utility functions for search suggestions and autocomplete

def get_state_suggestions():
    """Get list of US states only - 50 states + DC"""
    # Fixed list of US states (no territories)
    us_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
        'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
        'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
        'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ]
    
    # Filter to only states that have individual providers
    states_with_providers = Provider.objects.filter(
        entity_type_code='1',
        practice_state__in=us_states
    ).exclude(
        practice_state__isnull=True
    ).exclude(
        practice_state__exact=''
    ).values_list('practice_state', flat=True).distinct().order_by('practice_state')
    
    return list(states_with_providers)


def get_city_suggestions(state=None, limit=50):
    """Get list of cities, optionally filtered by state - individuals only"""
    queryset = Provider.objects.filter(entity_type_code='1').exclude(
        practice_city__isnull=True
    ).exclude(
        practice_city__exact=''
    )
    
    if state:
        queryset = queryset.filter(practice_state__iexact=state)
    
    cities = queryset.values_list(
        'practice_city', flat=True
    ).distinct().order_by('practice_city')[:limit]
    
    return list(cities)


def get_taxonomy_suggestions(query=None, limit=20):
    """Get taxonomy suggestions for autocomplete"""
    queryset = NuccTaxonomy.objects.all()
    
    if query and len(query) >= 2:
        queryset = queryset.filter(
            Q(classification__icontains=query) |
            Q(specialization__icontains=query) |
            Q(grouping__icontains=query) |
            Q(code__icontains=query)
        )
    
    suggestions = []
    for taxonomy in queryset[:limit]:
        display_name = taxonomy.classification
        if taxonomy.specialization:
            display_name += f" - {taxonomy.specialization}"
        
        suggestions.append({
            'code': taxonomy.code,
            'display_name': display_name,
            'classification': taxonomy.classification,
            'specialization': taxonomy.specialization,
            'grouping': taxonomy.grouping
        })
    
    return suggestions


def get_specialty_groups():
    """Get all unique specialty groups"""
    groups = NuccTaxonomy.objects.exclude(
        grouping__isnull=True
    ).exclude(
        grouping__exact=''
    ).values_list('grouping', flat=True).distinct().order_by('grouping')
    
    return list(groups)


def get_specialty_classifications(group=None):
    """Get specialty classifications, optionally filtered by group"""
    queryset = NuccTaxonomy.objects.exclude(
        classification__isnull=True
    ).exclude(
        classification__exact=''
    )
    
    if group:
        queryset = queryset.filter(grouping__icontains=group)
    
    classifications = queryset.values_list(
        'classification', flat=True
    ).distinct().order_by('classification')
    
    return list(classifications)

def search_interface(request):
    """Serve the HTML search interface"""
    return render(request, 'search_function/search.html')