import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface Scenario {
  id: string;
  title: string;
  probability: number;
  impact: number;
  description: string;
}

interface ScenarioVisualizationProps {
  scenarios: Scenario[];
  question: string;
}

const ScenarioVisualization: React.FC<ScenarioVisualizationProps> = ({ scenarios, question }) => {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!scenarios.length || !svgRef.current) return;

    const margin = { top: 80, right: 20, bottom: 50, left: 60 };
    const width = 800 - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([height, 0]);

    // Add axes
    svg.append("g")
      .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(xScale).ticks(5).tickFormat((d: d3.NumberValue) => `${+d * 100}%`));

    svg.append("g")
      .call(d3.axisLeft(yScale).ticks(5));

    // Add labels
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height + 40)
      .attr("text-anchor", "middle")
      .text("Probability");

    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -50)
      .attr("x", -(height / 2))
      .attr("text-anchor", "middle")
      .text("Impact");

    // Add title
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", -40)
      .attr("text-anchor", "middle")
      .attr("class", "title-text")
      .text("What if...");

    // Add question box
    const questionWidth = 350;
    const questionHeight = 30;

    svg.append("rect")
      .attr("x", (width - questionWidth) / 2)
      .attr("y", -30)
      .attr("width", questionWidth)
      .attr("height", questionHeight)
      .attr("class", "question-box");

    svg.append("text")
      .attr("x", width / 2)
      .attr("y", -10)
      .attr("text-anchor", "middle")
      .attr("class", "question-text")
      .text(question);

    // Add nodes
    const node = svg.selectAll("circle")
      .data(scenarios)
      .enter()
      .append("circle")
      .attr("r", 20)
      .attr("cx", d => xScale(d.probability))
      .attr("cy", d => yScale(d.impact))
      .attr("fill", d => d.impact > 0 ? "#4D5664" : "#A4292B")
      .on("click", (event, d) => showScenarioDetails(d));

    // Add labels
    svg.selectAll(".text")
      .data(scenarios)
      .enter()
      .append("text")
      .attr("x", d => xScale(d.probability) + 25)
      .attr("y", d => yScale(d.impact) + 5)
      .text(d => d.title)
      .attr("font-size", "12px")
      .attr("fill", "#414141");

  }, [scenarios, question]);

  const showScenarioDetails = (scenario: Scenario) => {
    // Implement this function to show scenario details
    console.log(scenario);
  };

  return (
    <div>
      <svg ref={svgRef}></svg>
      <div id="scenario" style={{ display: 'none' }}>
        <h3 id="scenario-title"></h3>
        <p id="scenario-desc"></p>
        <div id="scenario-ref"></div>
      </div>
    </div>
  );
};

export default ScenarioVisualization;