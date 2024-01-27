import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faComment, faPaperPlane } from "@fortawesome/free-solid-svg-icons";

export default function Chat({ topic, currentArticle, allArticles }: any) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    /*
    FETCH QUERIES FROM api/questions
    useEffect(() => {
      if (currentArticle) {
        fetch("/api/questions", {
          method: "POST",
          body: JSON.stringify({
            currentArticle,
          }),
        })
          .then((res) => res.json())
          .then((data) => setQueries(data))
          .catch((error) => console.error("Error fetching queries:", error));
      }
    }, [currentArticle]);
    */

    const handleNewMessageChange = (
        event: React.ChangeEvent<HTMLTextAreaElement>
    ) => {
        setNewMessage(event.target.value);
    };

    const handleSendMessage = async () => {
        if (newMessage.trim() === "") return;
        setIsSubmitting(true);

        const messageSent = newMessage.trim();
        setNewMessage("");
        console.log("submitting message");
        const response = await submitMessages(
            topic,
            currentArticle,
            allArticles,
            [...messages, { id: messages.length + 1, text: newMessage.trim() }]
        );
        setMessages([
            ...messages,
            { id: messages.length + 1, text: messageSent },
            { id: messages.length + 2, text: response },
        ]);
        console.log("got response", response);
        setIsSubmitting(false);
    };

    const handleAskQuestion = (question: string) => {
        setNewMessage(question);
        const textarea = document.getElementById("message-box");
        if (textarea) {
            textarea.focus();
        }
    };
    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    };

    return (
        currentArticle && (
                <div className="flex flex-col p-4 border-t">
                    <div className="flex flex-col items-start w-full ">
                        <span className="text-gray-500">Try asking:</span>
                        {currentArticle ? (
                            /*
                            CODE TO ADD LINKED TEXT BUTTONS WITH GENERATED QUERIES FROM api/questions
                            <>
                              {queries.map((query, index) => (
                                <button
                                  key={index}
                                  className="text-blue-900 mb-1 text-left"
                                  onClick={() => handleAskQuestion(query)}
                                >
                                  {query}
                                </button>
                              ))}
                            </>
                            */
                            <>
                                <button
                                    className="text-blue-900 mb-1 text-left "
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Question 1" // Summarize the article I am currently reading.
                                        )
                                    }
                                >
                                    Question 1
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Question 2" // What is unique about the article I am reading?
                                        )
                                    }
                                >
                                    Question 2
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Question 3" // Translate the first sentence of the article I am reading into spanish
                                        )
                                    }
                                >
                                    Question 3
                                </button>
                            </>
                        ) : null}
                    </div>

                    <div className="flex items-center mt-4 w-full">
                        <textarea
                            placeholder="Type your message here"
                            className="flex-1 border rounded-lg py-2 px-4 mr-4 resize-none"
                            id="message-box"
                            value={newMessage}
                            onChange={handleNewMessageChange}
                            onKeyDown={handleKeyDown}
                        />
                        <button
                            className="bg-gray-500 text-white rounded-full p-2 hover:bg-gray-600"
                            onClick={handleSendMessage}
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? (
                                "Loading..."
                            ) : (
                                <FontAwesomeIcon
                                    icon={faPaperPlane}
                                    size="sm"
                                    className="h-6 w-6"
                                />
                            )}
                        </button>
                    </div>
                    <div className="flex flex-col h-full">
                        <div className="flex-1 p-4 overflow-y-auto">
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`${
                                        message.id % 2 === 0
                                            ? "justify-end"
                                            : "justify-start"
                                    } flex mb-4`}
                                >
                                    <div
                                        className={`${
                                            message.id % 2 === 0
                                                ? "bg-blue-500"
                                                : "bg-gray-600"
                                        } rounded-lg p-2 max-w-xs`}
                                    >
                                        <p className="text-white">{message.text}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                </div>
            </div>
        )
    );
}

// Define an interface for the data structure you expect to receive as a response
interface ApiResponse {
  // Assuming the structure of your response; adjust according to your actual API response
  success: boolean;
  message?: string;
  [key: string]: any; // For additional properties that might be dynamic
}

async function callQ2AWorkflow(): Promise<ApiResponse | undefined> {
  const dataToSend = {
    article_id: "BB1hgzNq",
    user_prompt: "What happens if immigration becomes a key issue in the election?",
  };

  try {
    const response = await fetch('http://localhost:5000/api/call_q2a_workflow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dataToSend),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: ApiResponse = await response.json(); // Explicitly typing the response data
    console.log("Function result:", data);
    return data;
  } catch (error) {
    console.error('Error:', error);
    return undefined; // Handle error cases or throw an error as needed
  }
}

async function submitMessages(
    topic: string,
    currentArticle: any,
    allArticles: any[],
    messages: { id: number; text: string }[]
) {
//         const res = await fetch('http://localhost:5000/api/call_q2a_workflow', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({ article_id: "BB1hgzNq", user_prompt: "What happens if immigration becomes a key issue in the election?" }),
//         })
//         .then(response => response.json())
//         .then(data => console.log("Function result:", data))
//         .catch(error => console.error('Error:', error));
        // To call the function and handle the result
//         const res = callQ2AWorkflow().then(data => {
//                       if (data) {
//                         // Do something with the data here
//                         console.log("Received data:", data);
//                       }
//                       else {
//                         console.log("No Data");
//                       }
//                     });
//     const res = await fetch("/api/chat", {
//         method: "POST",
//         body: JSON.stringify({
//             messages: convertMessagesToAPIFormat(messages),
//             allArticles: allArticles,
//             currentArticle: currentArticle,
//             topicName: topic,
//         }),
//     });
    const res = await fetch("http://127.0.0.1:5000/api/call_q2a_workflow", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ article_id: "BB1hgzNq", user_prompt: "What happens if immigration becomes a key issue in the election?" , verbose: true}),
    }).then((response) => response.json()).then(response => console.log("Function result:", response));
    return res;
    // return res.text();
}
function convertMessagesToAPIFormat(messages: { id: number; text: string }[]) {
    return messages.map((message) => ({
        role: message.id % 2 === 0 ? "user" : "system",
        content: message.text,
    }));
}
