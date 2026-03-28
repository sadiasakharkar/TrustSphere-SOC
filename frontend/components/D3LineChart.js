"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function D3LineChart({ data }) {
  const ref = useRef(null);

  useEffect(() => {
    const svg = d3.select(ref.current);
    const width = 720;
    const height = 280;
    const margin = { top: 20, right: 24, bottom: 36, left: 44 };

    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const x = d3
      .scalePoint()
      .domain(data.map((d) => d.minute))
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.total) + 300])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const area = d3
      .area()
      .x((d) => x(d.minute))
      .y0(height - margin.bottom)
      .y1((d) => y(d.total))
      .curve(d3.curveCatmullRom.alpha(0.5));

    const line = d3
      .line()
      .x((d) => x(d.minute))
      .y((d) => y(d.suspicious))
      .curve(d3.curveCatmullRom.alpha(0.5));

    svg
      .append("path")
      .datum(data)
      .attr("d", area)
      .attr("fill", "url(#eventsGradient)")
      .attr("opacity", 0.8);

    svg
      .append("path")
      .datum(data)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "var(--error)")
      .attr("stroke-width", 3);

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).tickSize(0))
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll("text").attr("fill", "var(--outline)").style("font-size", "11px"));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(4).tickSize(-width + margin.left + margin.right))
      .call((g) => g.select(".domain").remove())
      .call((g) => g.selectAll("line").attr("stroke", "rgba(110, 120, 129, 0.15)"))
      .call((g) => g.selectAll("text").attr("fill", "var(--outline)").style("font-size", "11px"));

    svg
      .append("g")
      .selectAll("circle")
      .data(data)
      .join("circle")
      .attr("cx", (d) => x(d.minute))
      .attr("cy", (d) => y(d.suspicious))
      .attr("r", 4.5)
      .attr("fill", "var(--surface-container-lowest)")
      .attr("stroke", "var(--error)")
      .attr("stroke-width", 2);
  }, [data]);

  return (
    <svg ref={ref} role="img" aria-label="Live event volume and suspicious signal trend">
      <defs>
        <linearGradient id="eventsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="var(--primary-container)" />
          <stop offset="100%" stopColor="rgba(0, 174, 239, 0.04)" />
        </linearGradient>
      </defs>
    </svg>
  );
}
