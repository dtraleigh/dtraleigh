let freeColor = 'DarkSeaGreen';
let hourlyColor = 'orange';
let flatColor = 'blue';

let hourlyPattern = pattern.draw('dash', hourlyColor);
let flatPattern = pattern.draw('dot-dash', flatColor);
let defaultPattern = pattern.draw('diagonal', 'gray');

function patternToDataURL(pattern) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 20;
    canvas.height = 20;
    ctx.fillStyle = pattern;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return canvas.toDataURL();
}

function populateColorAndPattern(datasets) {
    datasets.forEach(function(dataset) {
        let backgroundColors = [];

        dataset.data.forEach(function(dataPoint) {
            let patternColor;
            switch(dataPoint.rate) {
                case 'Free':
                case 'Free Evenings':
                case 'Free all day':
                    patternColor = freeColor;
                    break;
                case 'Hourly Rates Apply':
                case 'Hourly Rates Apply all day':
                    patternColor = hourlyPattern;
                    break;
                case '$5 Flat Fee':
                case '$5 Flat Fee all day':
                case '$7 Flat Fee':
                case '$7 Flat Fee all day':
                    patternColor = flatPattern;
                    break;
                default:
                    patternColor = defaultPattern;
            }
            backgroundColors.push(patternColor);
        });

        dataset.backgroundColor = backgroundColors;
    });

    return datasets;
}