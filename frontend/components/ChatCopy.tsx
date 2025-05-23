import "dotenv/config";
import Head from "next/head";
import { Ring } from "@uiball/loaders";
import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faComment, faPaperPlane } from "@fortawesome/free-solid-svg-icons";

interface ChatProps {
  currentArticle: {
    id: string;
    url: string;
  }
}

export default function Chat({ currentArticle }: ChatProps) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [questions, setQuestions] = useState<string[]>([]);

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
            response,
        ]);
        console.log("got response", response);
        setIsSubmitting(false);
    };

    const handleAskQuestion = (question: string) => {
        question = question.substring(4);
        if (question[0] !== " ") {
            question = " " + question;
        }
        setNewMessage("What happens if" + question);
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

    useEffect(() => {
        console.log("ChatCopy useEffect triggered. currentArticle:", currentArticle);
        const fetchWhatIfQuestions = async () => {
          if(currentArticle){
            console.log("Fetching what-if questions for article:", currentArticle.id);
            try{
              console.log("HELLO")
              const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:5000'; // Fallback URL
              const response = await fetch(`${backendUrl}//api/generate_what_if_questions`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ article_id: currentArticle.id, articleUrl: currentArticle.url}),
              });
              if (!response.ok) {
                throw new Error(`Network response was not ok`);
              }
              const data = await response.json();
              console.log("data: ", data)
              const fetchedQuestions = Object.keys(data).map((key) => data[key]);
              setQuestions(fetchedQuestions);
            } catch
            (error) {
              console.error("Failed to fetch what-if questions:", error);
            }
          }
        };
        fetchWhatIfQuestions();
    }, [currentArticle]);

    return (
        currentArticle && (
            <div className="flex flex-col p-4 border-t">
                <div className="flex flex-col items-start w-full">
                    <span className="text-gray-500">What happens if:</span>
                    {questions && questions.map((question, index) => (
                        <button key={index} className="text-blue-900 mb-1 text-left" onClick={() => handleAskQuestion(question)}>
                            {question}
                        </button>
                    ))}
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
                        {isSubmitting ? "Loading..." : <FontAwesomeIcon icon={faPaperPlane} size="sm" className="h-6 w-6"/>}
                    </button>
                </div>
    
                <div className="flex flex-col h-full">
                <div className="flex-1 p-4 overflow-y-auto">
                    {/* Assuming messages[messages.length - 1] is the response with the articles */}
                    {messages.length > 0 && (
                        <div className="grid grid-cols-3 gap-4">
                            {Array.from({ length: 9 }).map((_, index) => {
                                const articleKey = `article_${index}`;
                                const article = messages[messages.length - 1][articleKey];
                                
                                if (!article) return null;

                                return (
                                    <div key={article.id} className="bg-white rounded-lg shadow-lg overflow-hidden p-6">
                                        <a href={`/article/${article.id}`}>
                                            <h2 className="text-2xl font-bold mb-2">{article.title}</h2>
                                            <p className="text-gray-700 text-base">{article.body.split('.')[0] + "..."}</p>
                                            <button className="text-blue-500 font-bold hover:text-blue-700 mt-4">Read more</button>
                                        </a>
                                        
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
        )
    );
}

async function submitMessages(
    currentArticle: any,
    messages: { id: number; text: string }[]
) {
    console.log("Current article id is:", currentArticle.id)
    console.log("User query is:", messages[messages.length - 1].text)
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:5000';
    const res = await fetch(`${backendUrl}/api/call_q2a_workflow`, {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ article_id: currentArticle.id, articleUrl: currentArticle.url, user_prompt: messages[messages.length - 1].text , verbose: true}),
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