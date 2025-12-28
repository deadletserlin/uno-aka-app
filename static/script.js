function getParams() {
    return {
      players: parseInt(document.getElementById("players").value, 10),
      hand: parseInt(document.getElementById("hand").value, 10),
      turns: parseInt(document.getElementById("turns").value, 10),
      repeat: parseInt(document.getElementById("repeat").value, 10)
    };
  }  
  
  function fmtRun(turns, timeMs) {
    return `
      <div><b>Turns:</b> ${turns}</div>
      <div><b>Time:</b> ${timeMs} ms</div>
    `;
  }
  
  function runAlgo(type) {
    fetch("/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({...getParams(), type})
    })
      .then(res => res.json())
      .then(data => {
        if (type === "iterative") {
          document.getElementById("out-iter").innerHTML = fmtRun(data.turns, data.time);
        } else {
          document.getElementById("out-rec").innerHTML = fmtRun(data.turns, data.time);
        }
      });
  }
  
  function compare() {
    fetch("/compare", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(getParams())
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("out-compare").innerHTML = `
          <div><b>Repeat:</b> ${data.repeat}x</div>
          <div><b>Iteratif avg:</b> ${data.iter_avg_ms} ms (total ${data.iter_total_ms} ms)</div>
          <div><b>Rekursif avg:</b> ${data.rec_avg_ms} ms (total ${data.rec_total_ms} ms)</div>
        `;
      });
  }  