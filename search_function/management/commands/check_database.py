from django.core.management.base import BaseCommand
from django.db import connection
from search_function.models import Provider, NuccTaxonomy


class Command(BaseCommand):
    help = 'Check database setup and display sample data'
    
    def handle(self, *args, **options):
        self.stdout.write("=== CHECKING DATABASE SETUP ===\n")
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Database connected: {version}")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Database connection failed: {e}")
            )
            return
        
        # Check providers table
        self.stdout.write("\n=== PROVIDERS TABLE ===")
        try:
            provider_count = Provider.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Providers table accessible: {provider_count:,} records")
            )
            
            # Show sample provider
            sample_provider = Provider.objects.first()
            if sample_provider:
                self.stdout.write(f"Sample provider:")
                self.stdout.write(f"  NPI: {sample_provider.npi}")
                self.stdout.write(f"  Name: {sample_provider.full_name}")
                self.stdout.write(f"  Type: {sample_provider.entity_type_display}")
                self.stdout.write(f"  Location: {sample_provider.practice_city}, {sample_provider.practice_state}")
                self.stdout.write(f"  Taxonomy: {sample_provider.primary_taxonomy_code}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Providers table error: {e}")
            )
        
        # Check taxonomy table
        self.stdout.write("\n=== TAXONOMY TABLE ===")
        try:
            taxonomy_count = NuccTaxonomy.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Taxonomy table accessible: {taxonomy_count:,} records")
            )
            
            # Show sample taxonomy
            sample_taxonomy = NuccTaxonomy.objects.first()
            if sample_taxonomy:
                self.stdout.write(f"Sample taxonomy:")
                self.stdout.write(f"  Code: {sample_taxonomy.code}")
                self.stdout.write(f"  Classification: {sample_taxonomy.classification}")
                self.stdout.write(f"  Specialization: {sample_taxonomy.specialization}")
                self.stdout.write(f"  Grouping: {sample_taxonomy.grouping}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Taxonomy table error: {e}")
            )
        
        # Check data relationships
        self.stdout.write("\n=== DATA RELATIONSHIPS ===")
        try:
            providers_with_taxonomy = Provider.objects.exclude(
                primary_taxonomy_code__isnull=True
            ).exclude(
                primary_taxonomy_code__exact=''
            ).count()
            
            self.stdout.write(
                f"Providers with taxonomy codes: {providers_with_taxonomy:,}"
            )
            
            # Check if taxonomy codes match
            sample_provider_with_taxonomy = Provider.objects.exclude(
                primary_taxonomy_code__isnull=True
            ).exclude(
                primary_taxonomy_code__exact=''
            ).first()
            
            if sample_provider_with_taxonomy:
                taxonomy_code = sample_provider_with_taxonomy.primary_taxonomy_code
                try:
                    matching_taxonomy = NuccTaxonomy.objects.get(code=taxonomy_code)
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Taxonomy relationships working")
                    )
                    self.stdout.write(
                        f"  Provider {sample_provider_with_taxonomy.npi} -> {matching_taxonomy.classification}"
                    )
                except NuccTaxonomy.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ Taxonomy code {taxonomy_code} not found in taxonomy table")
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Relationship check error: {e}")
            )
        
        # Check by entity types
        self.stdout.write("\n=== ENTITY TYPE BREAKDOWN ===")
        try:
            individuals = Provider.objects.filter(
                last_name__isnull=False,
                organization_name__isnull=True
            ).count()
            
            organizations = Provider.objects.filter(
                organization_name__isnull=False
            ).count()
            
            unclear = Provider.objects.filter(
                last_name__isnull=True,
                organization_name__isnull=True
            ).count()
            
            self.stdout.write(f"Individual providers: {individuals:,}")
            self.stdout.write(f"Organization providers: {organizations:,}")
            self.stdout.write(f"Unclear entity type: {unclear:,}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Entity type check error: {e}")
            )
        
        # Geographic distribution
        self.stdout.write("\n=== GEOGRAPHIC DISTRIBUTION ===")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT practice_state, COUNT(*) as count 
                    FROM providers 
                    WHERE practice_state IS NOT NULL 
                    GROUP BY practice_state 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                
                top_states = cursor.fetchall()
                self.stdout.write("Top 5 states by provider count:")
                for state, count in top_states:
                    self.stdout.write(f"  {state}: {count:,}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Geographic check error: {e}")
            )
        
        # Specialty distribution
        self.stdout.write("\n=== SPECIALTY DISTRIBUTION ===")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nt.classification, COUNT(*) as count
                    FROM providers p
                    JOIN nucc_taxonomy nt ON p.primary_taxonomy_code = nt.code
                    GROUP BY nt.classification
                    ORDER BY count DESC
                    LIMIT 5
                """)
                
                top_specialties = cursor.fetchall()
                self.stdout.write("Top 5 specialties:")
                for specialty, count in top_specialties:
                    self.stdout.write(f"  {specialty}: {count:,}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠ Specialty distribution check: {e}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("\n=== DATABASE CHECK COMPLETE ===")
        )