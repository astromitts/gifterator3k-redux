from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pdb(item):
    import pdb
    pdb.set_trace()

@register.filter
def format_date_time(datetime):
    return mark_safe(datetime.strftime('%b %d<br /> %H:%M %p %Z'))

@register.filter
def as_money(integer):
    return '${}'.format(integer)

@register.filter
def display_user_information(information):
    if information:
        return information
    else:
        return "None"

@register.filter
def display_likes(participant):
    if participant.likes:
        return '{} likes: {}'.format(
            participant.first_name, participant.likes)
    else:
        return '{} likes nothing, apparently. good luck!'.format(
            participant.first_name)

@register.filter
def display_dislikes(participant):
    if participant.dislikes:
        return '{} dislikes: {}'.format(
            participant.first_name, participant.dislikes)
    else:
        return "{} dislikes nothing, apparently. That's good news!".format(
            participant.first_name)

@register.filter
def display_allergies(participant):
    if participant.allergies_or_sensitivities:
        return '{} reported the following allergies/sensitivies: {}'.format(
            participant.first_name, participant.allergies_or_sensitivities)
    else:
        return '{} reported no allergies or sensitivies'.format(
            participant.first_name)

