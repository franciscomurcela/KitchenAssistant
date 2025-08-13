// scores.js extraído de scores.html
// ...todo o conteúdo do <script> de scores.html, exceto tags <script>...
// Inclui funções: setActive, logout, updateGaugeChart, updateMetricsChart, updateBarLabels, toggleScale, toggleSwarmplot, updateStackedLineChart, onScroll, fetchUsers, fetchMetrics, fetchJustificacoes, e o código do DOMContentLoaded e scroll suave.

Chart.defaults.font.size = 20;
Chart.defaults.font.family = 'Arial';
Chart.register(ChartDataLabels);

function setActive(el) {
  document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
}

function logout() {
  fetch('/api/logout', { method: 'POST', credentials: 'include' })
    .then(() => location.href = '/login');
}

function updateGaugeChart(val) {
  const gauge = echarts.init(document.getElementById('gaugeChart'));
  let label, color;
  if (val < 20) {
    label = 'Muito Mau'; color = '#b50000';
  } else if (val < 40) {
    label = 'Mau'; color = '#ea6d1c';
  } else if (val < 60) {
    label = 'Mediocre'; color = '#FFD700';
  } else if (val < 80) {
    label = 'Bom'; color = '#92d663';
  } else {
    label = 'Excelente'; color = '#019e04';
  }
  gauge.setOption({
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 10,
      axisLine: {
        lineStyle: {
          width: 8,
          color: [
            [0.2, '#b50000'],
            [0.4, '#ea6d1c'],
            [0.6, '#FFD700'],
            [0.8, '#92d663'],
            [1, '#019e04']
          ]
        }
      },
      pointer: {
        length: '70%',
        width: 10,
        offsetCenter: ['0', '-15%'],
        itemStyle: { color: 'auto' }
      },
      axisLabel: {
        distance: -50,
        fontSize: 16,
        formatter: '{value}'
      },
      detail: {
        offsetCenter: ['0', '40%'],
        fontSize: 24,
        valueAnimation: true,
        formatter: ` {b|${label}}\n  {c|${val}%}`,
        rich: {
          b: { fontWeight: 'bold', fontSize: 32, color: color },
          c: { fontWeight: 'bold', fontSize: 32, color: color }
        }
      },
      data: [{ value: val, name: '' }]
    }]
  });
}

let metricsData = null;
let showPercent = true;
let showSwarmplot = false;
let selectedUser = "Todos";

