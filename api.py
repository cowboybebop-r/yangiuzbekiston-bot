import requests

r = requests.get('https://raw.githubusercontent.com/consik/yii2-websocket/master/composer.json')

print(r.text)