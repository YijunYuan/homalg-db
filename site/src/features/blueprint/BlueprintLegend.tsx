import type { ReactNode } from "react";
import { t } from "../../i18n/t";
import { blueprintColors as colors } from "./appearance";
import "./BlueprintLegend.css";

type NodeKind = "source" | "auxiliary" | "bridge" | "cited" | "external";

function NodeSymbol({
  kind = "source",
  fill = colors.inProgress.fill,
  stroke = colors.inProgress.border,
  dashed = false,
}: {
  kind?: NodeKind;
  fill?: string;
  stroke?: string;
  dashed?: boolean;
}) {
  const outline = {
    fill,
    stroke,
    strokeWidth: 2,
    strokeDasharray:
      dashed || kind === "cited" || kind === "external" ? "4 2" : undefined,
  };
  return (
    <svg
      className="blueprint-legend-symbol"
      viewBox="0 0 36 26"
      aria-hidden="true"
      focusable="false"
    >
      {kind === "bridge" ? (
        <polygon points="18,2 33,13 18,24 3,13" {...outline} />
      ) : kind === "cited" ? (
        <polygon points="8,4 28,4 34,13 28,22 8,22 2,13" {...outline} />
      ) : kind === "auxiliary" ? (
        <rect x="8" y="8" width="20" height="10" rx="2" {...outline} />
      ) : (
        <rect x="3" y="5" width="30" height="16" rx="3" {...outline} />
      )}
    </svg>
  );
}

function EdgeSymbol({
  hollow = false,
  dashed = false,
  undeclared = false,
}: {
  hollow?: boolean;
  dashed?: boolean;
  undeclared?: boolean;
}) {
  const stroke = undeclared ? colors.undeclaredEdge : colors.edge;
  return (
    <svg
      className="blueprint-legend-symbol"
      viewBox="0 0 36 26"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M3 13H25"
        stroke={stroke}
        strokeWidth="2"
        strokeDasharray={dashed ? "4 2" : undefined}
      />
      <path
        d="M24 7L33 13L24 19Z"
        fill={hollow ? colors.canvas : stroke}
        stroke={stroke}
        strokeWidth="2"
      />
    </svg>
  );
}

function Key({ symbol, children }: { symbol: ReactNode; children: ReactNode }) {
  return (
    <li className="blueprint-legend-key">
      {symbol}
      <span>{children}</span>
    </li>
  );
}

function Group({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="blueprint-legend-group" role="group" aria-label={label}>
      <span className="blueprint-legend-heading" aria-hidden="true">
        {label}
      </span>
      <ul className="blueprint-legend-items">{children}</ul>
    </div>
  );
}

/** Compact preview with the complete Cytoscape notation behind a native disclosure. */
export function BlueprintLegend() {
  return (
    <section className="blueprint-legend" aria-label={t("doc.legend.title")}>
      <details className="blueprint-legend-disclosure" name="blueprint-tools">
        <summary>
          <span>{t("doc.legend.more")}</span>
          <span className="blueprint-legend-preview" aria-hidden="true">
            <span className="blueprint-legend-preview-colors">
              <NodeSymbol />
              <NodeSymbol
                fill={colors.statementComplete.fill}
                stroke={colors.statementComplete.border}
              />
              <NodeSymbol
                fill={colors.proofComplete.fill}
                stroke={colors.proofComplete.border}
              />
              <NodeSymbol
                fill={colors.error.fill}
                stroke={colors.error.border}
              />
              <NodeSymbol fill={colors.informalOrPruned} />
            </span>
            <span className="blueprint-legend-preview-shapes">
              <NodeSymbol />
              <NodeSymbol kind="auxiliary" />
              <NodeSymbol kind="bridge" />
              <NodeSymbol kind="cited" />
              <NodeSymbol kind="external" fill={colors.external} />
            </span>
          </span>
        </summary>
        <div className="blueprint-legend-details">
          <Group label={t("doc.legend.colors")}>
            <Key symbol={<NodeSymbol />}>
              {t("enum.HeadlineStatus.in-progress")}
            </Key>
            <Key
              symbol={
                <NodeSymbol
                  fill={colors.statementComplete.fill}
                  stroke={colors.statementComplete.border}
                />
              }
            >
              {t("enum.HeadlineStatus.statement-complete")}
            </Key>
            <Key
              symbol={
                <NodeSymbol
                  fill={colors.proofComplete.fill}
                  stroke={colors.proofComplete.border}
                />
              }
            >
              {t("enum.HeadlineStatus.proof-complete")}
            </Key>
            <Key
              symbol={
                <NodeSymbol
                  fill={colors.error.fill}
                  stroke={colors.error.border}
                />
              }
            >
              {t("doc.legend.confirmedError")}
            </Key>
            <Key symbol={<NodeSymbol fill={colors.informalOrPruned} />}>
              {t("doc.legend.informalOrPruned")}
            </Key>
          </Group>
          <Group label={t("doc.legend.shapes")}>
            <Key symbol={<NodeSymbol />}>{t("doc.legend.source")}</Key>
            <Key symbol={<NodeSymbol kind="auxiliary" />}>
              {t("doc.legend.auxiliary")}
            </Key>
            <Key symbol={<NodeSymbol kind="bridge" />}>
              {t("doc.legend.bridge")}
            </Key>
            <Key symbol={<NodeSymbol kind="cited" />}>
              {t("doc.legend.cited")}
            </Key>
            <Key symbol={<NodeSymbol kind="external" fill={colors.external} />}>
              {t("doc.legend.external")}
            </Key>
          </Group>
          <Group label={t("doc.legend.outlines")}>
            <Key symbol={<NodeSymbol stroke={colors.foundation} />}>
              {t("doc.legend.foundation")}
            </Key>
            <Key symbol={<NodeSymbol stroke={colors.deviation} />}>
              {t("doc.legend.deviation")}
            </Key>
            <Key symbol={<NodeSymbol stroke={colors.dispute} dashed />}>
              {t("doc.legend.dispute")}
            </Key>
            <Key symbol={<NodeSymbol stroke={colors.extraAxioms} />}>
              {t("doc.legend.extraAxioms")}
            </Key>
          </Group>
          <Group label={t("doc.legend.edges")}>
            <Key symbol={<EdgeSymbol />}>{t("doc.legend.statementEdge")}</Key>
            <Key symbol={<EdgeSymbol hollow />}>
              {t("doc.legend.proofEdge")}
            </Key>
            <Key symbol={<EdgeSymbol dashed />}>
              {t("doc.legend.unverifiedEdge")}
            </Key>
            <Key symbol={<EdgeSymbol undeclared />}>
              {t("doc.legend.undeclaredEdge")}
            </Key>
          </Group>
          <p className="blueprint-legend-note">{t("doc.legend.direction")}</p>
          <p className="blueprint-legend-note">{t("doc.legend.completion")}</p>
        </div>
      </details>
    </section>
  );
}
