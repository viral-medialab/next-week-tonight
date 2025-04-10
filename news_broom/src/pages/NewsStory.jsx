import { useState, useEffect } from "react";
import { FaCheck } from "react-icons/fa";
import ReactPlayer from "react-player";
import { useNavigate } from "react-router-dom";

const NewsStory = () => {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(-1);
  const [showVideo, setShowVideo] = useState(false);

  const steps = [
    "Generating News story script...",
    "Hiring AI John Oliver as voice actor...",
    "Generating supporting visuals...",
  ];

  useEffect(() => {
    if (progress < steps.length) {
      const timer = setTimeout(() => {
        setProgress((prev) => prev + 1);
      }, 1000);

      return () => clearTimeout(timer);
    } else {
      setTimeout(() => setShowVideo(true), 1000); // Show video after steps complete
    }
  }, [progress]);

  return (
    <div className="flex flex-col items-center justify-start h-full text-center px-6 py-10">
      {/* Title */}
      <h1 className="text-2xl font-bold text-black mb-6">
        TikTok Ban by the US Government + American Teen Mental Health
      </h1>

      {/* Step-by-step Loading */}
      <div className="text-right justify-end max-w-3xl w-full mb-6 ml-auto">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`flex items-center gap-3 font-semibold text-gray-900 mb-2 ${
              index > progress ? "hidden" : ""
            }`}
          >
            <span>{step}</span>
            {index < progress ? (
              <>
                <FaCheck className="text-black text-lg" />
                <span className="text-gray-700 text-lg">◀</span>
              </>
            ) : (
              <span className="text-gray-400">...</span> // Pending dots
            )}
          </div>
        ))}
      </div>

      {/* Video Player */}
      {showVideo && (
        <div className="bg-gray-100 p-4 rounded-lg max-w-3xl w-full text-left mt-4 flex flex-col items-center">
          <ReactPlayer
            url="https://www.youtube.com/watch?v=D0UnqGm_miA"
            controls
            width="100%"
            height="400px"
          />
          <button
            className="bg-black text-white py-2 px-6 mt-4 rounded-md"
            onClick={() => alert("Downloading video...")}
          >
            Download video
          </button>
        </div>
      )}

      {/* Back Button */}
      <button
        className="mt-6 bg-gray-200 text-black py-2 px-6 rounded-md flex items-center gap-2"
        onClick={() => navigate(-1)}
      >
        ⬅ Go back to the Editorial
      </button>
    </div>
  );
};

export default NewsStory;