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
        y2: {
            position: 'right',
            grid: {
                drawOnChartArea: false, // Only want the grid lines for one axis to show up
            },
            labels: ['Click any bar to Go'],
        }
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
    legendCallback: function(chart) {
        const text = [];
        text.push('<ul class="custom-legend">');
        chart.data.datasets.forEach((dataset, i) => {
            text.push('<li>');
            text.push('<span style="background-color:' + dataset.backgroundColor + '"></span>');
            text.push(dataset.label);
            text.push('</li>');
        });
        text.push('</ul>');
        return text.join('');
    }
};

const data = {
    labels: parkingLocations,
    datasets: datasets,
};

const customLegendPlugin = {
    id: 'customLegendPlugin',
    afterUpdate: function(chart) {
        const legendContainer = document.getElementById('custom-legend');
        const text = [];
        text.push('<ul class="custom-legend">');
        text.push('<li><span style="background-color:' + freeColor + '"></span>Free</li>');
        text.push('<li><span style="background-image:url(' + patternToDataURL(hourlyPattern) + ')"></span>Hourly Rate</li>');
        text.push('<li><span style="background-image:url(' + patternToDataURL(flatPattern) + ')"></span>Flat Rate</li>');
        text.push('</ul>');
        legendContainer.innerHTML = text.join('');
    }
};


const myChart = new Chart("myChart", {
    type: "bar",
    data: data,
    options: options,
    plugins: [customLegendPlugin]
});

document.getElementById("myChart").onclick = function (e) {
    const activePoints = myChart.getElementsAtEventForMode(e, 'nearest', { intersect: true }, false);
    if (activePoints.length > 0) {
        const firstPoint = activePoints[0];
        const labelIndex = firstPoint.index;
        console.log('Clicked bar:', parkingLocations[labelIndex],
        'labelIndex', labelIndex,
        'url: ', parkingLocationDirUrls[labelIndex]);
        window.open(parkingLocationDirUrls[labelIndex], '_blank');
    } else {
        console.log('No bar was clicked');
    }
};

