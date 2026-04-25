from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import AuditLog


@login_required
def audit_log_list(request):
    cid = request.session.get('company_id')
    qs = AuditLog.objects.select_related('user', 'company').order_by('-timestamp')
    if cid:
        qs = qs.filter(company_id=cid)

    action = request.GET.get('action', '')
    model = request.GET.get('model', '')
    if action:
        qs = qs.filter(action=action)
    if model:
        qs = qs.filter(model_name=model)

    return render(request, 'audit/audit_log_list.html', {
        'logs': qs[:200], 'action_filter': action, 'model_filter': model
    })


@login_required
def audit_log_detail(request, pk):
    log = get_object_or_404(AuditLog, pk=pk)
    return render(request, 'audit/audit_log_detail.html', {'log': log})
