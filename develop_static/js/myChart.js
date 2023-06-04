var randomScalingFactor = function() {
    return Math.round(Math.random() * 100);
};

var config = {
    type: "line",
    data: chart_data,
    options: {
        responsive: true,
        title: {
            display: false,
            text: "Chart with Multiline Labels"
        },
    }
};

window.onload = function() {
    var ctx = document.getElementById("myChart").getContext("2d");
    window.myLine = new Chart(ctx, config);
}
