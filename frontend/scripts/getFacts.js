const { Filter, ObjectId } = require("mongodb");
// fetch 
async function testGetFacts() {
    const { default: fetch } = await import("node-fetch");

    const topicId = new ObjectId("64ab1b2f9fc5ca5090a90c98") // Zuckerberg family pictures on Instagram

    fetch("http://127.0.0.1:3000/api/getNewsByTopicId",
    {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ topicId }),
    })
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                //get facts of these articles from /api/getFacts
                fetch(`http://127.0.0.1:3000/api/getFacts`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        topicAndArticles: data,
                    }),
                }).then((res) => res.json()).then((data) => {
                    console.log(data);
                })
            })
            .catch((err) => {
                console.log(err);
            });
}

testGetFacts();