from django.contrib import admin
from django.db.models import Q


class ErrorCodeFilter(admin.SimpleListFilter):
    title = 'Error code'
    parameter_name = 'error_code'

    def lookups(self, request, model_admin):
        return ("403", "403 Forbidden"), ("404", "404 Not found"), \
            ("500", "500 Server Error"), ("503", "503 Temporary Unavailable"), \
            ("900", "900 XPATH not found"), ("990", "990 Connection error"), ("999", "Errore sconosciuto")

    def queryset(self, request, queryset):
        # implements the filter
        if self.value():
            if self.value() == "999":
                return queryset.filter(
                    verification_error__isnull=False
                ).exclude(
                    Q(verification_error__icontains="403") |
                    Q(verification_error__icontains="404") |
                    Q(verification_error__icontains="500") |
                    Q(verification_error__icontains="503") |
                    Q(verification_error__icontains="900") |
                    Q(verification_error__icontains="990")
                )
            else:
                return queryset.filter(verification_error__icontains=self.value())
        else:
            return queryset
