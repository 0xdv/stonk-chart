"""ECharts HTML template for the annotated stock chart."""

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
    var markers = {markers};
    chart.setOption({{
      title: {{
        text: '{ticker} — Closing Price ({range_label})',
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
        }},
        markPoint: {{
          symbol: 'triangle',
          symbolSize: 18,
          data: markers,
          label: {{
            show: false
          }}
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
