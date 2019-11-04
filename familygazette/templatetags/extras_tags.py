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