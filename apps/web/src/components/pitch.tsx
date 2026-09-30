import type { Explorer } from "@/lib/contracts";
import { copy, type Locale } from "@/lib/content";
export function Pitch({
  data,
  locale,
  frameIndex,
}: {
  data: Explorer;
  locale: Locale;
  frameIndex: number;
}) {
  const c = copy[locale],
    snapshot = data.tracking_snapshots[frameIndex];
  const max = Math.max(1, ...data.spatial_bins.map((b) => b.count));
  const title = snapshot ? c.tracking : c.spatial;
  return (
    <figure className="pitch-figure">
      <div className="figure-heading">
        <h3>{title}</h3>
        <span>
          {snapshot
            ? `${snapshot.timestamp_seconds.toFixed(1)} s`
            : `${data.spatial_sample_size.toLocaleString(locale)} ${c.sampled}`}
        </span>
      </div>
      <svg
        viewBox="-3 -3 111 74"
        role="img"
        aria-label={`${title}. ${snapshot ? c.trackingNote : c.spatialNote}`}
      >
        <rect x="0" y="0" width="105" height="68" fill="#eef2ec" />
        {!snapshot &&
          data.spatial_bins.map((b, i) => (
            <rect
              key={i}
              x={b.x - 4.375}
              y={68 - b.y - 4.25}
              width="8.75"
              height="8.5"
              fill="#176448"
              opacity={0.06 + (0.78 * b.count) / max}
            >
              <title>{`${c.count}: ${b.count}; x ${b.x.toFixed(1)} m, y ${b.y.toFixed(1)} m`}</title>
            </rect>
          ))}
        <g fill="none" stroke="#788a7d" strokeWidth=".25">
          <rect width="105" height="68" />
          <path d="M52.5 0V68" />
          <circle cx="52.5" cy="34" r="9.15" />
          <rect x="0" y="13.84" width="16.5" height="40.32" />
          <rect x="88.5" y="13.84" width="16.5" height="40.32" />
          <rect x="0" y="24.84" width="5.5" height="18.32" />
          <rect x="99.5" y="24.84" width="5.5" height="18.32" />
          <path d="M16.5 26.69 A9.15 9.15 0 0 1 16.5 41.31 M88.5 26.69 A9.15 9.15 0 0 0 88.5 41.31" />
          <rect x="-1.5" y="30.34" width="1.5" height="7.32" />
          <rect x="105" y="30.34" width="1.5" height="7.32" />
        </g>
        <g fill="#788a7d">
          <circle cx="52.5" cy="34" r=".4" />
          <circle cx="11" cy="34" r=".4" />
          <circle cx="94" cy="34" r=".4" />
        </g>
        {snapshot?.points.map((p, i) => (
          <g
            key={i}
            fill={
              p.object_type === "ball"
                ? "#222f37"
                : p.team === data.match.home
                  ? "#176448"
                  : "#95502e"
            }
            stroke="#fff"
            strokeWidth=".3"
          >
            <title>{`${p.name} · ${p.team ?? "B"} · ${p.is_detected ? c.detected : c.extrapolated} · ${p.x.toFixed(1)}, ${p.y.toFixed(1)} m`}</title>
            {p.is_detected ? (
              <circle cx={p.x} cy={68 - p.y} r="1.5" />
            ) : (
              <rect
                x={p.x - 1.35}
                y={68 - p.y - 1.35}
                width="2.7"
                height="2.7"
              />
            )}
            {p.object_type === "player" && (
              <text
                x={p.x}
                y={68 - p.y + 0.6}
                textAnchor="middle"
                fontSize="1.8"
                fill="white"
                stroke="none"
              >
                {p.team === data.match.home ? "H" : "A"}
              </text>
            )}
            {p.object_type === "ball" && (
              <text x={p.x + 1.5} y={68 - p.y} fontSize="2.6" stroke="none">
                B
              </text>
            )}
          </g>
        ))}
      </svg>
      <figcaption>{snapshot ? c.trackingNote : c.spatialNote}</figcaption>
      {snapshot ? (
        <p className="legend">
          <span>H · {data.match.home}</span>
          <span>A · {data.match.away}</span>
        </p>
      ) : (
        <p className="legend">
          {c.count}: 1 — {max} · 105 × 68 m
        </p>
      )}
      <details>
        <summary>
          {locale === "nl"
            ? "Bekijk de waarden als tabel"
            : "View values as a table"}
        </summary>
        <div className="table-wrap">
          <table>
            <caption>{title}</caption>
            <thead>
              <tr>
                <th>{snapshot ? c.player : "x / y (m)"}</th>
                <th>{snapshot ? "x / y (m)" : c.count}</th>
              </tr>
            </thead>
            <tbody>
              {snapshot
                ? snapshot.points.map((p, i) => (
                    <tr key={i}>
                      <td>
                        {p.name}
                        <small>{p.team}</small>
                      </td>
                      <td>
                        {p.x.toFixed(1)} / {p.y.toFixed(1)} ·{" "}
                        {p.is_detected ? c.detected : c.extrapolated}
                      </td>
                    </tr>
                  ))
                : data.spatial_bins.map((b, i) => (
                    <tr key={i}>
                      <td>
                        {b.x.toFixed(1)} / {b.y.toFixed(1)}
                      </td>
                      <td>{b.count}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
