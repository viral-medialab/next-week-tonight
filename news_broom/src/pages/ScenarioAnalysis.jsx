import { useState, useEffect } from "react";
import { FaMicrophone, FaPaperPlane, FaUserCircle, FaCheck, FaTimes } from "react-icons/fa";
import { useLocation } from "react-router-dom";

const ScenarioAnalysis = () => {
  const location = useLocation();
  const userInput = location.state?.userInput || "";

  const [progress, setProgress] = useState(-1); // Start from -1 so steps appear one by one
  const [showParagraph, setShowParagraph] = useState(false);

  const steps = [
    "Generating base answer to question...",
    "Checking if this sufficiently answers the question...",
    "Gathering more News Sources on new topic...",
    "Summarizing Individual Reports...",
    "Updating Graph...",
    "Generating Key Findings...",
  ];

  useEffect(() => {
    if (progress < steps.length) {
      const timer = setTimeout(() => {
        setProgress((prev) => prev + 1);
      }, 1000); // 1-second delay per step

      return () => clearTimeout(timer);
    } else {
      setTimeout(() => setShowParagraph(true), 1000); // Show paragraph after steps complete
    }
  }, [progress]);

  return (
    <div className="flex flex-col items-center justify-start h-full text-center px-6 py-10 overflow-y-auto max-h-screen">
      {/* Display Previous Content */}
      <div className="flex flex-col w-full max-w-4xl">
        
        {/* Older Question */}
        <div className="flex items-center gap-3 mb-4">
          <FaUserCircle className="text-3xl text-gray-600" />
          <h1 className="text-lg font-semibold text-black text-left flex-1">{userInput}</h1>
        </div>

        {/* Initial Findings */}
        <div className="bg-gray-200 text-black font-semibold rounded-md p-3 text-left text-sm flex justify-between">
          <span>Initial Findings based on initial Graph:</span>
          <span className="text-lg">◀</span>
        </div>

        {/* Summary Section */}
        <div className="bg-gray-300 text-black font-semibold rounded-md p-3 text-left text-sm flex justify-between mt-2">
          <span>Summary of the possible scenarios surrounding the TikTok ban in the US:</span>
          <span className="text-lg">◀</span>
        </div>

        {/* New User Question */}
        <div className="flex items-center gap-3 mt-4">
          <FaUserCircle className="text-3xl text-gray-600" />
          <h1 className="text-lg font-semibold text-black text-left flex-1">What will be the effect of ByteDance divesting from TikTok on American Youth?</h1>
        </div>

        {/* Step-by-step Loading */}
        <div className="text-right justify-end max-w-4xl w-full mb-6 ml-auto mt-4">
          {steps.map((step, index) => (
            <div key={index} className={`flex items-center gap-3 font-semibold text-gray-900 mb-2 ${index > progress ? "hidden" : ""}`}>
              <span>{step}</span>
              {index < progress ? (
                <>
                  {index === 1 ? <FaTimes className="text-red-500 text-lg" /> : <FaCheck className="text-black text-lg" />}
                  <span className="text-gray-700 text-lg">◀</span>
                </>
              ) : (
                <span className="text-gray-400">...</span> // Pending dots
              )}
            </div>
          ))}
        </div>

        {/* Final Paragraph (Appears after all steps are completed) */}
        {showParagraph && (
          <div className="bg-gray-100 p-4 rounded-lg max-w-4xl w-full text-left mt-4">
            <p className="text-gray-700 font-semibold">
              Possible repercussions on the youth of America if ByteDance divests from TikTok are:
            </p>
            <ul className="list-disc ml-6 text-gray-700 mt-2">
              <li>
                <strong>Ownership Change Impact:</strong> ByteDance's TikTok divestment represents a significant shift in platform control affecting nearly 200 million US users.
              </li>
              <li>This transition in ownership structure could fundamentally reshape the platform's operations and governance.</li>
              <li>
                <strong>National Security Considerations:</strong> Divestment addresses concerns about Chinese government data access.
              </li>
              <li>Potential increased trust in TikTok's privacy practices among American users and government regulators.</li>
              <li>
                <strong>Mental Health Implications:</strong> Could influence ongoing debates about social media's impact on adolescent mental health.
              </li>
              <li>Potential shifts in content algorithms and safety features under new ownership.</li>
              <li>
                <strong>Regulatory Precedent:</strong> Changes in content moderation and data handling may establish new standards.
              </li>
              <li>Could set precedent for how foreign-owned technology platforms operate within the United States.</li>
            </ul>
          </div>
        )}
      </div>

      {/* Bottom Input Box */}
      <div className="w-full max-w-4xl mt-10 flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
        <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
        <input type="text" placeholder="Type message" className="flex-1 outline-none bg-transparent text-gray-700 text-sm" />
        <FaPaperPlane className="text-gray-500 text-xl ml-3 cursor-pointer" />
      </div>
    </div>
  );
};

export default ScenarioAnalysis;