function updateMetricsChart(metrics, rawFeedbacks) {
  metricsData = metrics;
  const barDiv = document.getElementById('metricsChart');
  const swarmDiv = document.getElementById('swarmplotDiv');
  // Always use the static div, just clear and toggle display
  if (window.metricsChartInstance) window.metricsChartInstance.destroy();

  if (!showSwarmplot) {
    // Bar chart mode
    barDiv.style.display = '';
    swarmDiv.style.display = 'none';
    let dataArr = showPercent
      ? [metrics.facil_de_usar, metrics.estou_satisfeito, metrics.usaria_novamente, metrics.comunica_bem, metrics.faz_oque_quero]
      : [metrics.facil_de_usar, metrics.estou_satisfeito, metrics.usaria_novamente, metrics.comunica_bem, metrics.faz_oque_quero].map(v => +(v/20).toFixed(2));
    let yMax = showPercent ? 100 : 5;
    let yLabel = showPercent ? 'Percentagem (%)' : 'Escala (0-5)';
    // Cada barra é um dataset para permitir toggle na legenda
    const barColors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF'];
    const barLabels = ['Fácil de Usar','Estou Satisfeito','Usaria Novamente','Comunica Bem','Faz o que eu quero'];
    const datasets = barLabels.map((label, i) => ({
      label: label,
      data: [dataArr[i]],
      backgroundColor: barColors[i],
      datalabels: {
        anchor: 'center', align: 'center', color: '#fff', font: { size: 18, weight: 'bold' },
        formatter: v => showPercent ? (v + '%') : v
      }
    }));
    window.metricsChartInstance = new Chart(barDiv.getContext('2d'), {
      type: 'bar',
      data: {
        labels: [''],
        datasets: datasets
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: yMax,
            min: 0,
            suggestedMin: 0
          }
        },
        plugins: {
          legend: { display: true, position: 'top', labels: { font: { size: 16 } },
            onClick: (e, legendItem, legend) => {
              const ci = legend.chart;
              const dsIndex = legendItem.datasetIndex;
              const meta = ci.getDatasetMeta(dsIndex);
              meta.hidden = meta.hidden === null ? !ci.data.datasets[dsIndex].hidden : null;
              ci.update();
              updateBarLabels(ci);
            }
          },
          datalabels: { display: true }
        }
      },
      plugins: [{
        id: 'barLabelBase',
        afterDatasetsDraw(chart) {
          const ctx = chart.ctx;
          ctx.save();
          const metas = chart.getSortedVisibleDatasetMetas();
          metas.forEach((meta) => {
            const bar = meta.data[0];
            if (!bar) return;
            const datasetIndex = meta.index;
            let label = chart.data.datasets[datasetIndex].label;
            if (label === 'Faz o que eu quero') {
              label = 'Faz o que\neu quero';
            }
            let barWidth = 0;
            if (bar.width) {
              barWidth = bar.width;
            } else if (bar.x !== undefined && bar.base !== undefined) {
              barWidth = Math.abs(bar.base - bar.x) * 2;
            } else {
              barWidth = 40;
            }
            let fontSize = 15;
            ctx.font = `bold ${fontSize}px Arial`;
            let labelLines = label.split('\n');
            let textWidth = Math.max(...labelLines.map(l => ctx.measureText(l).width));
            if (textWidth > barWidth - 8 && labelLines.length === 1) {
              const words = label.split(' ');
              if (words.length > 2) {
                const mid = Math.floor(words.length/2);
                labelLines = [words.slice(0,mid).join(' '), words.slice(mid).join(' ')];
                textWidth = Math.max(...labelLines.map(l => ctx.measureText(l).width));
              }
            }
            if (textWidth > barWidth - 8) {
              ctx.font = `bold 13px Arial`;
              if (labelLines.some(l => ctx.measureText(l).width > barWidth - 8)) {
                ctx.font = `bold 11px Arial`;
              }
            }
            const x = bar.x;
            let y = bar.y - 28;
            ctx.fillStyle = '#222';
            ctx.textAlign = 'center';
            labelLines.forEach((line, idx) => {
              ctx.fillText(line, x, y + idx*15);
            });
          });
          ctx.restore();
        }
      }]
    });
    updateBarLabels(window.metricsChartInstance);
    document.getElementById('toggleScaleBtn').innerText = showPercent ? 'Mostrar em escala 0-5' : 'Mostrar em percentagem';
    document.getElementById('toggleSwarmBtn').innerText = 'Mostrar Swarmplot';
  } else {
    // Swarmplot mode
    barDiv.style.display = 'none';
    swarmDiv.style.display = 'block';
    swarmDiv.innerHTML = '';
    let metricNames = ['facil_de_usar','estou_satisfeito','usaria_novamente','comunica_bem','faz_oque_quero'];
    let labels = ['Fácil de Usar','Estou Satisfeito','Usaria Novamente','Comunica Bem','Faz o que eu quero'];
    let colors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF'];
    let barMeans = metricNames.map(m => showPercent ? metrics[m] : +(metrics[m]/20).toFixed(2));
    let barTrace = {
      x: labels,
      y: barMeans,
      type: 'bar',
      marker: { color: colors, opacity: 0.25 },
      name: 'Média',
      width: 0.6,
      hoverinfo: 'y',
      showlegend: false,
      text: barMeans.map(v => v.toFixed(2)),
      textposition: 'inside',
      textfont: { size: 18, color: '#222', family: 'Arial' }
    };
    let traces = metricNames.map((m, i) => {
      let vals = (rawFeedbacks && rawFeedbacks[m]) ? rawFeedbacks[m] : [];
      let plotVals = vals.map(v => showPercent ? v*20 : v);
      let perguntas = (rawFeedbacks && rawFeedbacks[m + '_perguntas']) ? rawFeedbacks[m + '_perguntas'] : [];
      let respostas = (rawFeedbacks && rawFeedbacks[m + '_respostas']) ? rawFeedbacks[m + '_respostas'] : [];
      return {
        y: plotVals,
        x: Array(plotVals.length).fill(labels[i]),
        name: labels[i],
        type: 'box',
        boxpoints: 'all',
        boxmean: false, // Apenas boxplot padrão, linha de mediana automática
        jitter: 0.5,
        pointpos: 0,
        marker: { color: '#222', size: 8, opacity: 0.7 },
        line: { color: colors[i] },
        fillcolor: colors[i]+"33",
        opacity: 1,
        width: 0.5,
        showlegend: false,
        text: plotVals.map((v, idx) => {
          let pergunta = perguntas[idx] || '';
          let resposta = respostas[idx] || v;
          return pergunta ? pergunta + ': ' + resposta : resposta;
        }),
        hoverinfo: 'text',
      };
    });
    let plotData = [barTrace, ...traces];
    let yMax = showPercent ? 100 : 5;
    let yLabel = showPercent ? 'Percentagem (%)' : 'Escala (0-5)';
    let layout = {
      title: 'Distribuição das Opiniões dos Utilizadores',
      yaxis: { title: yLabel, range: [0, yMax] },
      boxmode: 'group',
      barmode: 'overlay',
      margin: { t: 60, l: 60, r: 30, b: 60 },
      font: { size: 18 },
      xaxis: { tickfont: { size: 13 } }
    };
    if(typeof Plotly==='undefined'){
      let s=document.createElement('script');
      s.src='https://cdn.plot.ly/plotly-latest.min.js';
      s.onload=()=>Plotly.newPlot('swarmplotDiv', plotData, layout, {responsive:true});
      document.body.appendChild(s);
    }else{
      Plotly.newPlot('swarmplotDiv', plotData, layout, {responsive:true});
    }
    document.getElementById('toggleSwarmBtn').innerText = 'Mostrar Barras';
    document.getElementById('toggleScaleBtn').innerText = showPercent ? 'Mostrar em escala 0-5' : 'Mostrar em percentagem';
  }
}

