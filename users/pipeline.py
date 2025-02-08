# your_app/pipeline.py
def save_orcid_id(strategy, details, backend, user=None, *args, **kwargs):
    if backend.name == 'orcid':
        orcid_id = kwargs['response'].get('orcid')
        if orcid_id and user:
            user.profile.orcid_id = orcid_id
            user.profile.save()
