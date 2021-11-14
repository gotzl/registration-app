from mysite.settings import PAGETITLE, SITE_NOTICE, PRIVACY_NOTICE

def pagetitle_context_processor(request):
    return {'pagetitle': PAGETITLE,
            'site_notice': SITE_NOTICE,
            'privacy_notice': PRIVACY_NOTICE,
            }
