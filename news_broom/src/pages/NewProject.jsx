import { useState } from "react";
import { FaMicrophone, FaPaperPlane } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import axios from "axios"; // You'll need to install axios: npm install axios

// Add this at the top of your file to debug
console.log("Environment variables:", {
    VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
    MODE: import.meta.env.MODE,
    DEV: import.meta.env.DEV
});

const NewProject = () => {
    const navigate = useNavigate();
    const [topic, setTopic] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async () => {
        if (!topic.trim()) return;
        
        setIsLoading(true);
        try {
            // Access the environment variable
            const API_URL = "http://127.0.0.1:5000";
            console.log(API_URL)
            
            // const response = await axios.post("http://127.0.0.1:5000/api/gather_news_sources", {
            //     topic: topic
            // });
            
            // Store the response data in localStorage for use on the next page
            //localStorage.setItem("topicData", JSON.stringify(response.data));
            //console.log(response.data)
            // Navigate to the next page
            navigate("/generating-scenarios");
        } catch (error) {
            console.error("Error fetching news stories:", error);
            alert("Failed to fetch news stories. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-full text-center px-6">
            {/* Title */}
            <h1 className="text-2xl mt-20 font-semibold text-black mb-10">
                What do you want to build scenarios about?
            </h1>

            {/* Bottom Input Bar */}
            <div className="flex-1 m-20 flex items-end justify-center w-full">
                <div className="w-full max-w-3xl flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
                    <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
                    <input 
                        type="text" 
                        placeholder="Type message" 
                        className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                    />
                    <button 
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="flex items-center justify-center"
                    >
                        <FaPaperPlane className={`text-gray-500 text-xl ml-3 cursor-pointer ${isLoading ? 'opacity-50' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NewProject;