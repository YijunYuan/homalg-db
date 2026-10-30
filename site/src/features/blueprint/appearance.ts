/** Graph colors stay fixed against the light canvas in both page themes. */
export const blueprintColors = {
  canvas: "#f6f8f6",
  inProgress: { fill: "#ffffff", border: "#63776a" },
  statementComplete: { fill: "#d6efdc", border: "#3f7850" },
  proofComplete: { fill: "#247347", border: "#164d2e" },
  error: { fill: "#ffe0dc", border: "#b02e22" },
  informalOrPruned: "#d5dcd7",
  external: "#edf2ef",
  foundation: "#3c4650",
  deviation: "#bc5c00",
  dispute: "#8052a3",
  extraAxioms: "#b77b00",
  edge: "#778a7e",
  undeclaredEdge: "#c6691b",
} as const;

export const blueprintShapes = {
  source: "roundrectangle",
  auxiliary: "roundrectangle",
  bridge: "diamond",
  cited: "hexagon",
} as const;
