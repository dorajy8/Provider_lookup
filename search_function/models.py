# search_function/models.py
from django.db import models

class NuccTaxonomy(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    grouping = models.TextField(blank=True, null=True)
    classification = models.TextField(blank=True, null=True)
    specialization = models.TextField(blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    display_name = models.TextField(blank=True, null=True)
    section = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'nucc_taxonomy'
        managed = False
    
    def __str__(self):
        return f"{self.code} - {self.classification}"

class Provider(models.Model):
    npi = models.CharField(max_length=10, primary_key=True)
    entity_type_code = models.CharField(max_length=1, blank=True, null=True)
    organization_name = models.TextField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    middle_name = models.TextField(blank=True, null=True)
    practice_address_line1 = models.TextField(blank=True, null=True)
    practice_address_line2 = models.TextField(blank=True, null=True)
    practice_city = models.TextField(blank=True, null=True)
    practice_state = models.CharField(max_length=2, blank=True, null=True)
    practice_postal_code = models.CharField(max_length=20, blank=True, null=True)
    practice_phone = models.CharField(max_length=20, blank=True, null=True)
    primary_taxonomy_code = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'providers'
        managed = False
    
    def __str__(self):
        if self.is_organization:
            return f"{self.npi} - {self.organization_name}"
        else:
            return f"{self.npi} - {self.last_name}, {self.first_name}"
    
    @property
    def full_name(self):
        """Return the full name based on entity type"""
        if self.entity_type_code == '2' or self.organization_name:
            return self.organization_name or "Unknown Organization"
        elif self.entity_type_code == '1' or self.last_name:
            name_parts = [self.first_name, self.middle_name, self.last_name]
            full_name = ' '.join([part for part in name_parts if part])
            return full_name or "Unknown Individual"
        else:
            return "Unknown Provider"
    
    @property
    def full_address(self):
        """Return the full practice address"""
        address_parts = [
            self.practice_address_line1,
            self.practice_address_line2,
            self.practice_city,
            self.practice_state,
            self.practice_postal_code
        ]
        return ', '.join([part for part in address_parts if part])
    
    @property
    def is_individual(self):
        """Check if this is an individual provider (entity_type_code = '1')"""
        return self.entity_type_code == '1'
    
    @property
    def is_organization(self):
        """Check if this is an organization (entity_type_code = '2')"""
        return self.entity_type_code == '2'
    
    @property
    def entity_type_display(self):
        """Return a display-friendly entity type"""
        if self.entity_type_code == '2':
            return "Organization"
        elif self.entity_type_code == '1':
            return "Individual"
        else:
            # Handle None or other values - try to guess from data
            if self.organization_name:
                return "Organization (inferred)"
            elif self.last_name:
                return "Individual (inferred)"
            else:
                return "Unknown"
    
    @property
    def primary_taxonomy(self):
        """Get the primary taxonomy object if it exists"""
        if self.primary_taxonomy_code:
            try:
                return NuccTaxonomy.objects.get(code=self.primary_taxonomy_code)
            except NuccTaxonomy.DoesNotExist:
                return None
        return None
    
    @property
    def specialty_description(self):
        """Get the specialty description from taxonomy"""
        taxonomy = self.primary_taxonomy
        if taxonomy:
            if taxonomy.specialization:
                return taxonomy.specialization
            return taxonomy.classification
        return None