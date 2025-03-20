import { useEffect, useState } from "react";
import { FaMicrophone, FaPaperPlane, FaUserCircle, FaCheck } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

const GeneratingScenarios = () => {
  const [progress, setProgress] = useState(-1); // Start at -1
  const [showParagraph, setShowParagraph] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const steps = [
    "Gathering News Sources...",
    "Summarizing Individual Reports...",
    "Creating Graph...",
    "Generating Key Findings...",
  ];

  const handleSend = () => {
    if (message.trim() === "") return;
    navigate("/scenario-analysis", { state: { userInput: message } });
  };

  // First useEffect to load data from localStorage
  useEffect(() => {
    const storedData = localStorage.getItem("topicData");
    if (storedData) {
      const parsedData = JSON.parse(storedData);
      setData(parsedData);
      // Set first step as complete immediately when data is loaded
      setProgress(0);
      setIsLoading(false);
    } else {
      // Redirect if no data
      navigate("/new-project");
    }
  }, [navigate]);

  // Second useEffect to handle the remaining steps with timer
  useEffect(() => {
    // Only start the timer after data is loaded and first step is marked complete
    if (progress >= 0 && progress < steps.length - 1) {
      const timer = setTimeout(() => {
        setProgress((prev) => prev + 1);
      }, 1000);
      
      return () => clearTimeout(timer);
    } else if (progress >= steps.length - 1) {
      // Show paragraph after all steps are complete
      setTimeout(() => setShowParagraph(true), 1000);
    }
  }, [progress, steps.length]);

  // If still loading initial data
  if (isLoading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="flex flex-col items-center justify-start h-full text-center px-6 py-10">
      {/* User Input */}
      <div className="flex items-center gap-3 mb-6 w-full max-w-3xl">
        <FaUserCircle className="text-3xl text-gray-600" />
        <h1 className="text-xl font-semibold text-black text-left flex-1">
          {/* Display the topic from the API response */}
          Build all possible scenarios around {data?.topic || "the TikTok Ban by the US Government"}.
        </h1>
      </div>

      {/* Step-by-step Loading - FULLY RIGHT-ALIGNED */}
      <div className="flex flex-col items-end max-w-3xl w-full mb-6 ml-auto">
        {steps.map((step, index) => (
          <div key={index} className={`flex items-center gap-3 font-semibold text-gray-900 mb-2 ${index > progress ? "hidden" : ""}`}>
            <span>{step}</span>
            {index <= progress ? (
              <>
                <FaCheck className="text-black text-lg" /> {/* Black tick */}
                <span className="text-gray-700 text-lg">◀</span> {/* Left arrow */}
              </>
            ) : (
              <span className="text-gray-400">...</span> // Pending dots
            )}
          </div>
        ))}
      </div>

      {/* Final Paragraph (Appears after all steps are completed) */}
      {showParagraph && (
        <div className="bg-gray-100 p-4 rounded-lg max-w-3xl w-full text-left">
          <p className="text-gray-700 font-semibold">
            Here's a summary of the possible scenarios surrounding {data?.topic || "the TikTok ban in the US"}:
          </p>
          
          {/* Show either API-provided stories or the default list */}
          {data?.stories ? (
            <div className="space-y-4 mt-4">
              {data.stories.map(story => (
                <div key={story.id} className="p-4 border rounded-lg shadow-sm">
                  <h2 className="text-lg font-semibold">{story.title}</h2>
                  <p className="text-sm text-gray-600">{story.source} • {story.published_date}</p>
                  <a 
                    href={story.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline text-sm"
                  >
                    Read more
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <ol className="list-decimal ml-6 text-gray-700 mt-2">
              <li><strong>Full Ban Enforcement:</strong> The Supreme Court upholds the ban, leading to TikTok's removal from app stores and potential ISP blocking.</li>
              <li><strong>ByteDance Divestment:</strong> TikTok is sold to a US-based company or consortium, allowing it to continue operations.</li>
              <li><strong>Trump Administration Action:</strong> The incoming Trump administration delays the ban or revives "Project Texas" for data management by Oracle.</li>
              <li><strong>Legal/Political Reversal:</strong> Congress amends the law, or new legal challenges lead to judicial reconsideration.</li>
              <li><strong>Partial Compliance:</strong> ByteDance attempts legal maneuvers or TikTok implements limited functionality for US users.</li>
              <li><strong>Permanent Ban:</strong> If no solutions are found, TikTok faces a complete shutdown in the US.</li>
            </ol>
          )}
        </div>
      )}

      {/* Bottom Input Box */}
      <div className="w-full max-w-3xl mt-10 flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
        <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
        <input
          type="text"
          placeholder="Type message"
          className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <FaPaperPlane className="text-gray-500 text-xl ml-3 cursor-pointer" onClick={handleSend} />
      </div>
    </div>
  );
};

export default GeneratingScenarios;