// src/pages/KnowledgeGraphPage.jsx
import { useEffect, useRef, useState } from "react";
import { FaArrowLeft } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import ForceGraph3D from "react-force-graph-3d";
import ForceGraph2D from "react-force-graph-2d";
import smallGraphData from "../../small_graph.json";  // Import small graph data
import bigGraphData from "../../big_graph.json";      // Import big graph data

export default function KnowledgeGraphPage() {
  const navigate = useNavigate();
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [view3D, setView3D] = useState(true);
  const [expandedGraph, setExpandedGraph] = useState(false);
  const graphRef = useRef();
  const [hoverNode, setHoverNode] = useState(null);
  const [hoverLink, setHoverLink] = useState(null);

  /* ---------- keep the canvas inside its box ---------- */
  const containerRef = useRef();
    const [size, setSize] = useState({ w: 1000, h: 1000 });

    useEffect(() => {
      function handleResize() {
        if (containerRef.current) {
          setSize({
            w: Math.floor(window.innerWidth * 0.8),
            h: Math.floor(window.innerHeight * 0.75)
          });
    }
  }
  handleResize();                // first run
    window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
  }, []);

  // ---------- load the graph data when expanded state changes ----------
  useEffect(() => {
    try {
      setLoading(true);
      // Use expanded graph data if toggle is on, otherwise use small graph
      const data = expandedGraph ? bigGraphData : smallGraphData;
      setGraph(data);
    } catch (err) {
      console.error("Could not load graph data:", err);
    } finally {
      setLoading(false);
    }
  }, [expandedGraph]);

  // ---------- once layout stabilises, zoom to fit ----------
  useEffect(() => {
    if (graphRef.current && graph.nodes.length) {
      graphRef.current.zoomToFit(400);
    }
  }, [graph]);

  const Graph = view3D ? ForceGraph3D : ForceGraph2D;

  
  /* ---------- build highlight sets each render ---------- */
  const highlightNodes = new Set();
  const highlightLinks = new Set();
  if (hoverNode) {
    highlightNodes.add(hoverNode);
    graph.links.forEach((l) => {
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
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="p-6 pb-2">
        <h1 className="text-2xl font-semibold mb-2">
          TikTok Ban by the US Government
        </h1>
        <p className="text-gray-600 mb-4">Knowledge Graph Visualization</p>
      </div>

      {/* Graph */}
      <div ref={containerRef} className="flex-1 px-6 pb-6 relative overflow-hidden">
        {loading ? (
          <p className="text-blue-500">Loading graph…</p>
        ) : (
          <>
            <div className="flex items-center gap-4 mb-2">
              <button
                onClick={() => setView3D((v) => !v)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Toggle {view3D ? "2-D" : "3-D"}
              </button>
              
              {/* New toggle for graph size */}
              <div className="flex items-center">
                <span className="mr-2 text-sm">Small</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={expandedGraph}
                    onChange={() => setExpandedGraph(prev => !prev)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
                <span className="ml-2 text-sm">Expanded</span>
              </div>
              
              <p className="text-sm">
                Nodes {graph.nodes.length} • Links {graph.links.length}
              </p>
            </div>

            <Graph
              ref={graphRef}
              graphData={graph}
              width={size.w}
              height={size.h}
              nodeAutoColorBy="group"
              nodeOpacity={0.85}
              /* simplified tool‑tips */
              nodeLabel={(n) => n.label || n.id}
              linkLabel={(l) => {
                const src = typeof l.source === "object" ? l.source.id : l.source;
                const tgt = typeof l.target === "object" ? l.target.id : l.target;
                const w = l.properties?.weight ?? l.properties?.Weight ?? "n/a";
                return `${src} → ${tgt}\nweight: ${w}`;
              }}
               /* --- highlight styling --- */
              nodeVal={(n) => (highlightNodes.has(n) ? 12 : 6)}
              linkWidth={(l) => (highlightLinks.has(l) ? 3 : 1)}
              linkDirectionalParticles={(l) => (highlightLinks.has(l) ? 4 : 0)}
              linkDirectionalParticleWidth={2}

              /* --- hover handlers --- */
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
          </>
        )}
      </div>

      {/* Back button */}
      <div className="px-6 pb-6">
        <button
          onClick={() => navigate(-1)}
          className="px-6 py-3 bg-gray-100 border rounded-lg flex items-center gap-2 hover:bg-gray-200 transition"
        >
          <FaArrowLeft className="text-gray-600" />
          Go back to the Editorial
        </button>
      </div>
    </div>
  );
}