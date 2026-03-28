"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function D3RiskDonut({ data }) {
  const ref = useRef(null);

  useEffect(() => {
    const svg = d3.select(ref.current);
    const width = 320;
    const height = 320;
    const radius = Math.min(width, height) / 2;

    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const chart = svg
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    const pie = d3.pie().sort(null).value((d) => d.value);
    const arc = d3.arc().innerRadius(radius * 0.58).outerRadius(radius * 0.88);

    chart
      .selectAll("path")
      .data(pie(data))
      .join("path")
      .attr("d", arc)
      .attr("fill", (d) => d.data.color)
      .attr("stroke", "var(--surface-container-lowest)")
      .attr("stroke-width", 6);

    chart
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", -8)
      .attr("fill", "var(--outline)")
      .style("font-size", "12px")
      .style("text-transform", "uppercase")
      .style("letter-spacing", "0.18em")
      .text("Risk Level");

    chart
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", 26)
      .attr("fill", "var(--error)")
      .style("font-size", "40px")
      .style("font-weight", "800")
      .text("90%");
  }, [data]);

  return <svg ref={ref} role="img" aria-label="Risk composition donut chart" />;
}
