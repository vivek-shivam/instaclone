from clarifai import rest
from clarifai.rest import ClarifaiApp

import clarifai
from clarifai.rest import ClarifaiApp

app = ClarifaiApp(api_key='b97f3b583d9149798fbf429dc82277f2')


model = app.models.get('general-v1.3')

a=model.predict_by_url(url='https://samples.clarifai.com/metro-north.jpg')
print a['outputs'][0]['id']