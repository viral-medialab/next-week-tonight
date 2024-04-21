import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

const AxisPlane = () => {
  const [polarization, setPolarization] = useState(50);
  const [probability, setProbability] = useState(50);
  const d3Container = useRef(null);

  useEffect(() => {
    if (d3Container.current) {
      const margin = { top: 20, right: 15, bottom: 60, left: 60 };
      const width = 500 - margin.left - margin.right;
      const height = 500 - margin.top - margin.bottom;

      // Remove the old svg
      d3.select(d3Container.current).select("svg").remove();

      const svg = d3.select(d3Container.current)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // X scale
      const x = d3.scaleLinear()
        .domain([0, 100])
        .range([0, width])
        .nice();

      // Y scale
      const y = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0])
        .nice();

      // X axis
      const xAxis = d3.axisBottom(x)
        .ticks(7)
        .tickFormat(value => `${value}%`);

      // Y axis
      const yAxis = d3.axisLeft(y)
        .ticks(7)
        .tickFormat(value => `${value}%`);

      // Append axes to the svg
      svg.append('g')
        .attr('transform', `translate(0, ${height})`)
        .call(xAxis);

      svg.append('g')
        .call(yAxis);

      // Label for the x-axis
      svg.append("text")             
        .attr("transform", `translate(${width/2}, ${height + margin.top + 20})`)
        .style("text-anchor", "middle")
        .text("Polarization");

      // Label for the y-axis
      svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x",0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Probability"); 

      // Function to update the headline based on the position
      const updateHeadline = (xValue, yValue) => {
        setPolarization(xValue);
        setProbability(yValue);
      };

      // Circle representing the chosen value
      const circle = svg.append('circle')
        .attr('r', 10)
        .attr('cx', x(polarization))
        .attr('cy', y(probability))
        .style('fill', 'blue')
        .style('cursor', 'pointer')
        .call(d3.drag()
          .on('drag', function (event) {
            let xValue = x.invert(event.x);
            let yValue = y.invert(event.y);
            xValue = Math.min(100, Math.max(0, xValue));
            yValue = Math.min(100, Math.max(0, yValue));
            d3.select(this)
              .attr('cx', x(xValue))
              .attr('cy', y(yValue));
            updateHeadline(Math.round(xValue), Math.round(yValue));
          }));
    }
  }, [polarization, probability]); // Redraw graph when data changes

  return (
    <div>
      <div ref={d3Container} />
      <div>
        Headline: {`Polarization: ${polarization}%, Probability: ${probability}%`}
      </div>
    </div>
  );
};

export default AxisPlane;