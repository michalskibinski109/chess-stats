import ChartInterface from "./chartInterface.js";

class MistakesChart extends ChartInterface {
  constructor() {
    super("mistakes_per_phase");
  }

  prepareData(mistakes) {
    return {
      labels: ["opening", "middle game", "end game"],
      datasets: [
        {
          label: "Inaccuracies",
          data: [
            mistakes["opening"][0],
            mistakes["middle_game"][0],
            mistakes["end_game"][0],
          ],
        },

        {
          label: "Mistakes",
          data: [
            mistakes["opening"][1],
            mistakes["middle_game"][1],
            mistakes["end_game"][1],
          ],
        },
        {
          label: "Blunders",
          data: [
            mistakes["opening"][2],
            mistakes["middle_game"][2],
            mistakes["end_game"][2],
          ],
        },
      ],
    };
  }

  createChart(data) {
    return new Chart($(this.chartId), {
      type: "bar",
      data: this.prepareData(data),
      options: {
        maintainAspectRatio: false,
        aspectRatio: 0.7,
        responsive: true,
        scales: {
          x: {
            stacked: true,
            title: {
              display: true,
              text: "Game Phase",
            },
          },
          y: {
            stacked: true,
            title: {
              display: true,
              text: "Avg number of different mistakes per phase",
            },
          },
        },
      },
    });
  }

  updateChart(hostName) {
    const data = this.data[hostName];
    this.chart.data = this.prepareData(data);
    this.chart.update();
  }
}

$(document).ready(() => {
  new MistakesChart();
});
