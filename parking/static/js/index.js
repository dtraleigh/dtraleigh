const ctx = document.getElementById('myChart').getContext('2d');

const options = {
    parsing: {
        yAxisKey: 'x'
    },
    indexAxis: 'y',
    scales: {
        x: {
            stacked: true,
            min: 5,
            max: 22,
            type: 'category',
            labels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
            ticks: {
                callback: function(value) {
                    const hour = value % 12 || 12; // convert to 12-hour format
                    const period = value < 12 || value === 24 ? 'AM' : 'PM';
                    return hour + ' ' + period;
                },
                stepSize: 1,
                autoSkip: false
            },
        },
        y: {
            stacked: true,
        },
    },
    responsive: false,
    plugins: {
        legend: {
            display: false
        },
        annotation: {
            annotations: {
                line1: {
                    type: 'line',
                    xMin: parseInt(getEasternStandardTimeHour(), 10),
                    xMax: parseInt(getEasternStandardTimeHour(), 10),
                    label: {
                        display: true,
                        content: 'Time Now',
                        position: 'end'
                    }
                }
            }
        },
        tooltip: {
            callbacks: {
                label: function(tooltipItem) {
                    const datasetIndex = tooltipItem.datasetIndex;
                    const dataIndex = tooltipItem.dataIndex;
                    return data.datasets[datasetIndex].data[dataIndex].rate;
                },
            },
        }
    },
};

const data = {
    labels: parkingLocations,
    datasets: datasets,
};

const myChart = new Chart("myChart", {
    type: "bar",
    data: data,
    options: options
});