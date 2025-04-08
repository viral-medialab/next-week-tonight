import { FaArrowLeft } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import Graph from "../assets/images/graph.png";

const KnowledgeGraphPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-full p-10">
      {/* Title */}
      <h1 className="text-2xl font-semibold mb-6">TikTok Ban by the US Government</h1>

      {/* Graph Placeholder - Replace with actual graph component if needed */}
      <div className="w-full max-w-10xl bg-gray-200 rounded-lg  flex items-center justify-center">
        <img src={Graph} />
      </div>

      {/* Back Button */}
      <button
        className="mt-6 px-6 py-3 bg-gray-100 border rounded-lg flex items-center gap-2 hover:bg-gray-200 transition"
        onClick={() => navigate(-1)}
      >
        <FaArrowLeft className="text-gray-600" />
        Go back to the Editorial
      </button>
    </div>
  );
};

export default KnowledgeGraphPage;