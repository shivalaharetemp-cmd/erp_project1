from .models import CompanyUser, Company


def user_companies(request):
    """
    Context processor to make user's companies available in all templates.
    """
    context = {
        'user_companies': [],
        'current_company': None,
    }
    
    if request.user.is_authenticated:
        # Get all companies for this user
        context['user_companies'] = CompanyUser.objects.filter(
            user=request.user, is_active=True
        ).select_related('company')
        
        # Get current company details
        company_id = request.session.get('company_id')
        if company_id:
            try:
                context['current_company'] = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
    
    return context