function updateBarLabels(chart) {
  const labelsDiv = document.getElementById('metricsBarLabels');
  labelsDiv.innerHTML = '';
  const metas = chart.getSortedVisibleDatasetMetas();
  const datasets = chart.data.datasets;
  const barLabels = chart.data.labels;
  for (let i = 0; i < barLabels.length; i++) {
    const meta = chart.getDatasetMeta(i);
    const div = document.createElement('div');
    div.textContent = barLabels[i];
    div.style.flex = '1 1 0';
    div.style.textAlign = 'center';
    div.style.fontWeight = 'bold';
    div.style.fontSize = '16px';
    div.style.color = meta.hidden ? '#bbb' : '#111';
    div.style.opacity = meta.hidden ? '0.5' : '1';
    labelsDiv.appendChild(div);
  }
}

function toggleScale() {
  showPercent = !showPercent;
  if(metricsData) fetchMetrics();
}

function toggleSwarmplot() {
  showSwarmplot = !showSwarmplot;
  if(metricsData) fetchMetrics();
}

async function updateStackedLineChart() {
  const dom = document.getElementById('stackedLineChart');
  const chart = echarts.init(dom);
  try {
    const r = await fetch('/api/task_metrics');
    const data = await r.json();
    const days = Object.keys(data).sort();
    const tarefas = ['gestao_despensa', 'receitas', 'lista_compras'];
    const nomes = ['Gestão de Despensa', 'Receitas', 'Lista de Compras'];
    // Cores: Despensa (azul), Receitas (verde), Compras (amarelo)
    const cores = ['#4BC0C0', '#4CAF50', '#FFCE56']; // Receitas agora verde
    const series = tarefas.map((t, i) => ({
      name: nomes[i],
      type: 'line',
      data: days.map(d => data[d][t] != null ? data[d][t] : null),
      lineStyle: { width: 3, color: cores[i] },
      itemStyle: { color: cores[i] }, // pontos da mesma cor da linha
      connectNulls: true
    }));
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: nomes, textStyle: { fontSize: 16 } },
      xAxis: { type: 'category', data: days, axisLabel: { fontSize: 16, rotate: 30 } },
      yAxis: { type: 'value', min: 0, max: 5, axisLabel: { fontSize: 16 } },
      series,
      toolbox: { feature: { saveAsImage: {} } }
    });
  } catch (e) {
    dom.innerHTML = '<div style="color:red">Erro ao carregar dados de desempenho diário.</div>';
    console.error(e);
  }
}

