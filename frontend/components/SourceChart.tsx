import React, { memo, useCallback, useRef, useState } from "react";
import { tSNE } from "@/utils/tsne";
import { useInterval } from "@/utils/useInterval";
import * as d3 from "d3";

type SourceChartProps = {
    sources: any;
    setSelectedArticleId: (id: string) => void; // function to set selected article id
    isLoading: boolean; // not necessary but to get around memoization
};
const SourceChart = memo(
    ({ sources, setSelectedArticleId, isLoading }: SourceChartProps) => {
        console.log("debug: isLoading", isLoading);
        const filteredSourceInfo = filterSourceInfo(sources);
        console.log("debug: filteredSourceInfo", sources, filteredSourceInfo);
        const [svgRef, setSvgRef] = useState(null);
        const onSvgRefChange = useCallback((node: any) => {
            setSvgRef(node);
        }, []);
        // const svgRef = useRef(null);

        let tsne: any;
        const svg = d3.select(svgRef);
        let tx = 0,
            ty = 0;
        let ss = 1;
        let tsneCoordinates: any = [];
        const colorSchemes = [
            ...d3.schemeCategory10,
            ...d3.schemeAccent,
            ...d3.schemeDark2,
            ...d3.schemePaired,
            ...d3.schemePastel1,
            ...d3.schemePastel2,
            ...d3.schemeSet1,
            ...d3.schemeSet2,
            ...d3.schemeSet3,
            ...d3.schemeTableau10,
        ];
        const colorScale = d3.scaleOrdinal(colorSchemes); // Create a color scale with 10 categorical colors

        useInterval(step, 100);
        console.log("debug: sources ");
        console.log("debug: svgRef", svgRef);
        if (
            sources.embeddingSimilarities &&
            sources.embeddingSimilarities.length > 0 &&
            svgRef
        ) {
            console.log("debug: drawing embedding");
            const opt = { epsilon: 10, perplexity: 5, dim: 2 };
            tsne = new tSNE(opt);
            // initialize data.
            tsne.initDataDist(sources.embeddingSimilarities);
            drawEmbedding();

            for (let k = 0; k < 100; k++) {
                tsne.step(); // every time you call this, solution gets better
                updateEmbedding();
            }

            tsneCoordinates = tsne.getSolution(); // Y is an array of 2-D points that you can plot
            console.log("tsneCoordinates", tsneCoordinates);
        }

        function filterSourceInfo(sources: any) {
            if (!sources.sourceEmbeddings) return [];
            const ids = sources.sourceEmbeddings.map(
                (similarity: any) => similarity.articleId
            );
            const filteredSources = sources.sourceInfo.filter(
                (source: any) => ids.indexOf(source._id) > -1
            );
            return filteredSources;
        }

        function updateEmbedding() {
            tsneCoordinates = tsne.getSolution(); // Y is an array of 2-D points that you can plot
            svg.selectAll(".u")
                .data(filteredSourceInfo)
                .attr(
                    "transform",
                    (d, i) =>
                        `translate(${
                            tsneCoordinates[i][0] * 20 * ss + tx + 400
                        },${tsneCoordinates[i][1] * 20 * ss + ty + 300})`
                );
        }

        function drawEmbedding() {
            const g = svg
                .selectAll(".b")
                .data(filteredSourceInfo)
                .enter()
                .append("g")
                .attr("class", "u cursor-pointer")
                .attr("id", (d: any) => `node-${d._id}`)
                .on("click", handleClick);

            // g.append("text")
            //     .attr("text-anchor", "top")
            //     .attr("font-size", 12)
            //     .attr("fill", "#333")
            //     .text((d: any) => d.name);
            g.each(function (d: any) {
                const hasImage = d.provider[0].image;
                if (hasImage) {
                    const imgUrl = d.provider[0].image.thumbnail.contentUrl;
                    d3.select(this)
                        .append("svg:image")
                        .attr("xlink:href", imgUrl)
                        .attr("x", 0) // Adjust the position of the image if needed
                        .attr("y", 2) // Adjust the position of the image if needed
                        .attr("width", 64)
                        .attr("height", 64);

                    d3.select(this)
                        .append("text")
                        .attr("text-anchor", "top")
                        .attr("font-size", 12)
                        .attr("fill", "#333")
                        .text((d: any) =>
                            d.provider[0].name.replace("on MSN.com", "")
                        );
                } else {
                    console.log(
                        "colorIndex",
                        d.provider[0].name
                            .replace("on MSN.com", "")
                            .replace(" ", "")
                    );
                    d3.select(this)
                        .append("circle")
                        .attr("cx", 0) // Set the x-coordinate of the center of the circle
                        .attr("cy", 0) // Set the y-coordinate of the center of the circle
                        .attr("r", 32) // Set the radius of the circle
                        .attr(
                            "fill",
                            colorScale(
                                d.provider[0].name
                                    .replace("on MSN.com", "")
                                    .replace(" ", "")
                            )
                        ); // Set the fill color based on the index of the data point

                    d3.select(this)
                        .append("text")
                        .attr("text-anchor", "middle")
                        .attr("font-size", 12)
                        .attr("fill", "#333")
                        .attr("x", -32)
                        .attr("y", -36)
                        .text((d: any) =>
                            d.provider[0].name.replace("on MSN.com", "")
                        );
                }
            });

            const zoomListener = d3
                .zoom()
                .scaleExtent([0.1, 10])
                .on("zoom", zoomHandler);
            svg.call(zoomListener as any);
        }

        function zoomHandler(event: any) {
            tx = event.transform.x - 400;
            ty = event.transform.y - 300;
            ss = event.transform.k;
            updateEmbedding();
        }

        let selectedElement: any = null;

        function handleClick(event: any, d: any) {
            console.log("clicked something");
            console.log("event clicked", event);
            // `event` is the click event object, `d` is the data bound to the clicked element
            console.log("Clicked element:", d);

            // Check if the clicked element is already selected
            const isSelected = svg.select(`#node-${d._id}`).classed("selected");

            // Remove "selected" class from all other elements
            svg.selectAll(".u").classed(
                "selected",
                (tempD: any) => tempD._id == d._id && !isSelected
            );

            // // Remove "selected" class from the clicked element if it is already selected
            // svg.select(`#node-${d._id}`).classed("selected", !isSelected);

            setSelectedArticleId(isSelected ? null : d._id);
            selectedElement = d._id;
            // Add your custom click event handling code here
            const g = d3.select(event.currentTarget);
        }

        function step() {
            if (
                sources.embeddingSimilarities &&
                sources.embeddingSimilarities.length > 0 &&
                svgRef &&
                tsne &&
                tsne.iter < 2500
            ) {
                tsne.step(); // every time you call this, solution gets better
                updateEmbedding();
            }
        }

        return (
            <svg
                ref={onSvgRefChange}
                className="w-full h-full"
                id="embed"
            ></svg>
        );
    }
);
SourceChart.displayName = "SourceChart";

export default SourceChart;
