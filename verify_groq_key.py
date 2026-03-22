from groq import Groq

def test_key(api_key):
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-8b-8192"  # Current recommended model
        )
        print("Key works! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("Key verification failed:", str(e))
        return False

test_key("youapikey")
