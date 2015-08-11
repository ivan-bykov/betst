from betst import get_handler

if __name__ == '__main__':
    sms_handler = get_handler('post.smsc.ru')
    print(len(sms_handler.send({'phone': '', 'text': ''})))
    sms_handler = get_handler('post.smsc.ru')
    print(len(sms_handler.send({'phone': '', 'text': ''})))
