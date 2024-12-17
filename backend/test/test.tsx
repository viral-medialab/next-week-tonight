const dataToSend = { article_id: "BB1hgzNq", user_prompt: "What happens if immigration becomes a key issue in the election?" };

fetch('http://localhost:5000/api/test', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(dataToSend), 
})
.then(response => response.json())
.then(data => console.log("Function result:", data))
.catch(error => console.error('Error:', error));