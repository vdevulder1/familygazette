from django import template

register = template.Library()

@register.simple_tag
def unseen_messages_conv(conversation, user):

    html = ''

    unread_messages = conversation.unseen_messages_count(user)
    if unread_messages != 0 :
        html = "<span class='badge badge-primary badge-pill' id='notifsConv{0}'>{1}</span>".format(conversation.id, unread_messages)
    
    return html

@register.simple_tag
def unseen_messages_user(user):

    html = ''

    unread_messages = user.unseenMessages()
    if unread_messages != 0 :
        html = "<span class='badge badge-primary badge-pill' id='notifsSidebar' >{0}</span>".format(unread_messages)
    
    return html

@register.simple_tag
def unseen_posts_family(family, user):

    html = ''

    unread_posts = family.unseen_posts_count(user)
    if unread_posts != 0 :
        html = "<span class='badge badge-primary badge-pill' id='notifsPostFamily{0}'>{1}</span>".format(family.id, unread_posts)
    
    return html

@register.simple_tag
def unseen_gazettes_family(family, user):

    html = ''

    unseen_gazettes = family.unseen_gazettes_count(user)
    if unseen_gazettes != 0 :
        html = "<span class='badge badge-primary badge-pill' id='notifsGazetteFamily{0}'>{1}</span>".format(family.id, unseen_gazettes)
    
    return html

@register.simple_tag
def unseen_elements_family(family, user):

    html = ''

    unseen_elements = family.unseen_elements_count(user)
    if unseen_elements != 0 :
        html = "<span class='badge badge-primary badge-pill' id='notifsFamily{0}'>{1}</span>".format(family.id, unseen_elements)
    
    return html