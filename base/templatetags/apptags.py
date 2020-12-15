from django import template

register = template.Library()

@register.filter
def pdb(item):
    """ Helper for dropping into PDB from a template
    """
    import pdb
    pdb.set_trace()
