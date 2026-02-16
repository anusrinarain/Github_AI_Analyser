
from google import genai

client = genai.Client(api_key="AIzaSyBjxccLrYEIUPxqUPhg2vocMeMP0Kz8xM4")

for m in client.models.list():
    print(m.name)
