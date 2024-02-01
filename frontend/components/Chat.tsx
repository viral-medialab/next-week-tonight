import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faComment, faPaperPlane } from "@fortawesome/free-solid-svg-icons";

export default function Chat({ currentArticle }: any) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

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
            currentArticle,
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
                                            ? "bg-gray-600 w-full"
                                            : "bg-blue-500 w-full"
                                    } rounded-lg p-2`}
                                >
                                    {message.id % 2 !== 0 ? (
                                        <p className="text-white">{message.text}</p>
                                    ) : (
                                        <div className="grid grid-cols-3 gap-8 w-full">
                                          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                                            <div className="p-6">
                                              <h2 className="text-2xl font-bold mb-2">
                                                {message.text["article_0"]["title"]}
                                              </h2>
                                              <p className="text-gray-700 text-base">
                                                {message.text["article_0"]["body"]}
                                              </p>
                                            </div>
                                          </div>

                                          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                                            <div className="p-6">
                                              <h2 className="text-2xl font-bold mb-2">
                                                {message.text["article_1"]["title"]}
                                              </h2>
                                              <p className="text-gray-700 text-base">
                                                {message.text["article_1"]["body"]}
                                              </p>
                                            </div>
                                          </div>

                                          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                                            <div className="p-6">
                                              <h2 className="text-2xl font-bold mb-2">
                                                {message.text["article_2"]["title"]}
                                              </h2>
                                              <p className="text-gray-700 text-base">
                                                {message.text["article_2"]["body"]}
                                              </p>
                                            </div>
                                          </div>
                                        </div>
                                    )}
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
    currentArticle: any,
    messages: { id: number; text: string }[]
) {
    console.log("Current article id is:", currentArticle)
    console.log("User query is:", messages[messages.length - 1].text)
    const res = await fetch("http://127.0.0.1:5000/api/call_q2a_workflow", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ article_id: currentArticle, user_prompt: messages[messages.length - 1].text , verbose: true}),
    });
    console.log("Raw Response:", res);
    const data = await res.json();
    console.log("Function result:", data);
    return data;
}
function convertMessagesToAPIFormat(messages: { id: number; text: string }[]) {
    return messages.map((message) => ({
        role: message.id % 2 === 0 ? "user" : "system",
        content: message.text,
    }));
}