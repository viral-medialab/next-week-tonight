import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faComment, faPaperPlane } from "@fortawesome/free-solid-svg-icons";

export default function Chat({ topic, currentArticle, allArticles }: any) {
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
                            <>
                                <button
                                    className="text-blue-900 mb-1 text-left "
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Summarize the article I am currently reading."
                                        )
                                    }
                                >
                                    Summarize the article I am currently reading.
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "What is unique about the article I am reading?"
                                        )
                                    }
                                >
                                    What is unique about the article I am reading?
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Translate the first sentence of the article I am reading into spanish"
                                        )
                                    }
                                >
                                    Translate the first sentence of the article I am
                                    reading into spanish.
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "What is this topic about?"
                                        )
                                    }
                                >
                                    What is this topic about?
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Which article do you recommend I start with?"
                                        )
                                    }
                                >
                                    Which article do you recommend I start with?
                                </button>
                                <button
                                    className="text-blue-900 mb-1 text-left"
                                    onClick={() =>
                                        handleAskQuestion(
                                            "Compare the first and the second articles."
                                        )
                                    }
                                >
                                    Compare the first and the second articles.
                                </button>
                            </>
                        )}
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
async function submitMessages(
    topic: string,
    currentArticle: any,
    allArticles: any[],
    messages: { id: number; text: string }[]
) {
    const res = await fetch("/api/chat", {
        method: "POST",
        body: JSON.stringify({
            messages: convertMessagesToAPIFormat(messages),
            allArticles: allArticles,
            currentArticle: currentArticle,
            topicName: topic,
        }),
    });

    return res.text();
}
function convertMessagesToAPIFormat(messages: { id: number; text: string }[]) {
    return messages.map((message) => ({
        role: message.id % 2 === 0 ? "user" : "system",
        content: message.text,
    }));
}
