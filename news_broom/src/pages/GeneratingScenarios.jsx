import { useEffect, useState } from "react";
import { FaMicrophone, FaPaperPlane, FaUserCircle, FaCheck } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const GeneratingScenarios = () => {
  const [progress, setProgress] = useState(-1); // Start at -1
  const [showParagraph, setShowParagraph] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const steps = [
    "Gathering News Sources...",
    "Generating Key Findings...",
    "Creating Graph...",
  ];

  const handleSend = () => {
    if (message.trim() === "") return;
    navigate("/scenario-analysis", { state: { userInput: message } });
  };

  // Execute step 1 - Gather News Sources
  const executeStep1 = async (topicData) => {
    try {
      // Check if we already have sources data from the previous step
      if (topicData.data && topicData.data.num_sources) {
        console.log(`Already gathered ${topicData.data.num_sources} news sources (${topicData.data.successful_extractions} successful extractions)`);
        
        // Show extraction details in a formatted way for debugging
        if (topicData.data.sources && topicData.data.sources.length > 0) {
          console.log("Extraction details available in topicData");
        }
        
        // Just display progress for a brief moment to show the step
        setTimeout(() => {
          setProgress(0); // Mark step 1 as complete
          executeStep2(topicData); // Proceed to step 2
        }, 1500);
      } else {
        // This branch shouldn't normally run if NewProject.jsx worked correctly
        console.warn("No source data found in topicData, this is unexpected");
        
        // Rather than re-fetching (which would be slow), let's just move to the next step
        setTimeout(() => {
          setProgress(0); // Mark step 1 as complete anyway
          executeStep2(topicData); // Proceed to step 2
        }, 1000);
      }
    } catch (error) {
      console.error("Error handling news sources step:", error);
      // Move to next step anyway to avoid blocking the user
      setTimeout(() => {
        setProgress(0);
        executeStep2(topicData);
      }, 1000);
    }
  };

  // Execute step 2 - Generate Scenarios
  const executeStep2 = async (topicData) => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/generate_scenarios", {
        topic: topicData.topic
      });
      
      if (response.data.status === "success") {
        setProgress(1); // Mark step 2 as complete
        executeStep3(topicData); // Proceed to step 3
      } else {
        console.error("Failed to generate scenarios:", response.data);
      }
    } catch (error) {
      console.error("Error generating scenarios:", error);
    }
  };

  // Execute step 3 - Create Knowledge Graph
  const executeStep3 = async (topicData) => {
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/create_knowledge_graph", {
        topic: topicData.topic
      });
      
      if (response.data.status === "success") {
        setProgress(2); // Mark step 3 as complete
        setTimeout(() => setShowParagraph(true), 1000); // Show final paragraph
      } else {
        console.error("Failed to create knowledge graph:", response.data);
      }
    } catch (error) {
      console.error("Error creating knowledge graph:", error);
    }
  };

  // First useEffect to load data from localStorage and start the process
  useEffect(() => {
    const storedData = localStorage.getItem("topicData");
    if (storedData) {
      const parsedData = JSON.parse(storedData);
      setData(parsedData);
      setIsLoading(false);
      
      // Start the sequence by executing step 1
      executeStep1(parsedData);
    } else {
      // Redirect if no data
      navigate("/new-project");
    }
  }, [navigate]);

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