import { FaCommentDots, FaProjectDiagram, FaExclamationTriangle, FaMicrophone, FaPaperPlane } from "react-icons/fa";
import Logo from "../assets/images/Logo.png";

const HomePage = () => {
  return (
    <div className="flex flex-col items-center justify-between h-screen bg-white text-center px-6 py-10">
      {/* Logo (Top) */}
      <div className="flex-1 flex items-center justify-center">
        <img src={Logo} alt="News Broom Logo" className="h-20" />
      </div>

      {/* Three Sections: Examples, GraphRAG-based, Limitations (Middle) */}
      <div className="flex-1 flex items-center justify-center">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 max-w-5xl w-full">
          {/* Examples Section */}
          <div className="text-left">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FaCommentDots className="text-xl text-gray-600" /> Examples
            </h2>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">"What will happen to the mental health of US adolescents if TikTok is banned?"</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">"How will Singapore be affected by the Ukraine Russia Conflict?"</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">"What happens if DeepSeek gets acquired by OpenAI?"</p>
          </div>

          {/* GraphRAG-based Section */}
          <div className="text-left">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FaProjectDiagram className="text-xl text-gray-600" /> GraphRAG based
            </h2>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">Builds dynamic news graphs based on user queries & reputed online sources.</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">Reasons over local and global graph context to build predictive scenarios.</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">Generates multimodal predictive reports based on overall graph content.</p>
          </div>

          {/* Limitations Section */}
          <div className="text-left">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FaExclamationTriangle className="text-xl text-gray-600" /> Limitations
            </h2>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">May occasionally generate incorrect information.</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">May occasionally produce harmful instructions or biased content.</p>
            <p className="bg-gray-100 p-3 rounded-lg mt-2">Model starts with limited knowledge that gradually becomes better.</p>
          </div>
        </div>
      </div>

      {/* Bottom Input Bar */}
      <div className="flex-1 flex items-end justify-center w-full">
        <div className="w-full max-w-3xl flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
          <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
          <input 
            type="text" 
            placeholder="Type message" 
            className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
          />
          <FaPaperPlane className="text-gray-500 text-xl ml-3 cursor-pointer" />
        </div>
      </div>
    </div>
  );
};

export default HomePage;