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
    const [error, setError] = useState(null);
    const [progress, setProgress] = useState(""); // For showing progress updates

    const handleSubmit = async () => {
        if (!topic.trim()) return;
        
        setIsLoading(true);
        setError(null);
        setProgress("Gathering news sources...");
        
        try {
            const API_URL = "http://127.0.0.1:5000";
            
            // Make the API call with the correct parameter name (query, not topic)
            const response = await axios.post(`${API_URL}/api/gather_news_sources`, {
                query: topic
            });
            
            if (response.data.status === "success") {
                setProgress(`Found ${response.data.data.num_sources} sources!`);
                
                // Store the complete response data in localStorage
                localStorage.setItem("topicData", JSON.stringify({
                    ...response.data,
                    topic: topic // Add the original topic for use in other components
                }));
                
                // Short delay to show success message before navigating
                setTimeout(() => {
                    navigate("/generating-scenarios");
                }, 1000);
            } else {
                throw new Error(response.data.message || "Failed to gather news sources");
            }
            
        } catch (error) {
            console.error("Error fetching news stories:", error);
            setError(
                error.response?.data?.message || 
                error.message || 
                "Failed to fetch news sources. Please try again."
            );
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

            {/* Progress and Error Messages */}
            {isLoading && (
                <div className="mb-4">
                    <div className="animate-pulse text-blue-600">{progress}</div>
                    <div className="mt-2">
                        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    </div>
                </div>
            )}
            
            {error && (
                <div className="mb-4 text-red-500 bg-red-50 p-3 rounded-lg">
                    {error}
                </div>
            )}

            {/* Bottom Input Bar */}
            <div className="flex-1 m-20 flex items-end justify-center w-full">
                <div className="w-full max-w-3xl flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
                    <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
                    <input 
                        type="text" 
                        placeholder="Type a topic to analyze (e.g., 'AI safety' or 'climate change')" 
                        className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSubmit()}
                        disabled={isLoading}
                    />
                    <button 
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className={`flex items-center justify-center transition-opacity ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'}`}
                    >
                        <FaPaperPlane className="text-gray-500 text-xl ml-3" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NewProject;