function onScroll() {
  const sections=document.querySelectorAll('main.content section'); const links=document.querySelectorAll('.sidebar-nav a'); let pos=window.scrollY+200;
  sections.forEach(sec=>{ if(sec.offsetTop<=pos && sec.offsetTop+sec.offsetHeight>pos){ links.forEach(l=>l.classList.remove('active')); document.querySelector(`.sidebar-nav a[href='#${sec.id}']`).classList.add('active'); }});
}

async function fetchUsers() {
  try {
    const r = await fetch('/api/users', {credentials:'include'});
    const users = await r.json();
    const sel = document.getElementById('userSelect');
    sel.innerHTML = '';
    users.forEach(u => {
      const opt = document.createElement('option');
      opt.value = u;
      opt.textContent = u;
      sel.appendChild(opt);
    });
    sel.onchange = function() {
      selectedUser = this.value;
      fetchMetrics();
    };
  } catch(e) { console.error(e); }
}

async function fetchMetrics(){
  try{
    let url = '/api/metrics';
    let rawUrl = '/api/metrics_raw';
    if(selectedUser && selectedUser !== 'Todos'){
      url += '?user=' + encodeURIComponent(selectedUser);
      rawUrl += '?user=' + encodeURIComponent(selectedUser);
    }
    const r=await fetch(url,{credentials:'include'}),d=await r.json();
    let raw = {};
    try {
      const r2 = await fetch(rawUrl,{credentials:'include'});
      raw = await r2.json();
    } catch(e) { raw = {}; }      updateMetricsChart(d, raw);
    const ov = Math.round((d.facil_de_usar + d.estou_satisfeito + d.usaria_novamente + d.comunica_bem + d.faz_oque_quero)/5);
    updateGaugeChart(ov);
  }catch(e){console.error(e);}
}

async function fetchJustificacoes(){ try{ const r=await fetch('/api/justificacoes'),arr=await r.json(),f1=document.getElementById('filtroDataInicio').value,f2=document.getElementById('filtroDataFim').value,cls=document.getElementById('filtroClassificacao').value,t1=f1?new Date(f1).getTime():0,t2=f2?new Date(f2).getTime()+86400000:Infinity,fil=arr.filter(i=>{const ts=new Date(i.timestamp).getTime();return ts>=t1&&ts<t2&&(!cls||i.resposta==cls);}),tb=document.getElementById('justificacoes-list'); tb.innerHTML=''; if(!fil.length){tb.innerHTML='<tr><td colspan="4">Nenhuma justificação encontrada.</td></tr>';return;} fil.forEach(i=>{const tr=document.createElement('tr');tr.innerHTML=`<td>${new Date(i.timestamp).toLocaleString('pt-PT')}</td><td>${i.pergunta}</td><td>${i.resposta}</td><td>${i.justificacao}</td>`;tb.appendChild(tr);});}catch(e){console.error(e);} }

document.addEventListener('DOMContentLoaded',()=>{ setActive(document.querySelector('.sidebar-nav a')); updateStackedLineChart(); fetchUsers(); fetchMetrics(); fetchJustificacoes(); window.addEventListener('scroll', onScroll); });
// Scroll suave ao clicar nos links da sidebar
 document.querySelectorAll('.sidebar-nav a').forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        const targetId = link.getAttribute('href').substring(1);
        const section = document.getElementById(targetId);
        if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setActive(link);
      });
    });
