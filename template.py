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
    var spans = {spans};
    var spanSeries = spans.map(function(s) {{
      var upColor = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        {{ offset: 0, color: 'rgba(0,230,118,0.30)' }},
        {{ offset: 1, color: 'rgba(0,230,118,0.03)' }}
      ]);
      var dnColor = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        {{ offset: 0, color: 'rgba(255,23,68,0.30)' }},
        {{ offset: 1, color: 'rgba(255,23,68,0.03)' }}
      ]);
      var data = dates.map(function(d, i) {{
        return (d >= s.start && d <= s.end) ? prices[i] : null;
      }});
      return {{
        type: 'line',
        data: data,
        silent: true,
        showSymbol: false,
        lineStyle: {{ opacity: 0 }},
        areaStyle: {{ color: s.up ? upColor : dnColor }},
        z: 1
      }};
    }});
    chart.setOption({{
      title: {{
        text: '{ticker} — Closing Price ({range_label})',
        left: 'center',
        textStyle: {{ color: '#e0e0e0' }}
      }},
      tooltip: {{
        trigger: 'item',
        confine: true,
        extraCssText: 'max-width: 350px; white-space: normal;',
        axisPointer: {{
          type: 'cross',
          crossStyle: {{ color: '#888' }},
          lineStyle: {{ color: '#888', type: 'dashed' }}
        }},
        formatter: function(params) {{
          if (params.componentType === 'markPoint') {{
            var d = params.data;
            return d.tooltip ? d.tooltip.formatter : d.value;
          }}
          return params.name + '<br/>Close: $' + params.value.toFixed(2);
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
      series: spanSeries.concat([{{
        type: 'line',
        data: prices,
        smooth: false,
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: false,
        lineStyle: {{ width: 2, color: '#00b4d8' }},
        areaStyle: {{
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {{ offset: 0, color: 'rgba(0,180,216,0.35)' }},
            {{ offset: 1, color: 'rgba(0,180,216,0.02)' }}
          ])
        }},
        markPoint: {{
          symbol: 'triangle',
          symbolSize: 9,
          data: markers,
          label: {{
            show: false
          }}
        }}
      }}]),
      backgroundColor: '#1a1a2e',
      grid: {{ left: 80, right: 40, top: 60, bottom: 40 }}
    }});
    window.addEventListener('resize', function() {{ chart.resize(); }});
  </script>
</body>
</html>
"""
