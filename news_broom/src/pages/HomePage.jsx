import { useState, useEffect, useRef } from "react";
import { FaCommentDots, FaProjectDiagram, FaExclamationTriangle, FaMicrophone, FaPaperPlane, FaSpinner, FaChevronDown, FaChevronUp, FaArrowLeft, FaUserCircle } from "react-icons/fa";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import ForceGraph2D from "react-force-graph-2d";
import ForceGraph3D from "react-force-graph-3d";
import Logo from "../assets/images/Logo.png";
import * as d3 from 'd3';

// Update the getNodeColor function at the top of the file
const getNodeColor = (group, colorScale) => {
  // Custom color mapping to match what's displayed in the actual graph
  const groupColorMap = {
    "EVENT": "#68a0cf",      // lighter blue
    "ORGANIZATION": "#1f77b4", // darker blue
    "PERSON": "#8bcc84",     // lighter green
    "GEO": "#2ca02c"         // darker green
  };
  
  // Use the direct mapping if available, otherwise fall back to the color scale
  return groupColorMap[group] || (colorScale ? colorScale(group) : "#cccccc");
};

const HomePage = () => {
  // Add this debugging log
  //console.log("API URL:", import.meta.env.VITE_API_URL || "Not found, using fallback");

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
  const [view3D, setView3D] = useState(true);
  const [graphWarning, setGraphWarning] = useState(null);
  const [followUpResponse, setFollowUpResponse] = useState(null);
  const [showFollowUpResponse, setShowFollowUpResponse] = useState(false);
  const [followUpLoading, setFollowUpLoading] = useState(false);
  const [submittedFollowUp, setSubmittedFollowUp] = useState(""); // Store the follow-up question
  const [expandedScenarios, setExpandedScenarios] = useState([false, false, false]);
  const [enhancedCitations, setEnhancedCitations] = useState(null);

  // Graph refs and state
  const graphRef = useRef();
  const containerRef = useRef();
  const [size, setSize] = useState({ w: 800, h: 400 });
  const [hoverNode, setHoverNode] = useState(null);
  const [hoverLink, setHoverLink] = useState(null);

  // Add new state for keeping track of node groups and their colors
  const [nodeGroups, setNodeGroups] = useState([]);
  const colorScale = useRef(d3.scaleOrdinal(d3.schemeCategory10));

  // Add these new state variables for selection (instead of just hover)
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedLink, setSelectedLink] = useState(null);

  // Add new state variables for highlighted nodes and links
  const [highlightedNodes, setHighlightedNodes] = useState(new Set());
  const [highlightedLinks, setHighlightedLinks] = useState(new Set());

  // Set container size on mount and window resize
  useEffect(() => {
    function handleResize() {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        setSize({
          w: containerWidth, 
          h: 600 // Match the container height
        });
      }
    }
    
    handleResize();
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
  }, [graphData, highlightedNodes]);

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

  // Add this useEffect to extract node groups when graph data changes
  useEffect(() => {
    if (graphData && graphData.nodes && graphData.nodes.length > 0) {
      // Extract unique groups from nodes
      const groups = [...new Set(graphData.nodes.map(node => node.group))].filter(Boolean);
      setNodeGroups(groups);
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

  // Update the API_URL constant to include a fallback
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5001";

  // Add this debugging log to help verify the URL being used
  //console.log("Current API URL:", API_URL);
  //console.log("Current environment:", import.meta.env.MODE);

  // Then update createKnowledgeGraphWithQuery function
  const createKnowledgeGraphWithQuery = async (query) => {
    try {
      setCreatingGraph(true);
      console.log("Creating knowledge graph for query:", query);
      
      // Single API call to create_knowledge_graph, which now also returns the graph data
      const graphResponse = await axios.post(`${API_URL}/api/create_knowledge_graph`, {
        query: query
      });
      
      // The response now directly contains the graph data (nodes and links)
      if (graphResponse.data && (graphResponse.data.nodes || graphResponse.data.links)) {
        setGraphData(graphResponse.data);
        setGraphReady(true);
        // return graphResponse.data
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
    
    // Reset states
    setFollowUpResponse(null);
    setShowFollowUpResponse(false);
    setSubmittedFollowUp(followUpInput);
    setFollowUpLoading(true);
    setHighlightedNodes(new Set());
    setHighlightedLinks(new Set());
    setExpandedScenarios([false, false, false]);
    setEnhancedCitations(null); // Reset enhanced citations
    
    try {
      const response = await axios.post(`${API_URL}/api/query_global_knowledge_graph`, {
        query: followUpInput,
        topic: submittedQuery,
      });
      
      if (response.data.status === "success") {
        // Process the response to remove unwanted prefixes
        let cleanedResponse = response.data.data.result;
        
        // Remove the technical headers with a more comprehensive regex
        cleanedResponse = cleanedResponse.replace(/INFO:[\s\S]*?REDACTED ====\}\s*\n/g, '');
        cleanedResponse = cleanedResponse.replace(/SUCCESS:\s*(?:Global|Local)\s*Search\s*Response:?\s*/g, '');
        cleanedResponse = cleanedResponse.replace(/Follow-up\s*Response:?\s*/g, '');
        
        // Trim leading and trailing whitespace
        cleanedResponse = cleanedResponse.trim();
        
        // Store and display the processed follow-up response
        setFollowUpResponse(cleanedResponse);
        setShowFollowUpResponse(true);
        
        // Process highlighted graph data if available
        if (response.data.data.citations) {
          const highlightNodes = response.data.data.citations.highlightNodes;
          const highlightEdges = response.data.data.citations.highlightEdges;
          // const graphData = response.data.data.graph;
          // Create sets of node and link IDs to highlight
          const nodeSet = new Set();
          const linkSet = new Set();
          highlightNodes.forEach(node => nodeSet.add(node));
          highlightEdges.forEach(link => {
            // Create a unique ID for each link (source-target)
            const linkId = typeof link.source === 'object' 
              ? `${link.source.id}-${link.target.id}` 
              : `${link.source}-${link.target}`;
            linkSet.add(linkId);
          });
          
          // Update state with highlighted elements
          setHighlightedNodes(nodeSet);
          setHighlightedLinks(linkSet);
        }

        // Store enhanced citations in state
        if (response.data.data.enhanced_citations) {
          setEnhancedCitations(response.data.data.enhanced_citations);
          
          // Log for debugging (you can keep or remove this)
          console.log("Enhanced citations:", response.data.data.enhanced_citations);
        }
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
      setFollowUpInput("");
      setFollowUpLoading(false);
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
    // Find all direct neighbors of the hovered node
    graphData.links.forEach((l) => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      const hoveredId = typeof hoverNode === 'object' ? hoverNode.id : hoverNode;
      
      if (sourceId === hoveredId || targetId === hoveredId) {
        highlightLinks.add(l);
        // Add both source and target to highlight nodes
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

  // Update the GraphLegend component
  const GraphLegend = () => {
    if (nodeGroups.length === 0) return null;
    
    return (
      <div className="absolute right-4 top-4 bg-white bg-opacity-90 p-4 rounded-lg shadow-md border border-gray-200 max-w-xs z-10 overflow-auto" style={{ maxHeight: '90%' }}>
        <h3 className="text-sm font-bold mb-3 text-left">Legend</h3>
        <div className="flex flex-col gap-2">
          {nodeGroups.map((group) => (
            <div key={group} className="flex items-center gap-2 text-left">
              <div 
                className="w-4 h-4 rounded-full" 
                style={{ backgroundColor: getNodeColor(group, colorScale.current) }}
              ></div>
              <span className="text-xs">{group}</span>
            </div>
          ))}
          {highlightedNodes.size > 0 && (
            <div key="Search Result" className="flex items-center gap-2 text-left">
              <div 
                className="w-4 h-4 rounded-full" 
                style={{ backgroundColor: '#ff5500'}}
              ></div>
              <span className="text-xs">CITED NODES</span>
            </div>
          )}
        </div>
        
        {selectedNode ? (
          <div className="mt-4 pt-3 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-bold text-left mb-2">Node Details</h4>
              <button 
                onClick={() => setSelectedNode(null)} 
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="text-left">
              <div className="mb-1">
                <span className="font-semibold text-gray-700 mr-1">ID:</span>
                <span className="text-gray-600">{selectedNode.id}</span>
              </div>
              {selectedNode.label && (
                <div className="mb-1">
                  <span className="font-semibold text-gray-700 mr-1">Label:</span>
                  <span className="text-gray-600">{selectedNode.label}</span>
                </div>
              )}
              {selectedNode.group && (
                <div className="mb-1">
                  <span className="font-semibold text-gray-700 mr-1">Group:</span>
                  <span className="text-gray-600">{selectedNode.group}</span>
                </div>
              )}
              {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, value]) => {
                if (key.startsWith('_') || typeof value === 'object') return null;
                return (
                  <div key={key} className="mb-1">
                    <span className="font-semibold text-gray-700 mr-1">{key}:</span>
                    <span className="text-gray-600">{value.toString()}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : selectedLink ? (
          <div className="mt-4 pt-3 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-bold text-left mb-2">Link Details</h4>
              <button 
                onClick={() => setSelectedLink(null)} 
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="text-left">
              <div className="mb-1">
                <span className="font-semibold text-gray-700 mr-1">Source:</span>
                <span className="text-gray-600">
                  {typeof selectedLink.source === 'object' ? selectedLink.source.id : selectedLink.source}
                </span>
              </div>
              <div className="mb-1">
                <span className="font-semibold text-gray-700 mr-1">Target:</span>
                <span className="text-gray-600">
                  {typeof selectedLink.target === 'object' ? selectedLink.target.id : selectedLink.target}
                </span>
              </div>
              {selectedLink.value && (
                <div className="mb-1">
                  <span className="font-semibold text-gray-700 mr-1">Value:</span>
                  <span className="text-gray-600">{selectedLink.value}</span>
                </div>
              )}
              {selectedLink.properties && Object.entries(selectedLink.properties).map(([key, value]) => {
                if (key.startsWith('_') || typeof value === 'object') return null;
                return (
                  <div key={key} className="mb-1">
                    <span className="font-semibold text-gray-700 mr-1">{key}:</span>
                    <span className="text-gray-600">{value.toString()}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="mt-4 pt-3 border-t border-gray-200 text-gray-500 text-xs italic text-left">
            Click on a node or link to see details
          </div>
        )}
      </div>
    );
  };

  // Updated CitationDetails component report section
  const CitationDetails = ({ enhancedCitations }) => {
    // Add state for toggling details visibility
    const [expandedReports, setExpandedReports] = useState({});
    
    if (!enhancedCitations) return null;
    
    const { reports, highlightedNodes, highlightedEdges } = enhancedCitations;
    
    // Check if we have data to display
    if (
      (!reports || reports.length === 0) &&
      (!highlightedNodes || highlightedNodes.length === 0) &&
      (!highlightedEdges || highlightedEdges.length === 0)
    ) {
      return null;
    }
    
    // Toggle report detail expansion
    const toggleReportDetails = (reportId) => {
      setExpandedReports(prev => ({
        ...prev,
        [reportId]: !prev[reportId]
      }));
    };
    
    return (
      <div className="mt-6 text-left">
        <h3 className="text-lg font-semibold mb-2">Citation Details</h3>
        
        {/* Display highlighted entities */}
        {highlightedNodes && highlightedNodes.length > 0 && (
          <div className="mb-4">
            <h4 className="font-medium text-gray-800 mb-1">Key Entities</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {highlightedNodes.map((node, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <div className="font-medium">{node.label}</div>
                  {node.details && (
                    <div className="text-sm text-gray-600 mt-1">
                      <div><span className="font-medium">Type:</span> {node.details.group || 'Entity'}</div>
                      {node.details.properties && Object.entries(node.details.properties)
                        .filter(([key, val]) => !key.startsWith('_') && val && typeof val !== 'object')
                        .map(([key, val]) => (
                          <div key={key}><span className="font-medium">{key}:</span> {val.toString()}</div>
                        ))
                      }
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Display highlighted relationships */}
        {highlightedEdges && highlightedEdges.length > 0 && (
          <div className="mb-4">
            <h4 className="font-medium text-gray-800 mb-1">Key Relationships</h4>
            <div className="space-y-2">
              {highlightedEdges.map((edge, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <div className="font-medium">{edge.source} → {edge.target}</div>
                  {edge.details && (
                    <div className="text-sm text-gray-600 mt-1">
                      <div><span className="font-medium">Type:</span> {edge.details.label || 'related to'}</div>
                      {edge.details.properties && Object.entries(edge.details.properties)
                        .filter(([key, val]) => !key.startsWith('_') && val && typeof val !== 'object')
                        .map(([key, val]) => (
                          <div key={key}><span className="font-medium">{key}:</span> {val.toString()}</div>
                        ))
                      }
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Display reports with improved formatting */}
        {reports && reports.length > 0 && (
          <div className="mb-4">
            <h4 className="font-medium text-gray-800 mb-1">Reports</h4>
            <div className="space-y-3">
              {reports.map((report, index) => {
                const isExpanded = expandedReports[report.id] || false;
                
                // Extract findings from properties if available
                const findings = report.properties?.findings || [];
                
                return (
                  <div key={index} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                    <div className="font-medium">Report {report.id}</div>
                    
                    {/* Report Content Section */}
                    <div className="text-sm text-gray-600">
                      {report.title && (
                        <div className="mt-1">
                          <span className="font-medium">Title:</span> {report.title}
                        </div>
                      )}
                      
                      {/* Show count of highlighted nodes in the graph */}
                      <div className="mt-1">
                        <span className="font-medium">Highlighted in Graph:</span> {highlightedNodes?.length || 0} entities
                      </div>
                      
                      {/* Report Content */}
                      {report.text && (
                        <div className="mt-2 border-t border-gray-200 pt-2">
                          <div className="font-medium mb-1">Report Content:</div>
                          <div className="bg-white p-2 rounded border border-gray-300 max-h-60 overflow-y-auto">
                            {/* Display summary text or beginning of content */}
                            {report.summary || (report.text.length > 300 ? report.text.substring(0, 300) + '...' : report.text)}
                          </div>
                        </div>
                      )}
                      
                      {/* Key Findings Section - Always show this since user likes it */}
                      {findings.length > 0 && (
                        <div className="mt-2 border-t border-gray-200 pt-2">
                          <div className="font-medium mb-1">Key Findings:</div>
                          <div className="space-y-2">
                            {findings.map((finding, idx) => (
                              <div key={idx} className="bg-white p-2 rounded border border-gray-300">
                                <div className="font-medium">{finding.summary}</div>
                                <div className="text-sm mt-1">{finding.explanation}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Consolidated Metadata Section - replaces both Additional Properties and Report Metadata */}
                      {(report.details || report.properties) && (
                        <div className="mt-2 border-t border-gray-200 pt-2">
                          <div className="font-medium mb-1 flex justify-between items-center">
                            <span>Report Metadata:</span>
                            <button 
                              onClick={() => toggleReportDetails(report.id)}
                              className="text-xs text-blue-500 hover:underline"
                            >
                              {isExpanded ? 'Show Less' : 'Show More Details'}
                            </button>
                          </div>
                          
                          {/* Always show a few key metadata fields */}
                          <div className="space-y-1">
                            {/* Priority fields to always show */}
                            {report.details?.period && (
                              <div><span className="font-medium">Period:</span> {report.details.period}</div>
                            )}
                            {report.details?.rank && (
                              <div><span className="font-medium">Impact Rank:</span> {report.details.rank}</div>
                            )}
                            {report.details?.rating_explanation && (
                              <div>
                                <span className="font-medium">Rating Explanation:</span> {
                                  report.details.rating_explanation.length > 100 && !isExpanded 
                                    ? report.details.rating_explanation.substring(0, 100) + '...' 
                                    : report.details.rating_explanation
                                }
                              </div>
                            )}
                          </div>
                          
                          {/* Show additional metadata when expanded */}
                          {isExpanded && (
                            <div className="mt-2 space-y-1">
                              {/* Combine metadata from both report.details and report.properties */}
                              {Object.entries({
                                // Merge properties from both sources, prioritizing details
                                ...Object.entries(report.properties || {})
                                  .filter(([key, val]) => (
                                    !['full_content', 'full_content_json', 'findings', 'entity_ids',
                                      'summary', 'title', 'text', 'rating_explanation', 'period', 'rank'].includes(key) &&
                                    !key.startsWith('_') && 
                                    val && 
                                    typeof val !== 'object'
                                  ))
                                  .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {}),
                                
                                ...Object.entries(report.details || {})
                                  .filter(([key, val]) => (
                                    !['properties', 'full_content', 'full_content_json', 'findings',
                                      'summary', 'title', 'text', 'nodes', 'rating_explanation', 'period', 'rank'].includes(key) &&
                                    !key.startsWith('_') && 
                                    val && 
                                    typeof val !== 'object'
                                  ))
                                  .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {})
                              }).map(([key, val]) => (
                                <div key={key}>
                                  <span className="font-medium">{key}:</span> {
                                    typeof val === 'string' && val.length > 100
                                      ? val.substring(0, 100) + '...' 
                                      : val.toString()
                                  }
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col items-center justify-between h-screen bg-white text-center px-6 py-10">
      {/* Logo (Top) */}
      <div className="flex items-center justify-center mb-8">
        <img src={Logo} alt="News Broom Logo" className="h-20" />
      </div>

      {/* Content Area (Middle) */}
      <div className="flex-1 w-full max-w-5xl mx-auto">
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
                
                <div className={`prose prose-sm max-w-none text-sm ${!isOverviewExpanded && 'line-clamp-3'}`}>
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
            <div className="mb-8 w-full">
              {creatingGraph ? (
                <div className="flex items-center text-left mb-4">
                  <FaSpinner className="text-blue-600 text-xl animate-spin mr-3" />
                  <span className="text-lg">Creating Knowledge Graph...</span>
                </div>
              ) : graphReady && (
                <div className="mb-4 w-full">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold">Knowledge Graph</h2>
                  </div>
                  
                  <div 
                    ref={containerRef} 
                    className="border border-gray-200 rounded-lg overflow-hidden relative w-full" 
                    style={{ height: '600px' }}
                  >
                    {graphData.nodes.length > 0 && (
                      <>
                        {/* Add the node/edge count overlay */}
                        <div className="absolute left-4 top-4 bg-white bg-opacity-90 p-2 rounded-lg shadow-md border border-gray-200 z-10">
                          <div className="text-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">Nodes:</span>
                              <span>{graphData.nodes.length}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">Edges:</span>
                              <span>{graphData.links.length}</span>
                            </div>
                          </div>
                        </div>
                        
                        <Graph
                          ref={graphRef}
                          graphData={graphData}
                          width={size.w}
                          height={size.h}
                          backgroundColor="#000"
                          nodeAutoColorBy="group"
                          nodeOpacity={0.85}
                          
                          // Keep labels but simplify them
                          nodeLabel={(n) => n.label || n.id || ''}
                          linkLabel={(l) => l.type || ''}
                          
                          // Fix the d3Force syntax error - changed comma to array notation
                          d3Force={['charge', d3.forceManyBody().strength(-50).distanceMax(200)]}
                          
                          // Add performance optimizations
                          d3AlphaDecay={0.02} // Faster stabilization
                          d3VelocityDecay={0.3} // Less node movement
                          cooldownTime={1000} // Reduced from 2000
                          warmupTicks={50} // Initial ticks in background
                          
                          onNodeHover={(n) => {
                            setHoverNode(n || null);
                            setHoverLink(null);
                          }}
                          onLinkHover={(l) => {
                            setHoverLink(l || null);
                            setHoverNode(null);
                          }}
                          onNodeClick={(n) => {
                            setSelectedNode(n);
                            setSelectedLink(null);
                          }}
                          onLinkClick={(l) => {
                            setSelectedLink(l);
                            setSelectedNode(null);
                          }}
                          onBackgroundClick={() => {
                            setSelectedNode(null);
                            setSelectedLink(null);
                          }}
                          nodeVal={(n) => {
                            const nodeId = typeof n === 'object' ? n.id : n;
                            
                            // Check if node is highlighted from backend
                            if (n.highlighted || highlightedNodes.has(nodeId)) {
                              return 18; // Largest size for highlighted nodes from search
                            }
                            
                            // Node being hovered on directly
                            if (n === hoverNode) {
                              return 20; // Biggest size for the exact hovered node
                            }
                            
                            // Interactive nodes (neighbors of hovered or selected)
                            if (highlightNodes.has(n) || n === selectedNode) {
                              return 15; // Larger size for neighbors
                            }
                            
                            // Default size
                            return 6;
                          }}
                          nodeColor={(n) => {
                            const nodeId = typeof n === 'object' ? n.id : n;
                            
                            // Check if node is highlighted from backend search results
                            if (n.highlighted || highlightedNodes.has(nodeId)) {
                              return '#ff5500'; // Keep orange for highlighted nodes from search results
                            }
                            
                            // Selected node
                            if (n === selectedNode) {
                              return '#ff00ff'; // Keep purple for selected node
                            }
                            
                            // For all other nodes (including hovered nodes and their neighbors)
                            // Always use the original group color
                            return getNodeColor(n.group, colorScale.current);
                          }}
                          linkWidth={(l) => {
                            // Create a unique ID for the link
                            const linkId = typeof l.source === 'object' 
                              ? `${l.source.id}-${l.target.id}` 
                              : `${l.source}-${l.target}`;

                            // Check if link is highlighted from backend
                            if (l.highlighted || highlightedLinks.has(linkId)) {
                              return 5; // Thickest for highlighted links
                            }
                            // Interactive links (hovered or selected)
                            if (highlightLinks.has(l) || l === selectedLink) {
                              return 3; // Medium width
                            }
                            // Default width
                            return 1;
                          }}
                          linkColor={(l) => {
                            // Create a unique ID for the link
                            const linkId = typeof l.source === 'object' 
                              ? `${l.source.id}-${l.target.id}` 
                              : `${l.source}-${l.target}`;
                            
                            // Check if link is highlighted from backend
                            if (l.highlighted || highlightedLinks.has(linkId)) {
                              return '#ff5500'; // Orange for highlighted links
                            }
                            // Default color
                            return '#ffffff';
                          }}
                          linkDirectionalParticles={(l) => {
                            // Create a unique ID for the link
                            const linkId = typeof l.source === 'object' 
                              ? `${l.source.id}-${l.target.id}` 
                              : `${l.source}-${l.target}`;
                            
                            // Show particles for:
                            // 1. Links highlighted from search results
                            // 2. Links connected to hovered nodes
                            // 3. The currently hovered link
                            // 4. The selected link
                            return (l.highlighted || 
                                    highlightedLinks.has(linkId) || 
                                    highlightLinks.has(l) || 
                                    l === hoverLink || 
                                    l === selectedLink) ? 4 : 0;
                          }}
                          linkDirectionalParticleWidth={2}
                          linkDirectionalArrowLength={3.5}
                          linkDirectionalArrowRelPos={1}
                          linkCurvature={0.25}
                        />
                        <GraphLegend />
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {followUpLoading && (
              <div className="flex items-center text-left mb-4">
                <FaSpinner className="text-blue-600 text-xl animate-spin mr-3" />
                <span className="text-lg">Querying Knowledge Graph...</span>
              </div>
            )}

            {submittedFollowUp && followUpResponse && showFollowUpResponse && !followUpLoading && (
              <div className="mb-8 text-left">
                <div className="flex items-center gap-3 mb-4">
                  <FaUserCircle className="text-3xl text-gray-600" />
                  <div>
                    <p className="text-sm text-gray-500">You asked:</p>
                    <p className="text-lg font-semibold">{submittedFollowUp}</p>
                  </div>
                </div>
                
                {/* Simple single-column display for the response */}
                <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown 
                      rehypePlugins={[rehypeRaw, rehypeSanitize]}
                      components={{
                        a: ({node, ...props}) => (
                          <a target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" {...props} />
                        )
                      }}
                    >
                      {followUpResponse}
                    </ReactMarkdown>
                  </div>
                  
                  {/* Add the citation details component - using state variable now */}
                  {enhancedCitations && (
                    <CitationDetails enhancedCitations={enhancedCitations} />
                  )}
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