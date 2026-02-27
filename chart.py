"""
V0 — PoC: Download AAPL data via yfinance and render an ECharts line chart
in a self-contained HTML file.
"""

import json
import webbrowser
from pathlib import Path

import yfinance as yf

TICKER = "AAPL"
PERIOD = "1y"
OUTPUT = Path(__file__).parent / "chart.html"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{ticker} — Price Chart</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #1a1a2e; display: flex; justify-content: center; align-items: center; height: 100vh; }}
    #chart {{ width: 95vw; height: 90vh; }}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    var chart = echarts.init(document.getElementById('chart'));
    var dates = {dates};
    var prices = {prices};
    chart.setOption({{
      title: {{
        text: '{ticker} — Closing Price (last {period})',
        left: 'center',
        textStyle: {{ color: '#e0e0e0' }}
      }},
      tooltip: {{
        trigger: 'axis',
        formatter: function(params) {{
          var p = params[0];
          return p.name + '<br/>Close: $' + p.value.toFixed(2);
        }}
      }},
      xAxis: {{
        type: 'category',
        data: dates,
        axisLabel: {{ color: '#aaa' }},
        axisLine: {{ lineStyle: {{ color: '#444' }} }}
      }},
      yAxis: {{
        type: 'value',
        scale: true,
        axisLabel: {{ color: '#aaa', formatter: '$ {{value}}' }},
        splitLine: {{ lineStyle: {{ color: '#333' }} }}
      }},
      series: [{{
        type: 'line',
        data: prices,
        smooth: false,
        symbol: 'none',
        lineStyle: {{ width: 2, color: '#00b4d8' }},
        areaStyle: {{
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {{ offset: 0, color: 'rgba(0,180,216,0.35)' }},
            {{ offset: 1, color: 'rgba(0,180,216,0.02)' }}
          ])
        }}
      }}],
      backgroundColor: '#1a1a2e',
      grid: {{ left: 80, right: 40, top: 60, bottom: 40 }}
    }});
    window.addEventListener('resize', function() {{ chart.resize(); }});
  </script>
</body>
</html>
"""


def main():
    print(f"Downloading {TICKER} data ({PERIOD})…")
    df = yf.download(TICKER, period=PERIOD, auto_adjust=True)

    # yfinance may return MultiIndex columns; flatten
    if isinstance(df.columns, __import__('pandas').MultiIndex):
        df.columns = df.columns.get_level_values(0)

    dates = df.index.strftime("%Y-%m-%d").tolist()
    prices = [round(float(v), 2) for v in df["Close"].values]

    html = HTML_TEMPLATE.format(
        ticker=TICKER,
        period=PERIOD,
        dates=json.dumps(dates),
        prices=json.dumps(prices),
    )

    OUTPUT.write_text(html)
    print(f"Chart saved to {OUTPUT}")
    webbrowser.open(OUTPUT.as_uri())


if __name__ == "__main__":
    main()
