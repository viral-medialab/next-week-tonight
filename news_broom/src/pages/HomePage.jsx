import { useState, useEffect, useRef } from "react";
import { FaCommentDots, FaProjectDiagram, FaExclamationTriangle, FaMicrophone, FaPaperPlane, FaSpinner, FaChevronDown, FaChevronUp, FaArrowLeft, FaUserCircle } from "react-icons/fa";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import ForceGraph2D from "react-force-graph-2d";
import ForceGraph3D from "react-force-graph-3d";
import Logo from "../assets/images/Logo.png";

const HomePage = () => {
  const [userInput, setUserInput] = useState("");
  const [followUpInput, setFollowUpInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [topicOverview, setTopicOverview] = useState(null);
  const [error, setError] = useState(null);
  const [showSections, setShowSections] = useState(true);
  const [gatheringComplete, setGatheringComplete] = useState(false);
  const [isOverviewExpanded, setIsOverviewExpanded] = useState(false);
  const [submittedQuery, setSubmittedQuery] = useState(""); // Store the submitted query for display
  const [numSources, setNumSources] = useState(0);
  const [creatingGraph, setCreatingGraph] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [graphReady, setGraphReady] = useState(false);
  const [view3D, setView3D] = useState(false);
  const [graphWarning, setGraphWarning] = useState(null);
  const [followUpResponse, setFollowUpResponse] = useState(null);
  const [showFollowUpResponse, setShowFollowUpResponse] = useState(false);

  // Graph refs and state
  const graphRef = useRef();
  const containerRef = useRef();
  const [size, setSize] = useState({ w: 800, h: 400 });
  const [hoverNode, setHoverNode] = useState(null);
  const [hoverLink, setHoverLink] = useState(null);

  // Set container size on mount and window resize
  useEffect(() => {
    function handleResize() {
      if (containerRef.current) {
        setSize({
          w: containerRef.current.offsetWidth,
          h: 400 // Fixed height
        });
      }
    }
    
    handleResize(); // Initial size
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Zoom to fit when graph data changes
  useEffect(() => {
    if (graphRef.current && graphData.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current.zoomToFit(400);
      }, 500);
    }
  }, [graphData]);

  useEffect(() => {
    if (graphData) {
      const hasValidGraphData = 
        graphData.nodes && 
        graphData.nodes.length > 0 && 
        graphData.links && 
        graphData.links.length > 0;
        
      if (!hasValidGraphData) {
        console.warn("Graph data is present but empty or invalid", graphData);
        // Show appropriate UI message
        setGraphWarning("The knowledge graph has insufficient data to display. Try a different topic with more sources.");
      } else {
        setGraphWarning(null);
      }
    }
  }, [graphData]);

  const handleInputChange = (e) => {
    setUserInput(e.target.value);
  };

  const handleFollowUpInputChange = (e) => {
    setFollowUpInput(e.target.value);
  };

  const toggleOverview = () => {
    setIsOverviewExpanded(!isOverviewExpanded);
  };

  const handleBackToHome = () => {
    setShowSections(true);
    setTopicOverview(null);
    setError(null);
    setIsLoading(false);
    setGatheringComplete(false);
    setGraphData({ nodes: [], links: [] });
    setGraphReady(false);
    setCreatingGraph(false);
  };

  // Function to process text and convert URLs to markdown links
  const processTextWithLinks = (text) => {
    if (!text) return "";
    
    // URL regex pattern - matches URLs starting with http://, https://, or www.
    const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/g;
    
    // Replace URLs with markdown link format
    return text.replace(urlRegex, (url) => {
      const linkUrl = url.startsWith('www.') ? `https://${url}` : url;
      return `[${url}](${linkUrl})`;
    });
  };

  const createKnowledgeGraphWithQuery = async (query) => {
    try {
      setCreatingGraph(true);
      const API_URL = "http://127.0.0.1:5000";
      
      console.log("Creating knowledge graph for query:", query);
      
      // Single API call to create_knowledge_graph, which now also returns the graph data
      const graphResponse = await axios.post(`${API_URL}/api/create_knowledge_graph`, {
        query: query
      });
      
      // The response now directly contains the graph data (nodes and links)
      if (graphResponse.data && (graphResponse.data.nodes || graphResponse.data.links)) {
        setGraphData(graphResponse.data);
        setGraphReady(true);
      } else {
        // Create a minimal graph if response doesn't have expected data
        console.warn("Creating minimal graph - received:", graphResponse.data);
        
        const minimalGraph = {
          nodes: [
            { id: "Query", label: query, group: "central" },
            { id: "GraphRAG", label: "GraphRAG", group: "system" }
          ],
          links: [
            { source: "GraphRAG", target: "Query", value: 1 }
          ]
        };
        
        setGraphData(minimalGraph);
        setGraphReady(true);
      }
    } catch (error) {
      console.error("Error creating knowledge graph:", error);
      setError(
        error.response?.data?.message || 
        error.message || 
        "Failed to create knowledge graph. Please try again."
      );
    } finally {
      setCreatingGraph(false);
    }
  };

  const handleSubmit = async () => {
    if (!userInput.trim()) return;

    // Save the query for display
    setSubmittedQuery(userInput);
    const currentQuery = userInput; // Store in local variable to ensure consistency

    // Reset states
    setIsLoading(true);
    setError(null);
    setTopicOverview(null);
    setShowSections(false);
    setGatheringComplete(false);
    setIsOverviewExpanded(false);
    setGraphData({ nodes: [], links: [] });
    setGraphReady(false);
    setCreatingGraph(false);

    try {
      // First call gather_news_sources
      const API_URL = "http://127.0.0.1:5000";
      
      const gatherResponse = await axios.post(`${API_URL}/api/gather_news_sources`, {
        query: currentQuery
      });

      if (gatherResponse.data.status === "success") {
        setGatheringComplete(true);
        
        // Store the number of sources
        if (gatherResponse.data.data && gatherResponse.data.data.num_sources) {
          setNumSources(gatherResponse.data.data.num_sources);
        }
        
        // Then call get_topic_overview
        const overviewResponse = await axios.post(`${API_URL}/api/get_topic_overview`, {
          query: currentQuery
        });

        if (overviewResponse.data.status === "success") {
          setTopicOverview(overviewResponse.data.data.overview);
          
          // Now create the knowledge graph with the same query
          await createKnowledgeGraphWithQuery(currentQuery);
        } else {
          throw new Error(overviewResponse.data.message || "Failed to get topic overview");
        }
      } else {
        throw new Error(gatherResponse.data.message || "Failed to gather news sources");
      }
    } catch (error) {
      console.error("Error processing query:", error);
      setError(
        error.response?.data?.message || 
        error.message || 
        "Failed to process your query. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleFollowUpSubmit = async () => {
    if (!followUpInput.trim()) return;
    
    // Reset follow-up response states
    setFollowUpResponse(null);
    setShowFollowUpResponse(false);
    
    try {
      const API_URL = "http://127.0.0.1:5000";
      
      // Call the query_knowledge_graph endpoint with the follow-up question
      const response = await axios.post(`${API_URL}/api/query_knowledge_graph`, {
        query: followUpInput,
        num_sources: 5
      });
      
      if (response.data.status === "success") {
        // Store and display the follow-up response
        setFollowUpResponse(response.data.data.result);
        setShowFollowUpResponse(true);
      } else {
        throw new Error(response.data.message || "Failed to process follow-up question");
      }
    } catch (error) {
      console.error("Error processing follow-up question:", error);
      setError(
        error.response?.data?.message || 
        error.message || 
        "Failed to process your follow-up question. Please try again."
      );
    } finally {
      // Clear the follow-up input after submission
      setFollowUpInput("");
    }
  };

  // Process the overview text to ensure links are clickable
  const processedOverview = topicOverview ? processTextWithLinks(topicOverview) : null;
  
  // Choose the graph component based on view mode
  const Graph = view3D ? ForceGraph3D : ForceGraph2D;
  
  // Build highlight sets for graph interaction
  const highlightNodes = new Set();
  const highlightLinks = new Set();
  
  if (hoverNode) {
    highlightNodes.add(hoverNode);
    graphData.links.forEach((l) => {
      if (l.source === hoverNode || l.target === hoverNode) {
        highlightLinks.add(l);
        highlightNodes.add(l.source);
        highlightNodes.add(l.target);
      }
    });
  }
  
  if (hoverLink) {
    highlightLinks.add(hoverLink);
    highlightNodes.add(hoverLink.source);
    highlightNodes.add(hoverLink.target);
  }

  return (
    <div className="flex flex-col items-center justify-between h-screen bg-white text-center px-6 py-10">
      {/* Logo (Top) */}
      <div className="flex items-center justify-center mb-8">
        <img src={Logo} alt="News Broom Logo" className="h-20" />
      </div>

      {/* Content Area (Middle) */}
      <div className="flex-1 w-full overflow-auto max-w-5xl mx-auto">
        {showSections ? (
          // Original Three Sections
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 w-full">
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
        ) : (
          // Results or Loading State
          <div className="w-full px-4">
            {/* "You asked" section */}
            <div className="flex items-center gap-3 mb-6 text-left">
              <FaUserCircle className="text-3xl text-gray-600" />
              <div>
                <p className="text-sm text-gray-500">You asked:</p>
                <p className="text-lg font-semibold">{submittedQuery}</p>
              </div>
            </div>
            
            {/* Topic Overview */}
            {topicOverview && (
              <div className="text-left bg-white border border-gray-200 rounded-lg p-5 shadow-md mb-8">
                <div className="flex justify-between items-center mb-2 cursor-pointer" onClick={toggleOverview}>
                  <h2 className="text-lg font-bold">Topic Overview</h2>
                  <button className="text-gray-500 hover:text-gray-700">
                    {isOverviewExpanded ? <FaChevronUp /> : <FaChevronDown />}
                  </button>
                </div>
                
                <div className={`prose prose-sm max-w-none text-sm overflow-hidden transition-all duration-300 ${isOverviewExpanded ? 'max-h-[5000px]' : 'max-h-28'}`}>
                  <ReactMarkdown 
                    rehypePlugins={[rehypeRaw, rehypeSanitize]}
                    components={{
                      a: ({node, ...props}) => (
                        <a target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" {...props} />
                      )
                    }}
                  >
                    {processedOverview}
                  </ReactMarkdown>
                </div>
                
                {!isOverviewExpanded && (
                  <div className="mt-2 text-center">
                    <button 
                      onClick={toggleOverview}
                      className="text-blue-500 text-sm hover:text-blue-700 hover:underline focus:outline-none"
                    >
                      Show more
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Sources Loading/Complete Indicator */}
            <div className="mb-8">
              {isLoading ? (
                <div className="flex items-center text-left">
                  <FaSpinner className="text-blue-600 text-xl animate-spin mr-3" />
                  <span className="text-lg">Gathering News Sources... (estimated 2 min)</span>
                </div>
              ) : gatheringComplete && (
                <div className="text-left text-green-700 p-3 bg-green-50 rounded-lg">
                  I retrieved {numSources} sources related to the topic "{submittedQuery}"
                </div>
              )}
            </div>

            {/* Knowledge Graph Section */}
            <div className="mb-8">
              {creatingGraph ? (
                <div className="flex items-center text-left mb-4">
                  <FaSpinner className="text-blue-600 text-xl animate-spin mr-3" />
                  <span className="text-lg">Creating Knowledge Graph...</span>
                </div>
              ) : graphReady && (
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold">Knowledge Graph</h2>
                    <button
                      onClick={() => setView3D(prev => !prev)}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                    >
                      Toggle {view3D ? "2D" : "3D"} View
                    </button>
                  </div>
                  
                  <div 
                    ref={containerRef} 
                    className="border border-gray-200 rounded-lg overflow-hidden" 
                    style={{ height: '400px' }}
                  >
                    {graphData.nodes.length > 0 && (
                      <Graph
                        ref={graphRef}
                        graphData={graphData}
                        width={size.w}
                        height={size.h}
                        nodeAutoColorBy="group"
                        nodeOpacity={0.85}
                        nodeLabel={(n) => n.label || n.id}
                        linkLabel={(l) => {
                          const src = typeof l.source === "object" ? l.source.id : l.source;
                          const tgt = typeof l.target === "object" ? l.target.id : l.target;
                          const w = l.properties?.weight ?? l.properties?.Weight ?? "n/a";
                          return `${src} → ${tgt}\nweight: ${w}`;
                        }}
                        nodeVal={(n) => (highlightNodes.has(n) ? 12 : 6)}
                        linkWidth={(l) => (highlightLinks.has(l) ? 3 : 1)}
                        linkDirectionalParticles={(l) => (highlightLinks.has(l) ? 4 : 0)}
                        linkDirectionalParticleWidth={2}
                        onNodeHover={(n) => {
                          setHoverNode(n || null);
                          setHoverLink(null);
                        }}
                        onLinkHover={(l) => {
                          setHoverLink(l || null);
                          setHoverNode(null);
                        }}
                        linkDirectionalArrowLength={3.5}
                        linkDirectionalArrowRelPos={1}
                        linkCurvature={0.25}
                        cooldownTime={2000}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>

            {followUpResponse && showFollowUpResponse && (
              <div className="mb-8 text-left bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h3 className="text-lg font-semibold mb-2">Follow-up Response:</h3>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown rehypePlugins={[rehypeRaw, rehypeSanitize]}>
                    {followUpResponse}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {error && (
              <div className="p-4 mb-6 bg-red-50 text-red-600 rounded-lg">
                <p className="font-semibold">Error:</p>
                <p>{error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Input Bar with Back to Homepage Button */}
      <div className="mt-8 flex flex-col items-center justify-center w-full max-w-3xl">
        {!showSections && (
          <div className="w-full flex justify-center mb-4">
            <button 
              onClick={handleBackToHome}
              className="flex items-center text-blue-600 hover:text-blue-800 font-medium"
            >
              <FaArrowLeft className="mr-2" /> Back to homepage
            </button>
          </div>
        )}
        <div className="w-full flex items-center border border-gray-300 rounded-lg p-3 shadow-sm">
          <FaMicrophone className="text-gray-500 text-xl mr-3 cursor-pointer" />
          {showSections ? (
            <>
              <input 
                type="text" 
                placeholder="Ask anything about current events or future scenarios..." 
                className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
                value={userInput}
                onChange={handleInputChange}
                onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSubmit()}
                disabled={isLoading}
              />
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className={`transition-opacity ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'}`}
              >
                <FaPaperPlane className="text-gray-500 text-xl ml-3" />
              </button>
            </>
          ) : (
            <>
              <input 
                type="text" 
                placeholder="Ask a follow-up question about the knowledge graph..." 
                className="flex-1 outline-none bg-transparent text-gray-700 text-sm"
                value={followUpInput}
                onChange={handleFollowUpInputChange}
                onKeyPress={(e) => e.key === 'Enter' && handleFollowUpSubmit()}
                disabled={isLoading || creatingGraph}
              />
              <button
                onClick={handleFollowUpSubmit}
                disabled={isLoading || creatingGraph}
                className={`transition-opacity ${(isLoading || creatingGraph) ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'}`}
              >
                <FaPaperPlane className="text-gray-500 text-xl ml-3" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;