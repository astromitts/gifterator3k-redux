from django import template

register = template.Library()


@register.filter
def pdb(item):
    import pdb
    pdb.set_trace()

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
            participant.user.first_name, participant.likes)
    else:
        return '{} likes nothing, apparently. good luck!'.format(
            participant.user.first_name)

@register.filter
def display_dislikes(participant):
    if participant.dislikes:
        return '{} dislikes: {}'.format(
            participant.user.first_name, participant.dislikes)
    else:
        return "{} dislikes nothing, apparently. That's good news!".format(
            participant.user.first_name)

@register.filter
def display_allergies(participant):
    if participant.allergies_or_sensitivities:
        return '{} reported the following allergies/sensitivies: {}'.format(
            participant.user.first_name, participant.allergies_or_sensitivities)
    else:
        return '{} reported no allergies or sensitivies'.format(
            participant.user.first_name)

