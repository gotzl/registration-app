from mysite.settings import PAGETITLE

def pagetitle_context_processor(request):
    return {'pagetitle': PAGETITLE}